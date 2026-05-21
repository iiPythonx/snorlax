# Copyright (c) 2025-2026 iiPython

from enum import StrEnum
from dataclasses import dataclass

class JobStatus(StrEnum):
    QUEUED         = "queued"
    DOWNLOADING    = "downloading"
    POSTPROCESSING = "postprocessing"
    FINISHED       = "finished"
    FAILED         = "failed"
    CANCELED       = "canceled"

@dataclass
class Job:
    id:       str
    video_id: str
    url:      str

    status:   JobStatus    = JobStatus.QUEUED
    progress: int          = 0
    speed:    float | None = None
    eta:      int | None   = None
    error:    str | None   = None

@dataclass
class ProgressEvent:
    status:   str
    progress: int
    speed:    float | None
    eta:      int | None
