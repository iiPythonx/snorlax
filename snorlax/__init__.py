# Copyright (c) 2025-2026 iiPython

# Modules
import typing
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from humanize import naturaltime
from starlette.exceptions import HTTPException

from snorlax.ingest import Snorlax
from snorlax.database import db

# Handle API
@asynccontextmanager
async def lifespan(app: FastAPI) -> typing.AsyncGenerator:
    await db.init()
    yield

app = FastAPI(openapi_url = None, lifespan = lifespan)
app.state.snorlax = Snorlax()

templates = Jinja2Templates(directory = Path(__file__).parent / "templates")
templates.env.filters |= {"naturaltime": lambda x: naturaltime(datetime.fromtimestamp(x))}

# Exception processing
@app.exception_handler(HTTPException)
async def handle_exception(request: Request, exception: HTTPException):
    return templates.TemplateResponse(request, f"errors/{exception.status_code}.jinja2")

# Routing
@app.get("/", response_class = HTMLResponse)
async def route_home(request: Request):
    return templates.TemplateResponse(request, "pages/home.jinja2", {
        "videos": await db.get_videos(limit = 12),
        "channels": await db.get_channels(limit = 8)
    })

@app.get("/channel/{channel_id:str}", response_class = HTMLResponse)
async def route_channel(request: Request, channel_id: str):
    channel = await db.get_channel(channel_id)
    if channel is None:
        raise HTTPException(status_code = 404)

    return templates.TemplateResponse(request, "pages/channel.jinja2", {
        "channel": channel,
        "videos": await db.get_videos(channel_id)
    })

@app.get("/watch/{video_id:str}", response_class = HTMLResponse)
async def route_watch(request: Request, video_id: str):
    video_data = await db.get_video(video_id)
    if video_data is None:
        raise HTTPException(status_code = 404)

    return templates.TemplateResponse(request, "pages/video.jinja2", {
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
app.mount("/", StaticFiles(directory = Path(__file__).parent / "static"))
