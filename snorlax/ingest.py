# Copyright (c) 2025-2026 iiPython

import asyncio
import traceback
import typing

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from snorlax.config import config
from snorlax.database import VIDEO_PARAMS, db

TEMP_PATH = config.snorlax.video_path / "in_progress"

class Job:
    def __init__(self, video_data: dict[str, typing.Any]) -> None:
        self.info = video_data
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
            "noprogress": True,
            "js_runtimes": {"bun": {}}
        })  # pyright: ignore[reportArgumentType]

        self._progress: dict[str, typing.Any] = {
            "progress": 0,
            "status": "queued",
            "title": video_data["title"],
            "channel": video_data["uploader"],
            "channel_preferred_id": video_data.get("uploader_id") or video_data["channel_id"],
            "timestamp": video_data["timestamp"]
        }
        self._canceled: bool = False

    def _progress_hook(self, data: dict) -> None:
        if self._canceled:
            raise DownloadError("The requested download has been canceled")

        if (data["status"] not in {"finished", "downloading"}) or ("title" not in data["info_dict"]):
            return

        self._progress |= {
            "progress": round((data["downloaded_bytes"] / (data["total_bytes"] or 0.1)) * 100),
            "status": data["status"] if data["status"] != "finished" else "remuxing",
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

    async def _download_video(self) -> None:
        try:
            await asyncio.to_thread(self.ytdl.extract_info, f"https://youtu.be/{self.info['id']}")

        except Exception as e:
            if self._canceled:
                for file in TEMP_PATH.glob(f"{self.info['id']}*"):
                    file.unlink()

            self._progress |= {"progress": 0, "status": "failed"}
            if not isinstance(e, DownloadError):
                traceback.print_exc()

    async def start(self) -> None:
        if not TEMP_PATH.is_dir():
            TEMP_PATH.mkdir(parents = True)

        # Handle video data
        existing_video = await db.get_video(self.info["id"])
        if existing_video is not None:
            self._progress["status"] = "finished"
            return  # The video already exists

        await self._download_video()
        self._progress["status"] = "finished"

        # Save everything to database
        channel = await db.get_channel(self.info["channel_id"])
        if channel is None:
            await db.add_channel(self.info["channel_id"], self.info.get("uploader_id"), self.info["uploader"], self.info["channel_follower_count"])

        self.info |= {"caption_langs": list((self.info["requested_subtitles"] or {}).keys()), "chapters": self.info["chapters"] or []}
        await db.add_video(**{k: v for k, v in self.info.items() if k in VIDEO_PARAMS})

        # Reorganize everything
        video_path = config.snorlax.video_path / self.info["channel_id"] / self.info["id"]
        if not video_path.is_dir():
            video_path.mkdir(parents = True)

        for file in TEMP_PATH.glob(f"{self.info['id']}*"):
            file.rename(video_path / file.name.replace(self.info["id"], {".webp": "cover", ".vtt": "sub", ".mkv": "video"}[file.suffix]))

# Handle snoring and laxing
class Snorlax:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}
        self.queue: asyncio.Queue[Job] = asyncio.Queue()

        # Metadata-only YouTube instance
        self.ytdl = YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": "yes", "js_runtimes": {"bun": {}}})

    async def process_queue(self) -> None:
        while True:
            job = await self.queue.get()
            if job.canceled:
                self.queue.task_done()
                continue

            await job.start()
            self.queue.task_done()

    async def fetch_url(self, url: str) -> None:

        # YouTube: Remove playlist data from video watch URL
        # This prevents us from getting stuck in a loop of processing the same URL endlessly
        if "/playlist" not in url:
            for item in {"?list=", "&list="}:
                url = url.split(item)[0]

        # Handle extraction
        try:
            info: dict[str, typing.Any] = await asyncio.to_thread(self.ytdl.extract_info, url, download = False)  # pyright: ignore[reportAssignmentType]
            if (media_type := info.get("_type", info.get("media_type"))) not in {"playlist", "video"}:
                raise ValueError(f"Received an unsupported media type: {media_type}")

            match media_type:
                case "playlist":
                    for item in info["entries"]:
                        item_url = item.get("url") or item.get("webpage_url")
                        if item_url is None:
                            continue

                        await self.fetch_url(item_url)

                case "video":
                    self.jobs[info["id"]] = Job(info)
                    await self.queue.put(self.jobs[info["id"]])

        except Exception:
            traceback.print_exc()

    async def cancel_job(self, video_id: str) -> None:
        if video_id in self.jobs:
            self.jobs[video_id].cancel()
            del self.jobs[video_id]
