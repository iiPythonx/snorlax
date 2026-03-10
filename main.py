# Copyright (c) 2025 iiPython

# Modules
import typing
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

import aiosqlite
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from yt_dlp import YoutubeDL
from humanize import naturaltime

# Database
VIDEO_PARAMETERS = ["id", "title", "description", "view_count", "like_count", "duration_string", "timestamp", "uploader_id"]

class Database:
    def __init__(self) -> None:
        self.db: aiosqlite.Connection

    async def init(self) -> None:
        self.db = await aiosqlite.connect("snorlax.db")
        await self.db.execute("""CREATE TABLE IF NOT EXISTS channels (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            subscribers INTEGER
        )""")
        await self.db.execute("""CREATE TABLE IF NOT EXISTS videos (
            id              TEXT PRIMARY KEY,
            title           TEXT,
            description     TEXT,
            view_count      INTEGER,
            like_count      INTEGER,
            duration_string TEXT,
            timestamp       INTEGER,
            uploader_id     TEXT
        )""")
        await self.db.commit()

    async def add_channel(self, id: str, name: str, subscribers: int) -> None:
        await self.db.execute("INSERT INTO channels VALUES (?, ?, ?)", (id, name, subscribers))
        await self.db.commit()

    async def add_video(self, id: str, title: str, description: str, views: int, likes: int, duration: str, timestamp: int, uploader_id: str) -> None:
        await self.db.execute("INSERT INTO videos VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
            id, title, description, views, likes, duration, timestamp, uploader_id
        ))
        await self.db.commit()

    async def channel_exists(self, channel_id: str) -> bool:
        async with self.db.execute("SELECT id FROM channels WHERE id = ?", (channel_id,)) as result:
            return await result.fetchone() is not None

    async def get_channels(self) -> list[dict]:
        async with self.db.execute_fetchall("SELECT * FROM channels") as results:
            return [
                {"id": id, "name": name, "subscribers": subscribers}
                for id, name, subscribers in results
            ]

    async def get_videos(self, channel_id: str) -> list[dict]:
        async with self.db.execute_fetchall(
            "SELECT id, title, view_count, duration_string, timestamp FROM videos WHERE uploader_id = ?",
            (channel_id,)
        ) as results:
            return [
                {"id": id, "title": title, "view_count": view_count, "duration_string": duration_string, "timestamp": timestamp}
                for id, title, view_count, duration_string, timestamp in results
            ]

    async def get_video(self, video_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)) as result:
            result = await result.fetchone()
            return {k: result[i] for i, k in enumerate(VIDEO_PARAMETERS)} if result else None

    async def get_channel(self, channel_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)) as result:
            result = await result.fetchone()
            return {
                "id": result[0],
                "name": result[1],
                "subscribers": result[2]
            } if result else None

db = Database()

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
            return  # Video already exists

        info: dict[str, typing.Any] = self.ytdl.extract_info(f"https://youtu.be/{video_id}", download = True)  # type: ignore

        # Save everything to database
        channel_id = info["uploader_id"]
        if not await db.channel_exists(channel_id):
            await db.add_channel(channel_id, info["uploader"], info["channel_follower_count"])

        await db.add_video(*[
            info[parameter]
            for parameter in VIDEO_PARAMETERS
        ])

        # Reorganize everything
        channel_path = self.video_path / channel_id
        if not channel_path.is_dir():
            channel_path.mkdir(parents = True)

        for file in self.temp_path.iterdir():
            file.rename(channel_path / file.name)

# Handle API
@asynccontextmanager
async def lifespan(app: FastAPI) -> typing.AsyncGenerator:
    await db.init()
    yield

app = FastAPI(openapi_url = None, lifespan = lifespan)
app.state.snorlax = Snorlax()

templates = Jinja2Templates(directory = Path(__file__).parent / "templates")
templates.env.filters |= {"naturaltime": lambda x: naturaltime(datetime.fromtimestamp(x))}

# Routing
@app.get("/channel/{channel_id:str}", response_class = HTMLResponse)
async def route_channel(request: Request, channel_id: str):
    channel = await db.get_channel(channel_id)
    if channel is None:
        return templates.TemplateResponse(request, "404.jinja2")

    return templates.TemplateResponse(request, "channel.jinja2", {
        "channel": channel,
        "videos": await db.get_videos(channel_id)
    })

@app.get("/watch/{video_id:str}", response_class = HTMLResponse)
async def route_watch(request: Request, video_id: str):
    video_data = await db.get_video(video_id)
    if video_data is None:
        return templates.TemplateResponse(request, "404.jinja2")

    return templates.TemplateResponse(request, "video.jinja2", {
        "video": video_data,
        "channel": await db.get_channel(video_data["uploader_id"])
    })

# Download routes
@app.post("/download/video/{video_id:str}")
async def route_download_video(video_id: str, background_tasks: BackgroundTasks) -> JSONResponse:
    background_tasks.add_task(app.state.snorlax.fetch_video, video_id)
    return JSONResponse({"code": 202})

@app.post("/download/channel/{channel_id:str}")
async def route_download_channel(channel_id: str, background_tasks: BackgroundTasks) -> JSONResponse:
    background_tasks.add_task(app.state.snorlax.fetch_channel, channel_id)
    return JSONResponse({"code": 202})

# Mount /videos
app.mount("/videos", StaticFiles(directory = app.state.snorlax.video_path))
