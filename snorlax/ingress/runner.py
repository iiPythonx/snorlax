# Copyright (c) 2025-2026 iiPython

import traceback
from time import time

from snorlax.config import config
from snorlax.database import db
from snorlax.ingress import dlp, Job, ProgressEvent, TEMP_PATH

SUFFIX_MAPPING = {".webp": "cover", ".vtt": "sub", ".mkv": "video"}

async def organize(job: Job) -> None:
    video_data = await db.get_video(job.video_id)
    if video_data is None:
        raise RuntimeError("get_video() returned None during attempted organization")

    video_path = config.snorlax.video_path / video_data["channel_id"] / job.video_id
    if not video_path.is_dir():
        video_path.mkdir(parents = True)

    print("organize(): began renaming files")
    for file in TEMP_PATH.glob(f"{job.video_id}*"):
        if file.suffix not in SUFFIX_MAPPING:
            continue  # debug message eventually

        file.rename(video_path / file.name.replace(job.video_id, SUFFIX_MAPPING[file.suffix]))

    print("organize(): file rename complete")

async def run(job: Job) -> None:
    last_status: str = ""

    async def progress_hook(event: ProgressEvent) -> None:
        nonlocal last_status

        job.eta, job.speed, job.progress = event.eta, event.speed, event.progress
        if event.status != last_status:
            print(f"progress_hook(): trying to update job status at {time()}")
            await db.update_job(job.id, status = event.status)
            print(f"progress_hook(): job status updated to {event.status}")

        last_status = event.status

    try:
        await dlp.download(job, progress_hook)

        # Ensure we're in the postprocessing stage, and then organize files
        print(f"run(): updating status to postprocessing at {time()}")
        await db.update_job(job.id, status = "postprocessing")
        print("run(): status set to postprocessing successfully!")
        await organize(job)

        # And then we're done
        await db.update_job(job.id, status = "finished")
        await db.set_video_available(job.video_id, available = True)

    except Exception:
        await db.update_job(job.id, status = "failed")

        # Current exceptions not finalized, so just track everything
        traceback.print_exc()

