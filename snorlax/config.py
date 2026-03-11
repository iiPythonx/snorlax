# Copyright (c) 2025-2026 iiPython

import tomllib
from pathlib import Path
from pydantic import BaseModel, DirectoryPath, FilePath

ROOT = Path(__file__).parent

class SnorlaxConfig(BaseModel):
    database_path: FilePath
    video_path:    DirectoryPath

class VideoConfig(BaseModel):
    subtitle_languages: list[str]

class Config(BaseModel):
    snorlax: SnorlaxConfig
    videos:  VideoConfig

# Load config file
config = Config(**tomllib.loads((ROOT.parent / "snorlax.toml").read_text()))
