# Copyright (c) 2025-2026 iiPython

import typing
import asyncio
import traceback

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
            "format": "bestvideo+bestaudio",
            "format_sort": ["codec:av1", "codec:vp9", "res", "fps", "br"],
            "progress_hooks": [self._progress_hook],
            "merge_output_format": "mkv",
            "remux_video": "mkv",
            "quiet": True,
            "noprogress": True
        })  # type: ignore

        self._progress: dict[str, typing.Any] = {}
        self._canceled: bool = False

    def _progress_hook(self, data: dict) -> None:
        if self._canceled:
            raise DownloadError("The requested download has been canceled")

        if (data["status"] not in {"finished", "downloading"}) or ("title" not in data["info_dict"]):
            return

        self._progress = {
            "progress": round((data["downloaded_bytes"] / (data["total_bytes"] or 0.1)) * 100),
            "status": data["status"],
            "title": data["info_dict"]["title"],
            "channel": data["info_dict"]["uploader"],
            "channel_preferred_id": data["info_dict"].get("uploader_id") or data["info_dict"]["channel_id"],
            "timestamp": data["info_dict"]["timestamp"],
            "speed": round((data["speed"] or 0) / (1024 ** 2), 2),
            "eta": round((data["total_bytes"] - data["downloaded_bytes"]) / (data["speed"] or 0.1))
        }

    def get_progress(self) -> dict[str, typing.Any]:
        return self._progress

    def cancel(self) -> None:
        self._canceled = True

    @property
    def canceled(self) -> bool:
        return self._canceled

    async def _extract_info(self, download: bool = True) -> dict[str, typing.Any] | None:
        try:
            info: dict[str, typing.Any] = await asyncio.to_thread(self.ytdl.extract_info, f"https://youtu.be/{self.video_id}", download)  # type: ignore
            return info

        except Exception as e:
            if self._canceled:
                for file in TEMP_PATH.glob(f"{self.video_id}*"):
                    file.unlink()

            self._progress = {"progress": 0, "status": "failed", "title": self.video_id}
            if not isinstance(e, DownloadError):
                traceback.print_exc()

    async def start(self) -> None:
        if not TEMP_PATH.is_dir():
            TEMP_PATH.mkdir(parents = True)

        # Handle video data
        existing_video = await db.get_video(self.video_id)
        if existing_video is not None:
            return  # The video already exists

        info = await self._extract_info()
        if info is None:
            return

        # Save everything to database
        channel = await db.get_channel(info["channel_id"])
        if channel is None:
            await db.add_channel(info["channel_id"], info.get("uploader_id"), info["uploader"], info["channel_follower_count"])

        info |= {"caption_langs": ",".join((info["requested_subtitles"] or {}).keys())}
        await db.add_video(**{k: v for k, v in info.items() if k in VIDEO_PARAMS})  # type: ignore

        # Reorganize everything
        video_path = config.snorlax.video_path / info["channel_id"] / self.video_id
        if not video_path.is_dir():
            video_path.mkdir(parents = True)

        for file in TEMP_PATH.glob(f"{self.video_id}*"):
            file.rename(video_path / file.name.replace(self.video_id, {".webp": "cover", ".vtt": "sub", ".mkv": "video"}[file.suffix]))

    async def fetch_info(self) -> None:
        info = await self._extract_info(False)
        if info is None:
            return

        self._progress |= {
            "progress": 0,
            "status": "queued",
            "title": info["title"],
            "channel": info["uploader"],
            "channel_id": info["uploader_id"],
            "timestamp": info["timestamp"]
        }

# Handle snoring and laxing
class Snorlax:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.queue: asyncio.Queue[Job] = asyncio.Queue()

        # Metadata-only YouTube instance
        self.ytdl = YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": "yes"})

    async def process_queue(self) -> None:
        while True:
            job = await self.queue.get()
            if job.canceled:
                self.queue.task_done()
                continue

            await job.start()
            self.queue.task_done()

    async def fetch_channel(self, channel_id: str) -> None:
        try:
            info: dict[str, typing.Any] = await asyncio.to_thread(self.ytdl.extract_info, f"https://youtube.com/{channel_id}/videos", download = False)  # type: ignore
            if "entries" not in info:
                raise RuntimeError("failed to extract video entries from channel")

            for video in info["entries"]:
                await self.fetch_video(video["url"].split("=")[-1])

        except DownloadError:
            pass

    async def fetch_video(self, video_id: str) -> None:
        self.jobs[video_id] = Job(video_id)
        await self.jobs[video_id].fetch_info()
        await self.queue.put(self.jobs[video_id])

    async def cancel_job(self, video_id: str) -> None:
        if video_id not in self.jobs:
            return

        self.jobs[video_id].cancel()
        del self.jobs[video_id]
