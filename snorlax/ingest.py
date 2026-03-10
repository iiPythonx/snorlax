# Copyright (c) 2025-2026 iiPython

import typing
from pathlib import Path

from yt_dlp import YoutubeDL

from snorlax.database import db, VIDEO_PARAMETERS

# Handle snoring and laxing
class Snorlax:
    def __init__(self) -> None:
        self.video_path = Path("videos")
        self.temp_path = self.video_path / "in_progress"

        # Base yt-dlp parameters
        self.ytdl = YoutubeDL({
            "writesubtitles": True,
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
        if not await db.channel_exists(channel_id):
            await db.add_channel(channel_id, info["uploader"], info["channel_follower_count"])

        await db.add_video(*map(info.get, VIDEO_PARAMETERS))  # type: ignore

        # Reorganize everything
        channel_path = self.video_path / channel_id
        if not channel_path.is_dir():
            channel_path.mkdir(parents = True)

        for file in self.temp_path.iterdir():
            file.rename(channel_path / file.name)
