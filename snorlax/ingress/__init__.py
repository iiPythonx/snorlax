# Copyright (c) 2025-2026 iiPython

import typing
from enum import StrEnum
from dataclasses import dataclass

from snorlax.config import config

TEMP_PATH = config.snorlax.video_path / "in_progress"

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

    def build_status(self) -> dict[str, typing.Any]:
        return {
            "progress": self.progress,
            "speed": self.speed,
            "eta": self.eta
        }

@dataclass
class ProgressEvent:
    status:   str
    progress: int
    speed:    float | None
    eta:      int | None

# Shared imports
from .dlp import dlp
from .runner import run
from .intake import queue
