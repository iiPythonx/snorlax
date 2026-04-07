# Copyright (c) 2025-2026 iiPython

# Modules
import asyncio
import typing
from shutil import rmtree
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Body, Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from snorlax.config import ROOT, config
from snorlax.database import db
from snorlax.ingest import process_queue, store

# Handle API
@asynccontextmanager
async def lifespan(_: FastAPI) -> typing.AsyncGenerator:
    await db.init()

    asyncio.create_task(process_queue())

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
async def route_v1_videos(pagination: typing.Annotated[dict, Depends(pagination_parameters)], channel_id: str | None = None, query: str | None = None) -> JSONResponse:
    videos, total = await db.get_videos(query = query, channel_id = channel_id, **pagination)
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

@app.get("/v1/jobs")
async def route_v1_jobs(pagination: typing.Annotated[dict, Depends(pagination_parameters)]) -> JSONResponse:
    jobs, total = await db.get_jobs(**pagination)
    return JSONResponse({"code": 200, "data": {"items": jobs, "total": total}})

@app.post("/v1/jobs/create")
async def route_v1_job_create(url: typing.Annotated[str, Body(embed = True)]) -> JSONResponse:
    success, error = await store.create(url)
    return JSONResponse({
        "code": 200 if success else 400,
        "data": {"message": error}
    }, status_code = 200 if success else 400)

@app.delete("/v1/jobs/{job_id}")
async def route_v1_job_delete(job_id: str) -> JSONResponse:
    success = await db.delete_job(job_id)
    if not success:
        return JSONResponse({"code": 404, "data": {"message": "The specified job does not exist."}}, status_code = 404)

    await store.cancel(job_id)
    return JSONResponse({"code": 200})

# Mount assets
config.snorlax.video_path.mkdir(exist_ok = True)
app.mount("/v1/assets", StaticFiles(directory = config.snorlax.video_path))

# Mount frontend
FRONTEND = ROOT / "frontend/dist"

@app.get("/{path:path}")
async def route_index(path: str) -> FileResponse:
    target = FRONTEND / path
    if not (target.is_relative_to(FRONTEND) and target.is_file()):
        return FileResponse(FRONTEND / "index.html")

    return FileResponse(target)
