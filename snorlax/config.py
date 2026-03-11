from pathlib import Path
import tomllib
from pydantic import BaseModel, DirectoryPath, FilePath

ROOT = Path(__file__).parent

# Load config file
class SnorlaxConfig(BaseModel):
    database_path: FilePath
    video_path:    DirectoryPath

class VideoConfig(BaseModel):
    subtitle_languages: list[str]

class Config(BaseModel):
    snorlax: SnorlaxConfig
    videos:  VideoConfig

config = Config(**tomllib.loads((ROOT.parent / "snorlax.toml").read_text()))
