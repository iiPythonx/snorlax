# Copyright (c) 2026 iiPython

# Modules
import json
import asyncio
import os
from sys import argv
from pathlib import Path
from subprocess import run

from snorlax.config import config
from snorlax.database import VIDEO_PARAMS, db

# Initialization
files = [Path(file) for file in argv[1:]]

# Load JSON
async def main() -> None:
    await db.init()
    info = json.loads(next(filter(lambda f: f.suffix == ".json", files)).read_text())
    
    channel = await db.get_channel(info["channel_id"])
    if channel is None:
        await db.add_channel(info["channel_id"], info.get("uploader_id"), info["uploader"], info["channel_follower_count"])

    info |= {"caption_langs": ""}
    await db.add_video(**{k: v for k, v in info.items() if k in VIDEO_PARAMS})  # type: ignore

    # Reorganize everything
    video_path = config.snorlax.video_path / info["channel_id"] / info["id"]
    if not video_path.is_dir():
        video_path.mkdir(parents = True)
    
    run(["ffmpeg", "-i", next(filter(lambda f: f.suffix in [".mp4", ".webm", ".mkv"], files)), "-map", "0", "-c", "copy", video_path / "video.mkv"])
    next(filter(lambda f: f.suffix == ".webp", files)).move(video_path / "cover.webp")

    await db.close()
    os._exit(0)

asyncio.run(main())
