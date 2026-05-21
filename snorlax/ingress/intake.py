# Copyright (c) 2025-2026 iiPython

import asyncio
from uuid import uuid4

from snorlax.ingress import run, dlp, Job
from snorlax.database import db, VIDEO_COLUMNS

class Queue:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[Job] = asyncio.Queue()
        self.active_jobs: dict[str, Job] = {}

    async def process(self) -> None:
        await self.fetch_old_queue()
        while True:
            job: Job = await self.queue.get()
            self.active_jobs[job.id] = job

            print("process(): now running:", job.id, job.video_id)
            await run(job)
            print(f"process(): run has completed on {job.id} / {job.video_id}")

            self.queue.task_done()

    async def add(self, job: Job) -> None:
        await self.queue.put(job)
        print(f"add(): job added: {job}")

    async def fetch_old_queue(self) -> None:
        for job in await db.get_queued_jobs():
            await self.queue.put(Job(*job))

queue = Queue()

async def submit_url(url: str) -> None:
    async for item in dlp.resolve(url):
        existing_video = await db.get_video(item["id"]) or {"available": False}
        if existing_video["available"]:
            print("submit_url(): requested video is already available")
            continue  # The video metadata exists AND the video file itself is already available

        if await db.find_job_by_video_id(item["id"]) is not None:
            print("submit_url(): request video already has a job for it")
            continue  # There's already a job present for this video

        await db.add_channel(item["channel_id"], item.get("uploader_id"), item["uploader"], item["channel_follower_count"])
        await db.add_video(**{k: v for k, v in item.items() if k in VIDEO_COLUMNS.get("insert")} | \
            {"caption_langs": list((item["requested_subtitles"] or {}).keys()), "chapters": item["chapters"] or [], "available": False})

        job_id = str(uuid4())

        # Send job to database and immediate queue
        await db.add_job(job_id, item["id"], item["webpage_url"])
        print(f"submit_url(): {item['id']}: job created")
        await queue.add(Job(id = job_id, video_id = item["id"], url = item["webpage_url"]))
        print(f"submit_url(): {item['id']}: queued")
