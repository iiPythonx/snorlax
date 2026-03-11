# Copyright (c) 2025-2026 iiPython

# Modules
import typing
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import Field
from starlette.exceptions import HTTPException

from snorlax.config import config
from snorlax.ingest import Snorlax
from snorlax.database import db

# Handle API
@asynccontextmanager
async def lifespan(app: FastAPI) -> typing.AsyncGenerator:
    await db.init()
    yield
    await db.close()

app = FastAPI(openapi_url = None, lifespan = lifespan)
app.state.snorlax = Snorlax()

templates = Jinja2Templates(directory = config.TEMPLATE_PATH)

# Exception processing
@app.exception_handler(HTTPException)
async def handle_exception(request: Request, exception: HTTPException):
    return templates.TemplateResponse(
        request,
        f"errors/{exception.status_code}.jinja2",
        status_code = exception.status_code
    )

# API
async def pagination_parameters(
    limit: typing.Annotated[int, Field(ge = 1, le = 30)] = 20,
    page: typing.Annotated[int, Field(ge = 1)] = 1
) -> dict[str, int]:
    return {"limit": limit, "page": page}

@app.get("/v1/channels")
async def route_v1_channels(pagination: typing.Annotated[dict, Depends(pagination_parameters)]) -> JSONResponse:
    channels, total = await db.get_channels(**pagination)
    return JSONResponse({"code": 200, "data": {"items": channels, "total": total}})

@app.get("/v1/channel/{channel_id}")
async def route_v1_channel(channel_id: str) -> JSONResponse:
    channel_data = await db.get_channel(channel_id)
    if channel_data is None:
        return JSONResponse({"code": 404, "data": {"message": "The specified channel does not exist."}}, status_code = 404)

    return JSONResponse({"code": 200, "data": channel_data})

@app.get("/v1/videos")
async def route_v1_videos(pagination: typing.Annotated[dict, Depends(pagination_parameters)], channel_id: str | None = None) -> JSONResponse:
    videos, total = await db.get_videos(channel_id = channel_id, **pagination)
    return JSONResponse({"code": 200, "data": {"items": videos, "total": total}})

@app.get("/v1/video/{video_id}")
async def route_v1_video(video_id: str) -> JSONResponse:
    video_data = await db.get_video(video_id)
    if video_data is None:
        return JSONResponse({"code": 404, "data": {"message": "The specified video does not exist."}}, status_code = 404)

    return JSONResponse({"code": 200, "data": video_data})

# Routing
@app.get("/", response_class = HTMLResponse)
async def route_home(request: Request):
    return templates.TemplateResponse(request, "pages/home.jinja2")

@app.get("/channel/{channel_id:str}", response_class = HTMLResponse)
async def route_channel(request: Request, channel_id: str):
    channel = await db.get_channel(channel_id)
    if channel is None:
        raise HTTPException(status_code = 404)

    return templates.TemplateResponse(request, "pages/channel.jinja2", {"channel": channel})

@app.get("/watch/{video_id}", response_class = HTMLResponse)
async def route_watch(request: Request, video_id: str):
    return templates.TemplateResponse(request, "pages/video.jinja2")

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
app.mount("/videos", StaticFiles(directory = config.VIDEO_PATH))
app.mount("/", StaticFiles(directory = config.STATIC_PATH))
