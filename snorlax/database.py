# Copyright (c) 2025-2026 iiPython

import typing
import aiosqlite

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
