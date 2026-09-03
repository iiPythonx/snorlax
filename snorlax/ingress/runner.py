# Copyright (c) 2025-2026 iiPython

import asyncio
import traceback
from time import time

from yt_dlp.utils import DownloadError

from snorlax import SNORLAX_LOGGER
from snorlax.config import config
from snorlax.database import db
from snorlax.ingress import TEMP_PATH, Job, ProgressEvent, dlp

SUFFIX_MAPPING = {".webp": "cover", ".vtt": "sub", ".mkv": "video"}

def migrate_files(video_id: str, channel_id: str) -> None:
    video_path = config.snorlax.video_path / channel_id / video_id
    if not video_path.is_dir():
        video_path.mkdir(parents = True)

    SNORLAX_LOGGER.debug(f"organize({video_id}): began renaming files")
    for file in TEMP_PATH.glob(f"{video_id}*"):
        if file.suffix not in SUFFIX_MAPPING:
            return SNORLAX_LOGGER.debug(f"organize({video_id}): unknown file suffix found in download location: {file.suffix}")

        file.rename(video_path / file.name.replace(video_id, SUFFIX_MAPPING[file.suffix]))

    SNORLAX_LOGGER.debug(f"organize({video_id}): file rename complete")

async def organize(job: Job) -> None:
    video_data = await db.get_video(job.video_id)
    if video_data is None:
        raise RuntimeError(f"get_video({job.id}, {job.video_id}) returned None during attempted organization")

    await asyncio.to_thread(migrate_files, job.video_id, video_data["channel_id"])

async def run(queue, job: Job) -> None:
    last_status: str = ""

    queue.active_jobs[job.id] = job

    async def progress_hook(event: ProgressEvent) -> None:
        nonlocal last_status

        job.eta, job.speed, job.progress = event.eta, event.speed, event.progress
        if event.status != last_status:
            start_time = time()
            await db.update_job(job.id, status = event.status)
            SNORLAX_LOGGER.debug(f"progress_hook({job.id}): job status updated to {event.status}, took {(time() - start_time) * 1000:.0f}ms")

        last_status = event.status

    try:
        await dlp.download(job, progress_hook)

        # Ensure we're in the postprocessing stage, and then organize files
        start_time = time()
        await db.update_job(job.id, status = "postprocessing")
        SNORLAX_LOGGER.debug(f"run({job.id}): status set to postprocessing successfully, took {(time() - start_time) * 1000:.0f}ms!")
        await organize(job)

        # And then we're done
        await db.update_job(job.id, status = "finished")
        await db.set_video_available(job.video_id, available = True)

    except DownloadError:
        SNORLAX_LOGGER.debug(f"run({job.id}): job failed")
        await db.update_job(job.id, status = "failed")

        # Current exceptions not finalized, so just track everything
        traceback.print_exc()

