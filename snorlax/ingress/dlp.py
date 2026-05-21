# Copyright (c) 2025-2026 iiPython

import asyncio
import typing
from time import monotonic
from dataclasses import dataclass
from collections.abc import AsyncIterable, Callable, Coroutine

from yt_dlp import YoutubeDL

from snorlax.config import config
from snorlax.ingress import Job, ProgressEvent, TEMP_PATH

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

type Item = dict[str, typing.Any]
type ProgressReturn = Callable[[ProgressEvent], Coroutine[typing.Any, typing.Any, None]]

@dataclass
class DownloadState:
    audio_processed: bool = False
    video_processed: bool = False
    last_updated: float   = 0.0
    postprocessing: bool  = False

class DLP:
    def __init__(self) -> None:
        self.resolving_ytdl = YoutubeDL(YTDL_OPTS | {"extract_flat": True, "skip_download": "yes"})  # pyright: ignore[reportArgumentType]

    async def download(self, job: Job, progress_hook: ProgressReturn) -> None:
        loop, state = asyncio.get_running_loop(), DownloadState(last_updated = monotonic())

        def emit_status(**kwargs) -> None:
            asyncio.run_coroutine_threadsafe(
                progress_hook(ProgressEvent(**kwargs)),
                loop
            )

        def hook(data: dict[str, typing.Any]) -> None:
            nonlocal state

            force_update = False
            data.setdefault("downloaded_bytes", 0)
            
            # Handle determining postprocessing
            data.setdefault("info_dict", {})
            if data["info_dict"].get("audio_ext") != "none":
                state.audio_processed = True

            if data["info_dict"].get("video_ext") != "none":
                state.video_processed = True
            
            both_processed = state.audio_processed and state.video_processed
            if both_processed and data["status"] == "finished" and not state.postprocessing:
                
                # Both the video track AND audio track have passed through yt-dlp at this point
                # Therefore, if we're "finished" and haven't exited yet, we're 100% postprocessing
                data["status"], force_update, state.postprocessing = "postprocessing", True, True

            # Handle clock
            now = monotonic()
            if (now - state.last_updated >= 2) or force_update:
                state.last_updated = now
                emit_status(
                    status = data["status"],
                    progress = round((data["downloaded_bytes"] / (data["total_bytes"] or 0.1)) * 100),
                    speed = round((data["speed"] or 0) / (1024 ** 2), 2),
                    eta = round((data["total_bytes"] - data["downloaded_bytes"]) / (data["speed"] or 0.1))
                )

        ytdl = YoutubeDL(YTDL_OPTS | {"progress_hooks": [hook]})  # pyright: ignore[reportArgumentType]
        await asyncio.to_thread(ytdl.extract_info, job.url)

    async def resolve(self, url: str) -> AsyncIterable[Item]:
        if "/playlist" not in url:
            for item in {"?list=", "&list="}:
                url = url.split(item)[0]

        info: Item = await asyncio.to_thread(self.resolving_ytdl.extract_info, url, download = False)  # pyright: ignore[reportAssignmentType]
        match media_type := info.get("_type", info.get("media_type")):
            case "playlist":
                for item in info["entries"]:
                    item_url = item.get("url") or item.get("webpage_url")
                    if item_url is None:
                        continue  # TODO: debug logging

                    async for item in self.resolve(item_url):
                        yield item

            case "video":
                yield info

            case _:
                raise ValueError(f"resolve() received an unsupported media type: {media_type}")

dlp = DLP()
