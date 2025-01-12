from dataclasses import dataclass
import sys
from typing import List, Optional, Type, TYPE_CHECKING
from fancy_dataclass import JSONDataclass
import flpc
from requests import request
from pathlib import Path


from papermill.metadata.base import BookData, ExtractionHelper


def backup_book_search(
    helper: ExtractionHelper, book_path: Path
) -> Optional["BookData"]:
    # TODO: Implement backup search
    return None
