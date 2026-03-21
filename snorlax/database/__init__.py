# Copyright (c) 2025-2026 iiPython

import json
import string
import typing

import aiosqlite

from snorlax.config import ROOT, config

VIDEO_PARAMS           = ("id", "title", "description", "view_count", "like_count", "duration_string", "timestamp", "channel_id", "caption_langs", "chapters")
VIDEO_W_CHANNEL_PARAMS = VIDEO_PARAMS + ("channel_name", "channel_preferred_id")
CHANNEL_PARAMS         = ("id", "handle", "name", "subscribers", "preferred_id")
JSON_COLUMNS           = ("caption_langs", "chapters")

SEARCH_VALID_TOKENS = string.ascii_letters + string.digits + " "

class Database:
    def __init__(self) -> None:
        self.db: aiosqlite.Connection

    async def init(self) -> None:
        self.db = await aiosqlite.connect(config.snorlax.database_path)

        # Initialize tables
        await self.db.executescript((ROOT / "database/tables.sql").read_text())

        # Handle FTS
        async with self.db.execute_fetchall("SELECT 1 FROM videos_fts LIMIT 1") as response:
            if not response:
                await self.db.execute("""
                    INSERT INTO videos_fts(rowid, title, description, channel_name)
                    SELECT v.rowid, v.title, v.description, c.name
                    FROM videos v
                    JOIN channels c ON c.id = v.channel_id;
                """)

        await self.db.commit()

    async def close(self) -> None:
        await self.db.commit()
        await self.db.close()

    # JSON storage
    @staticmethod
    def _serialize(result: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return result | {
            k: json.dumps(v)
            for k, v in result.items() if k in JSON_COLUMNS
        }

    @staticmethod
    def _deserialize(result: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return result | {
            k: json.loads(v)
            for k, v in result.items() if k in JSON_COLUMNS
        }

    # Querying
    @staticmethod
    def _build_column_string(columns: tuple[str, ...], alias: str | None = None) -> str:
        return ", ".join(
            f"{alias}.{column} as {column}" if alias else column
            for column in columns
        )

    async def _fetch(
        self,
        table: str,
        columns: tuple[str, ...],
        filters: list[tuple[str, str, typing.Any]] | None = None,
        joins: list[str] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        page: int | None = 1
    ) -> tuple[list[dict], int]:
        select_columns = self._build_column_string(columns, alias = "v" if joins else None)
        query, params = f"SELECT {select_columns} FROM {table}", []

        # Handle joining
        if joins:
            query += f" {' '.join(joins)}"

        # Handle filtering
        if filters:
            query += " WHERE " + " AND ".join(f"{column} {operator} ?" for column, operator, _ in filters)
            params.extend(value for _, _, value in filters)

        # Handle counting
        count_query = f"SELECT COUNT(*) FROM {table}"
        if joins:
            count_query += f" {' '.join(joins)}"

        if filters:
            count_query += " WHERE " + " AND ".join(f"{column} {operator} ?" for column, operator, _ in filters)

        count_result = await (await self.db.execute(count_query, params)).fetchone()
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
            return [self._deserialize(dict(zip(columns, row))) for row in rows], count_result[0]

    # Channels
    async def add_channel(self, channel_id: str, handle: str | None, name: str, subscribers: int) -> None:
        await self.db.execute("INSERT OR IGNORE INTO channels VALUES (?, ?, ?, ?)", (channel_id, handle, name, subscribers))
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

    async def delete_channel(self, channel_id: str) -> None:
        await self.db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await self.db.commit()

    # Videos
    async def add_video(self, **video) -> None:
        video = self._serialize(video)
        await self.db.execute(
            f"INSERT OR IGNORE INTO videos ({', '.join(VIDEO_PARAMS)}) VALUES ({', '.join('?' for _ in VIDEO_PARAMS)})",
            tuple(video[p] for p in VIDEO_PARAMS)
        )
        await self.db.commit()

    async def get_video(self, video_id: str) -> dict[str, typing.Any] | None:
        async with self.db.execute(f"SELECT {', '.join(VIDEO_W_CHANNEL_PARAMS)} FROM videos_w_channel WHERE id = ?", (video_id,)) as result:
            result = await result.fetchone()
            return self._deserialize(dict(zip(VIDEO_W_CHANNEL_PARAMS, result))) if result else None

    async def get_videos(self, channel_id: str | None = None, limit: int | None = None, page: int | None = 1) -> tuple[list[dict], int]:
        return await self._fetch(
            table = "videos_w_channel",
            columns = VIDEO_W_CHANNEL_PARAMS,
            filters = [("channel_id", "=", channel_id)] if channel_id is not None else [],
            order_by = "timestamp DESC",
            limit = limit,
            page = page
        )

    async def search_videos(self, query: str, limit: int | None = None, page: int | None = 1) -> tuple[list[dict[str, typing.Any]], int]:
        query = "".join(c for c in query if c in SEARCH_VALID_TOKENS)
        if not query.strip():
            return [], 0

        return await self._fetch(
            table = "videos_fts f",
            columns = VIDEO_W_CHANNEL_PARAMS,
            filters = [("videos_fts", "MATCH", " ".join(f"{word}*" for word in query.split()))],
            joins = ["JOIN videos_w_channel v ON v.rowid = f.rowid"],
            order_by = "bm25(videos_fts)",
            limit = limit,
            page = page
        )

    async def delete_video(self, video_id: str) -> None:
        await self.db.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        await self.db.commit()

db = Database()
