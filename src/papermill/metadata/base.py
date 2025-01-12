"""
Defines the ExtractionHelper, which serves to provide a uniform interface for testing various tools against each other (such as Extractous and PyMuPDF).
I suspect that we'll wind up adding other types of extraction tools later once we have to get
more creative with how we are extracting metadata
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, TypeVar
from extractous import Extractor as Extractous  # type: ignore
from fancy_dataclass import JSONDataclass
from cachetools import cached
from cachetools.keys import hashkey


@dataclass
class BookData(JSONDataclass):
    title: str
    """Title of the book"""
    isbn: str
    """ISBN number of the book"""
    description: str
    """Description of the book"""
    published_date: str
    """Published date of the book"""
    authors: List[str] = field(default_factory=list)
    """List of authors of the book"""


@dataclass
class PaperData(JSONDataclass):
    title: str
    """Title of the paper"""
    abstract: str
    """Abstract of the paper"""
    publication_date: str
    """Publication date of the paper"""
    authors: List[str] = field(default_factory=list)
    """List of authors of the paper"""


SourceType = TypeVar("SourceType", BookData, PaperData)


@dataclass
class ExtractionHelper:
    __extractor = Extractous()

    @cached(cache={}, key=lambda self, file, limit=4096: hashkey(file, limit))
    def get_text(self, file: Path, limit=4096) -> str:
        """Get the text from a file, defaults to the first 4096 bytes. If the limit is set to 0, reads the entire file"""

        reader, _ = self.__extractor.extract_file(str(file))
        if limit == 0:
            return reader.read().decode("utf-8")
        return reader.read(limit).decode("utf-8")
