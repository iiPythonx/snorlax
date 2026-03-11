# Copyright (c) 2025-2026 iiPython

import typing

from yt_dlp import YoutubeDL

from snorlax.config import config
from snorlax.database import db, VIDEO_PARAMS

# Path information
TEMP_PATH = config.VIDEO_PATH / "in_progress"

class Job:
    def __init__(self, video_id: str) -> None:
        self.video_id = video_id
        self.ytdl = YoutubeDL({
            "writesubtitles": True,
            "allsubtitles": True,
            "writethumbnail": True,
            "remote_components": {"ejs:github"},
            "outtmpl": str(TEMP_PATH / "%(id)s.%(ext)s"),
            "format": "bestvideo+bestaudio",
            "progress_hooks": [self._progress_hook]
        })  # type: ignore

    def _progress_hook(self, data: dict) -> None:
        print(data)

    async def start(self) -> None:

        # Make sure temp exists
        if not TEMP_PATH.is_dir():
            TEMP_PATH.mkdir(parents = True)

        # Handle video data
        existing_video = await db.get_video(self.video_id)
        if existing_video is not None:
            return  # The video already exists

        info: dict[str, typing.Any] = self.ytdl.extract_info(f"https://youtu.be/{self.video_id}", download = True)  # type: ignore

        # Save everything to database
        channel_id = info["uploader_id"]
        if await db.get_channel(channel_id) is None:
            await db.add_channel(channel_id, info["uploader"], info["channel_follower_count"])

        info["caption_langs"] = ",".join(info["subtitles"].keys())
        await db.add_video(*map(info.get, VIDEO_PARAMS))  # type: ignore

        # Reorganize everything
        video_path = config.VIDEO_PATH / channel_id / self.video_id
        if not video_path.is_dir():
            video_path.mkdir(parents = True)

        for file in TEMP_PATH.iterdir():
            if self.video_id not in file.name:
                continue

            file.rename(video_path / file.name.replace(self.video_id, {".webp": "cover", ".vtt": "sub", ".webm": "video"}[file.suffix]))

# Handle snoring and laxing
class Snorlax:
    def __init__(self) -> None:
        self.jobs: list[Job] = []

    async def fetch_channel(self, channel_id: str) -> None:
        with YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": "yes"}) as ytdl:
            info: dict[str, typing.Any] = ytdl.extract_info(f"https://youtube.com/{channel_id}/videos", download = False)  # type: ignore
            if "entries" not in info:
                raise RuntimeError("failed to extract video entries from channel")

            for video in info["entries"]:
                await self.fetch_video(video["url"].split("=")[-1])

    async def fetch_video(self, video_id: str) -> None:
        job = Job(video_id)
        self.jobs.append(job)
        await job.start()
