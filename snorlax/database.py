# Copyright (c) 2025-2026 iiPython

import typing
import aiosqlite

VIDEO_PARAMETERS = ("id", "title", "description", "view_count", "like_count", "duration_string", "timestamp", "uploader_id")
CHANNEL_PARAMETERS = ("id", "name", "subscribers")

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

    # Channels
    async def get_channel(self, channel_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)) as result:
            channel = await result.fetchone()
            return dict(zip(CHANNEL_PARAMETERS, channel)) if channel else None

    async def get_channels(self, search: str | None = None, limit: int | None = None) -> list[dict]:
        query, params = "SELECT * FROM channels", []
        if search is not None:
            query += " WHERE name LIKE ?"
            params.append(f"%{search}%")

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        async with self.db.execute_fetchall(query, params) as channels:
            return [dict(zip(CHANNEL_PARAMETERS, channel)) for channel in channels]

    # Videos
    async def get_video(self, video_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)) as result:
            result = await result.fetchone()
            return dict(zip(VIDEO_PARAMETERS, result)) if result else None

    async def get_videos(self, channel_id: str | None = None, limit: int | None = None) -> list[dict]:
        query, params = f"SELECT {', '.join(VIDEO_PARAMETERS)} FROM videos", []
        if channel_id is not None:
            query += " WHERE uploader_id = ?"
            params.append(channel_id)

        query += " ORDER BY timestamp DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        async with self.db.execute_fetchall(query, params) as results:
            return [dict(zip(VIDEO_PARAMETERS, row)) for row in results]

db = Database()
