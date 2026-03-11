# Copyright (c) 2025-2026 iiPython

import typing
from pathlib import Path

from yt_dlp import YoutubeDL

from snorlax.database import db, VIDEO_PARAMS

# Handle snoring and laxing
class Snorlax:
    def __init__(self) -> None:
        self.video_path = Path("videos")

        # Create temp and initial videos path
        self.temp_path = self.video_path / "in_progress"
        self.temp_path.mkdir(parents = True, exist_ok = True)

        # Base yt-dlp parameters
        self.ytdl = YoutubeDL({
            "writesubtitles": True,
            "allsubtitles": True,
            "writethumbnail": True,
            "remote_components": {"ejs:github"},
            "outtmpl": str(self.temp_path / "%(id)s.%(ext)s"),
            "format": "bestvideo+bestaudio"
        })  # type: ignore

    async def fetch_channel(self, channel_id: str) -> None:
        with YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": "yes"}) as ytdl:
            info: dict[str, typing.Any] = ytdl.extract_info(f"https://youtube.com/{channel_id}/videos", download = False)  # type: ignore
            if "entries" not in info:
                raise RuntimeError("failed to extract video entries from channel")

            for video in info["entries"]:
                await self.fetch_video(video["url"].split("=")[-1])

    async def fetch_video(self, video_id: str) -> None:
        existing_video = await db.get_video(video_id)
        if existing_video is not None:
            return  # The video already exists

        info: dict[str, typing.Any] = self.ytdl.extract_info(f"https://youtu.be/{video_id}", download = True)  # type: ignore

        # Save everything to database
        channel_id = info["uploader_id"]
        if await db.get_channel(channel_id) is None:
            await db.add_channel(channel_id, info["uploader"], info["channel_follower_count"])

        info["caption_langs"] = ",".join(info["subtitles"].keys())
        await db.add_video(*map(info.get, VIDEO_PARAMS))  # type: ignore

        # Reorganize everything
        video_path = self.video_path / channel_id / video_id
        if not video_path.is_dir():
            video_path.mkdir(parents = True)

        for file in self.temp_path.iterdir():
            if video_id not in file.name:
                continue

            file.rename(video_path / file.name.replace(video_id, {".webp": "cover", ".vtt": "sub", ".webm": "video"}[file.suffix]))
