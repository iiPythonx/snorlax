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

    # Querying
    async def _fetch(
        self,
        table: str,
        columns: tuple[str, ...],
        filters: dict[str, typing.Any] = {},
        order_by: str | None = None,
        limit: int | None = None,
        page: int | None = 1
    ) -> tuple[list[dict], int]:
        query, params = f"SELECT {', '.join(columns)} FROM {table}", []
        if filters:
            query += " WHERE " + " AND ".join(f"{k} = ?" for k in filters)
            params.extend(filters.values())

        # Handle counting
        count_query = f"SELECT COUNT(*) FROM {table}"
        if filters:
            count_query += " WHERE " + " AND ".join(f"{k} = ?" for k in filters)

        count_result = await (await self.db.execute(count_query, list(filters.values()))).fetchone()
        if count_result is None:
            raise RuntimeError("SQL returned no count data!")

        # Handle ordering, limiting, pagination
        if order_by:
            query += f" ORDER BY {order_by}"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

            if page is not None and page > 1:
                offset = (page - 1) * limit
                query += " OFFSET ?"
                params.append(offset)

        async with self.db.execute_fetchall(query, params) as rows:
            return [dict(zip(columns, row)) for row in rows], count_result[0]

    # Channels
    async def get_channel(self, channel_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)) as result:
            channel = await result.fetchone()
            return dict(zip(CHANNEL_PARAMETERS, channel)) if channel else None

    async def get_channels(self, limit: int | None = None, page: int | None = 1) -> tuple[list[dict], int]:
        return await self._fetch(
            table = "channels",
            columns = CHANNEL_PARAMETERS,
            order_by = "name ASC",
            limit = limit,
            page = page
        )

    # Videos
    async def get_video(self, video_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)) as result:
            result = await result.fetchone()
            return dict(zip(VIDEO_PARAMETERS, result)) if result else None

    async def get_videos(self, channel_id: str | None = None, limit: int | None = None, page: int | None = 1) -> tuple[list[dict], int]:
        filters = {}
        if channel_id is not None:
            filters["uploader_id"] = channel_id

        return await self._fetch(
            table = "videos",
            columns = VIDEO_PARAMETERS,
            filters = filters,
            order_by = "timestamp DESC",
            limit = limit,
            page = page
    )

db = Database()
