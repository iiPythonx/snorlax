# Copyright (c) 2025-2026 iiPython

import asyncio
import traceback
import typing
from uuid import uuid4

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from snorlax.config import config
from snorlax.database import VIDEO_COLUMNS, db

TEMP_PATH = config.snorlax.video_path / "in_progress"
YTDL_OPTS = {
    "writesubtitles": True,
    "writethumbnail": True,
    "subtitlesformat": "vtt",
    "subtitleslangs": config.videos.subtitle_languages,
    "remote_components": {"ejs:github"},
    "outtmpl": str(TEMP_PATH / "%(id)s.%(ext)s"),
    "format": "bestvideo+bestaudio",
    "format_sort": ["codec:av1", "codec:vp9", "res", "fps", "br"],
    "merge_output_format": "mkv",
    "remux_video": "mkv",
    "quiet": True,
    "noprogress": True,
    "js_runtimes": {"bun": {}}
}

class Job:
    def __init__(self, job_id: str, video_id: str, url: str) -> None:
        self.id, self.video_id, self.url = job_id, video_id, url

        self.progress: int = 0
        self.status: str = "queued"
        self.speed: float = 0.0
        self.eta: int = 0

        self._ytdl = YoutubeDL(YTDL_OPTS | {"progress_hooks": [self._progress_hook]})  # pyright: ignore[reportArgumentType]
        self._canceled: bool = False

    def __repr__(self) -> str:
        return f"<Job id = '{self.id}' url = '{self.url}'>"

    def _progress_hook(self, data: dict) -> None:
        if self._canceled:
            raise DownloadError("The requested download has been canceled")

        if (data["status"] not in {"finished", "downloading"}) or ("title" not in data["info_dict"]):
            return

        if "downloaded_bytes" not in data:
            data["downloaded_bytes"] = 0

        self.progress = round((data["downloaded_bytes"] / (data["total_bytes"] or 0.1)) * 100)
        self.status = data["status"] if data["status"] != "finished" else "remuxing"
        self.speed = round((data["speed"] or 0) / (1024 ** 2), 2)
        self.eta = round((data["total_bytes"] - data["downloaded_bytes"]) / (data["speed"] or 0.1))

    def cancel(self) -> None:
        self._canceled = True

    async def _download_video(self) -> None:
        try:
            await asyncio.to_thread(self._ytdl.extract_info, self.url)

        except Exception as e:
            if self._canceled:
                for file in TEMP_PATH.glob(f"{self.video_id}*"):
                    file.unlink()

            await db.update_job(self.id, status = "failed", error = str(e))
            if not isinstance(e, DownloadError):
                traceback.print_exc()

    async def run(self) -> None:
        if not TEMP_PATH.is_dir():
            TEMP_PATH.mkdir(parents = True)

        # Handle video data
        await self._download_video()
        self.status = "finished"

        # Reorganize everything
        video_data = await db.get_video(self.video_id)
        if video_data is None:
            return  # ?????

        video_path = config.snorlax.video_path / video_data["channel_id"] / self.video_id
        if not video_path.is_dir():
            video_path.mkdir(parents = True)

        for file in TEMP_PATH.glob(f"{self.video_id}*"):
            file.rename(video_path / file.name.replace(self.video_id, {".webp": "cover", ".vtt": "sub", ".mkv": "video"}[file.suffix]))

class JobStore:
    def __init__(self):
        self.ytdl = YoutubeDL(YTDL_OPTS | {"extract_flat": True, "skip_download": "yes"})  # pyright: ignore[reportArgumentType]
        self.queue: asyncio.Queue[tuple[str, str, str]] = asyncio.Queue()
        self.jobs: dict[str, Job] = {}

    async def create(self, url: str) -> tuple[bool, str | None]:

        # YouTube: Remove playlist data from video watch URL
        # This prevents us from getting stuck in a loop of processing the same URL endlessly
        if "/playlist" not in url:
            for item in {"?list=", "&list="}:
                url = url.split(item)[0]

        # Handle extraction
        try:
            info: dict[str, typing.Any] = await asyncio.to_thread(self.ytdl.extract_info, url, download = False)  # pyright: ignore[reportAssignmentType]
            match media_type := info.get("_type", info.get("media_type")):
                case "playlist":
                    for item in info["entries"]:
                        item_url = item.get("url") or item.get("webpage_url")
                        if item_url is None:
                            continue

                        await self.create(item_url)

                case "video":
                    await db.add_channel(info["channel_id"], info.get("uploader_id"), info["uploader"], info["channel_follower_count"])
                    await db.add_video(**{k: v for k, v in info.items() if k in VIDEO_COLUMNS.get("insert")} | \
                        {"caption_langs": list((info["requested_subtitles"] or {}).keys()), "chapters": info["chapters"] or [], "available": False})

                    job_id = str(uuid4())

                    # Send job to database and immediate queue
                    await db.add_job(job_id, info["id"], url)
                    await self.queue.put((job_id, info["id"], url))

                case _:
                    raise ValueError(f"Received an unsupported media type: {media_type}")

        except Exception as e:
            message = str(e)
            if isinstance(e, DownloadError):
                message = message.split("[0m ")[1]

            traceback.print_exc()
            return False, message

        return True, None

    async def queued(self) -> tuple[str, str, str]:
        return await self.queue.get()

    async def cancel(self, job_id: str) -> None:
        if job_id in self.jobs:
            self.jobs[job_id].cancel()
            del self.jobs[job_id]

    async def launch(self, job: Job) -> None:
        self.jobs[job.id] = job
        await job.run()
        await db.update_job(job.id, status = "finished", progress = 100, speed = None, eta = None)

    async def flush_jobs_to_db(self) -> None:
        for job_id, job in self.jobs.items():
            if job.status == "finished":
                continue

            await db.update_job(
                job_id,
                progress = job.progress,
                status = job.status,
                speed = job.speed,
                eta = job.eta
            )

    async def fetch_queue_from_db(self) -> None:
        for job in await db.get_queued_jobs():
            await self.queue.put(job)

# Handle snoring and laxing
store = JobStore()

async def periodic_flush() -> None:
    while not await asyncio.sleep(2):
        await store.flush_jobs_to_db()

async def process_queue() -> None:
    await store.fetch_queue_from_db()
    asyncio.create_task(periodic_flush())
    while True:
        await store.launch(Job(*await store.queued()))
