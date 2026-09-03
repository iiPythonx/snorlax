# Copyright (c) 2025-2026 iiPython

import asyncio
from uuid import uuid4

from snorlax import SNORLAX_LOGGER
from snorlax.database import VIDEO_COLUMNS, db
from snorlax.ingress import Job, dlp, run


class Queue:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self.active_jobs: dict[str, Job] = {}

    async def process(self) -> None:
        await self.fetch_old_queue()
        while True:
            job: Job = await self.queue.get()
            self.active_jobs[job.id] = job

            SNORLAX_LOGGER.debug(f"process({job.id}): now running: {job.video_id}")
            await run(self, job)
            SNORLAX_LOGGER.debug(f"process({job.id}): run has completed on {job.video_id}")

            self.queue.task_done()

    async def add(self, job: Job) -> None:
        await self.queue.put(job)
        SNORLAX_LOGGER.debug(f"add({job.id}): job added: {job}")

    async def fetch_old_queue(self) -> None:
        for job in await db.get_queued_jobs():
            await self.queue.put(Job(*job))

queue = Queue()

async def submit_url(url: str) -> None:
    async for item in dlp.resolve(url):
        existing_video = await db.get_video(item["id"]) or {"available": False}
        if existing_video["available"]:
            SNORLAX_LOGGER.debug(f"submit_url({item['id']}): requested video is already available")
            continue  # The video metadata exists AND the video file itself is already available

        if (job_data := await db.find_job_by_video_id(item["id"])) is not None:
            SNORLAX_LOGGER.debug(f"submit_url({item['id']}): request video already has a job for it ({job_data[0]})")
            continue  # There's already a job present for this video

        await db.add_channel(item["channel_id"], item.get("uploader_id"), item["uploader"], item["channel_follower_count"])
        await db.add_video(**{k: v for k, v in item.items() if k in VIDEO_COLUMNS.get("insert")} | \
            {"caption_langs": list((item["requested_subtitles"] or {}).keys()), "chapters": item["chapters"] or [], "available": False})

        job_id = str(uuid4())

        # Send job to database and immediate queue
        await db.add_job(job_id, item["id"], item["webpage_url"])
        SNORLAX_LOGGER.debug(f"submit_url({job_id}, {item['id']}): job created")
        await queue.add(Job(id = job_id, video_id = item["id"], url = item["webpage_url"]))
        SNORLAX_LOGGER.debug(f"submit_url({job_id}, {item['id']}): queued")
