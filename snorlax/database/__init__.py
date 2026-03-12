# Copyright (c) 2025-2026 iiPython

import typing
import aiosqlite
from snorlax.config import ROOT, config

VIDEO_PARAMS           = ("id", "title", "description", "view_count", "like_count", "duration_string", "timestamp", "channel_id", "caption_langs")
VIDEO_W_CHANNEL_PARAMS = VIDEO_PARAMS + ("channel_name", "channel_handle")
CHANNEL_PARAMS         = ("id", "handle", "name", "subscribers")

class Database:
    def __init__(self) -> None:
        self.db: aiosqlite.Connection

    async def init(self) -> None:
        self.db = await aiosqlite.connect(config.snorlax.database_path)

        # Initialize tables
        await self.db.executescript((ROOT / "database/tables.sql").read_text())
        await self.db.commit()

    async def close(self) -> None:
        await self.db.commit()
        await self.db.close()

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
    async def add_channel(self, id: str, handle: str | None, name: str, subscribers: int) -> None:
        await self.db.execute("INSERT OR IGNORE INTO channels VALUES (?, ?, ?, ?)", (id, handle, name, subscribers))
        await self.db.commit()

    async def get_channel(self, channel_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM channels WHERE id = ? OR handle = ?", (channel_id, channel_id)) as result:
            channel = await result.fetchone()
            return dict(zip(CHANNEL_PARAMS, channel)) if channel else None

    async def get_channels(self, limit: int | None = None, page: int | None = 1) -> tuple[list[dict], int]:
        return await self._fetch(
            table = "channels",
            columns = CHANNEL_PARAMS,
            order_by = "name ASC",
            limit = limit,
            page = page
        )

    # Videos
    async def add_video(self, **video) -> None:
        await self.db.execute(
            f"INSERT OR IGNORE INTO videos ({', '.join(VIDEO_PARAMS)}) VALUES ({', '.join('?' for _ in VIDEO_PARAMS)})",
            tuple(video[p] for p in VIDEO_PARAMS)
        )
        await self.db.commit()

    async def get_video(self, video_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute("SELECT * FROM videos_w_channel WHERE id = ?", (video_id,)) as result:
            result = await result.fetchone()
            return dict(zip(VIDEO_W_CHANNEL_PARAMS, result)) if result else None

    async def get_videos(self, channel_id: str | None = None, limit: int | None = None, page: int | None = 1) -> tuple[list[dict], int]:
        return await self._fetch(
            table = "videos_w_channel",
            columns = VIDEO_W_CHANNEL_PARAMS,
            filters = {"channel_id": channel_id} if channel_id is not None else {},
            order_by = "timestamp DESC",
            limit = limit,
            page = page
    )

db = Database()
