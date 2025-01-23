from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    IMAGE_SAVE_DIR: Path
    ERROR_DIR: Path


def load_config() -> Config:
    image_save_dir = Path(__file__).parents[1].joinpath('images').resolve()

    return Config(
        IMAGE_SAVE_DIR=image_save_dir,
        ERROR_DIR=image_save_dir.joinpath('error'),
    )
