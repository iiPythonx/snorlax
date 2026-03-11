# Copyright (c) 2025-2026 iiPython

import typing
import asyncio

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from snorlax.config import config
from snorlax.database import db, VIDEO_PARAMS

TEMP_PATH = config.snorlax.video_path / "in_progress"

class Job:
    def __init__(self, video_id: str) -> None:
        self.video_id = video_id
        self.ytdl = YoutubeDL({
            "writesubtitles": True,
            "writethumbnail": True,
            "subtitlesformat": "vtt",
            "subtitleslangs": config.videos.subtitle_languages,
            "remote_components": {"ejs:github"},
            "outtmpl": str(TEMP_PATH / "%(id)s.%(ext)s"),
            "format": "bv*+ba/b",
            "progress_hooks": [self._progress_hook],
            "merge_output_format": "mkv",
            "remux_video": "mkv",
            "quiet": True
        })  # type: ignore

        self._progress: dict[str, typing.Any] = {}

    def _progress_hook(self, data: dict) -> None:
        if "title" not in data["info_dict"]:
            return

        self._progress = {
            "progress": round((data["downloaded_bytes"] / (data["total_bytes"] or 0.1)) * 100),
            "status": data["status"],
            "title": data["info_dict"]["title"],
            "channel": data["info_dict"]["uploader"],
            "channel_id": data["info_dict"]["uploader_id"],
            "timestamp": data["info_dict"]["timestamp"],
            "speed": round((data["speed"] or 0) / (1024 ** 2), 2),
            "eta": round((data["total_bytes"] - data["downloaded_bytes"]) / (data["speed"] or 0.1))
        }

    def get_progress(self) -> dict[str, typing.Any]:
        return self._progress

    async def start(self) -> None:

        # Make sure temp exists
        if not TEMP_PATH.is_dir():
            TEMP_PATH.mkdir(parents = True)

        # Handle video data
        existing_video = await db.get_video(self.video_id)
        if existing_video is not None:
            return  # The video already exists

        try:
            info: dict[str, typing.Any] = await asyncio.to_thread(self.ytdl.extract_info, f"https://youtu.be/{self.video_id}", download = True)  # type: ignore

        except DownloadError:
            self._progress = {"progress": 0, "status": "failed", "title": self.video_id}
            return

        # Save everything to database
        if await db.get_channel(info["uploader_id"]) is None:
            await db.add_channel(info["uploader_id"], info["uploader"], info["channel_follower_count"])

        info |= {"caption_langs": ",".join(info["requested_subtitles"].keys()), "channel_id": info["uploader_id"]}
        await db.add_video(**{k: v for k, v in info.items() if k in VIDEO_PARAMS})  # type: ignore

        # Reorganize everything
        video_path = config.snorlax.video_path / info["uploader_id"] / self.video_id
        if not video_path.is_dir():
            video_path.mkdir(parents = True)

        for file in TEMP_PATH.iterdir():
            if self.video_id not in file.name:
                continue

            file.rename(video_path / file.name.replace(self.video_id, {".webp": "cover", ".vtt": "sub", ".mkv": "video"}[file.suffix]))

# Handle snoring and laxing
class Snorlax:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}

    async def fetch_channel(self, channel_id: str) -> None:
        with YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": "yes"}) as ytdl:
            info: dict[str, typing.Any] = await asyncio.to_thread(ytdl.extract_info, f"https://youtube.com/{channel_id}/videos", download = False)  # type: ignore
            if "entries" not in info:
                raise RuntimeError("failed to extract video entries from channel")

            for video in info["entries"]:
                await self.fetch_video(video["url"].split("=")[-1])

    async def fetch_video(self, video_id: str) -> None:
        self.jobs[video_id] = Job(video_id)
        await self.jobs[video_id].start()

    def remove_job(self, video_id: str) -> None:
        if video_id in self.jobs:
            del self.jobs[video_id]
