# Copyright (c) 2025-2026 iiPython

from functools import lru_cache
from typing import Literal, Sequence

type ColumnType = Literal["base", "full", "insert", "json", "job"]
type ColumnList = list[tuple[str, Sequence[ColumnType]]]

class Columns:
    VIDEO: ColumnList = [
        # Column name            | Base  | Full  | Insert  | JSON  | Job
        ("id",                   ["base", "full", "insert",         "job"]),
        ("title",                ["base", "full", "insert",         "job"]),
        ("duration",             ["base", "full", "insert",         "job"]),
        ("view_count",           ["base", "full", "insert"               ]),
        ("timestamp",            ["base", "full", "insert",         "job"]),
        ("channel_id",           ["base", "full", "insert",         "job"]),
        ("channel_name",         ["base", "full",                   "job"]),
        ("channel_preferred_id", ["base", "full",                   "job"]),
        ("available",            ["base", "full", "insert"               ]),
        ("like_count",           [        "full", "insert"               ]),
        ("description",          [        "full", "insert"               ]),
        ("caption_langs",        [        "full", "insert", "json"       ]),
        ("chapters",             [        "full", "insert", "json"       ]),
        ("job_id",               [                                  "job"]),
        ("status",               [                                  "job"]),
        ("progress",             [                                  "job"]),
        ("speed",                [                                  "job"]),
        ("eta",                  [                                  "job"]),
        ("error",                [                                  "job"]),
    ]

    CHANNEL: ColumnList = [
        ("id",           ["base"]),
        ("handle",       ["base"]),
        ("name",         ["base"]),
        ("subscribers",  ["base"]),
        ("preferred_id", ["base"]),
    ]

class ColumnSet:
    def __init__(self, columns: ColumnList):
        self._columns = columns

    @lru_cache
    def get(self, column_type: ColumnType) -> tuple[str, ...]:
        return tuple(k for k, v in self._columns if column_type in v)

VIDEO_COLUMNS = ColumnSet(Columns.VIDEO)
CHANNEL_COLUMNS = ColumnSet(Columns.CHANNEL)
