# Copyright (c) 2025-2026 iiPython

# Modules
import asyncio
import typing
from shutil import rmtree
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketState
from pydantic import Field

from snorlax.config import ROOT, config
from snorlax.database import db
from snorlax.ingest import Snorlax

# Handle API
@asynccontextmanager
async def lifespan(app: FastAPI) -> typing.AsyncGenerator:
    await db.init()

    app.state.snorlax = Snorlax()
    asyncio.create_task(app.state.snorlax.process_queue())

    yield
    await db.close()

app = FastAPI(openapi_url = None, lifespan = lifespan)

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

@app.api_route("/v1/channel/{channel_id}", methods = ["GET", "DELETE"])
async def route_v1_channel(request: Request, channel_id: str, background_tasks: BackgroundTasks) -> JSONResponse:
    channel_data = await db.get_channel(channel_id)
    if channel_data is None:
        return JSONResponse({"code": 404, "data": {"message": "The specified channel does not exist."}}, status_code = 404)

    if request.method == "DELETE":
        await db.delete_channel(channel_data["id"])
        background_tasks.add_task(rmtree, config.snorlax.video_path / channel_data["id"], True)
        return JSONResponse({"code": 200})

    return JSONResponse({"code": 200, "data": channel_data})

@app.get("/v1/videos")
async def route_v1_videos(pagination: typing.Annotated[dict, Depends(pagination_parameters)], channel_id: str | None = None) -> JSONResponse:
    videos, total = await db.get_videos(channel_id = channel_id, **pagination)
    return JSONResponse({"code": 200, "data": {"items": videos, "total": total}})

@app.api_route("/v1/video/{video_id}", methods = ["GET", "DELETE"])
async def route_v1_video(request: Request, video_id: str, background_tasks: BackgroundTasks) -> JSONResponse:
    video_data = await db.get_video(video_id)
    if video_data is None:
        return JSONResponse({"code": 404, "data": {"message": "The specified video does not exist."}}, status_code = 404)

    if request.method == "DELETE":
        await db.delete_video(video_id)
        background_tasks.add_task(rmtree, config.snorlax.video_path / video_data["channel_id"] / video_id, True)
        return JSONResponse({"code": 200})

    return JSONResponse({"code": 200, "data": video_data})

@app.get("/v1/search")
async def route_v1_search(pagination: typing.Annotated[dict, Depends(pagination_parameters)], query: str) -> JSONResponse:
    videos, total = await db.search_videos(query, **pagination)
    return JSONResponse({"code": 200, "data": {"items": videos, "total": total}})

async def print_job_updates(websocket: WebSocket) -> None:
    while True:
        try:
            await websocket.send_json({
                video_id: job.get_progress()
                for video_id, job in app.state.snorlax.jobs.items()
            })
            await asyncio.sleep(2)

        except WebSocketDisconnect:
            break

@app.websocket("/v1/jobs")
async def route_v1_jobs(websocket: WebSocket) -> None:
    await websocket.accept()
    task = asyncio.create_task(print_job_updates(websocket))

    # Receive client data
    try:
        while websocket.application_state == WebSocketState.CONNECTED:
            match await websocket.receive_json():
                case {"type": "cancel-job", "id": video_id}:
                    await app.state.snorlax.cancel_job(video_id)

                case {"type": "add-job", "url": job_url}:
                    await app.state.snorlax.fetch_url(job_url)

    except WebSocketDisconnect:
        task.cancel()

# Mount assets
app.mount("/v1/assets", StaticFiles(directory = config.snorlax.video_path))

# Mount frontend
FRONTEND = ROOT / "frontend/dist"

@app.get("/{path:path}")
async def route_index(path: str) -> FileResponse:
    target = FRONTEND / path
    if not (target.is_relative_to(FRONTEND) and target.is_file()):
        return FileResponse(FRONTEND / "index.html")

    return FileResponse(target)
