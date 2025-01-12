from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from fancy_dataclass import TOMLDataclass

project_root = Path(__file__).parent.parent.parent


@dataclass
class Config(TOMLDataclass):
    books_path: Optional[Path] = None
    """Path to the directory containing the books."""
    papers_path: Optional[Path] = None
    """Path to the directory containing the papers."""
    metadata_path: Path = project_root / "data"
    """Path to the directory containing generated metadata."""
    client_param: str = ":memory:"
    """The qdrant client string, defaults to in memory."""

    # Patch until fancy_dataclass supports Path
    # see https://github.com/jeremander/fancy-dataclass/issues/1
    @classmethod
    def _from_dict_value_basic(cls, tp, val):
        if issubclass(tp, Path):
            return Path(val)
        return super()._from_dict_value_basic(tp, val)


def dev_config() -> Config:
    with open(project_root / "config.toml") as f:
        return Config.from_toml(f)
