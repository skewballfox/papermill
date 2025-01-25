"""
Abandon all hope, ye who enter here.

This module handles the process of extracting metadata from the supported content types. If there is one thing that is certain, it is that any method devised for extracting
metadata from a group of files from various sources will likely fail in some or even most cases, so the best approach is probably to chain together as many methods as possible
and document the failures.

"""

from dataclasses import InitVar, dataclass, field
from json import JSONEncoder
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, Sequence, Type, TypeVar
import warnings

from fancy_dataclass import JSONDataclass

from papermill import Config
from papermill.metadata.backup import backup_book_search
from papermill.metadata.isbn import search_isbn
from papermill.metadata.arxiv import search_arxiv_id
from papermill.metadata.base import ExtractionHelper, BookData, PaperData, SourceType


class UnReachable(Exception):
    pass


@dataclass
class OutlierData(JSONDataclass):
    filepath: Path
    """File path of the outlier"""
    extractors_attempted: list[str] = field(default_factory=list)
    """List of extractor names that were attempted on the file"""

    # Patch until fancy_dataclass supports Path
    # see https://github.com/jeremander/fancy-dataclass/issues/1
    @classmethod
    def json_encoder(cls):
        class Encoder(JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Path):
                    return str(obj)
                return JSONDataclass.json_encoder().default(self, obj)

        return Encoder

    @classmethod
    def _from_dict_value_basic(cls, tp, val):
        if issubclass(tp, Path):
            return Path(val)
        return super()._from_dict_value_basic(tp, val)


supported_book_extensions = {".pdf", ".epub"}
supported_paper_extensions = {".pdf"}

Deserializable = TypeVar("Deserializable", bound=JSONDataclass)


DataExtractor = Callable[[ExtractionHelper, Path], Optional[SourceType]]


def deserialize_or_delete(
    file: Path, func: Callable[[Any], Deserializable]
) -> Optional[Deserializable]:
    with open(file) as f:
        try:
            return func(f)
        except Exception as e:
            warnings.warn(
                f"Failed to deserialize {file}, deleting it\nreason: {e}\n filecontent: {f.read()}"
            )
    file.unlink(missing_ok=True)
    return None


def try_from_cache(
    file: Path, func: Callable[[Any], Deserializable]
) -> Optional[Deserializable]:
    if file.exists():
        return deserialize_or_delete(file, func)
    return None


# @dataclass
# MetaMiner(Generic[SourceType]):


@dataclass
class MetadataHandler:
    config: Config
    helper = ExtractionHelper()
    book_extractors: List[DataExtractor[BookData]] = field(
        default_factory=lambda: [
            search_isbn,
            backup_book_search,
        ],
    )
    paper_extractors: List[DataExtractor[PaperData]] = field(
        default_factory=lambda: [
            search_arxiv_id,
        ],
    )

    def _get_metadata(
        self, file: Path, document_type: Type[SourceType]
    ) -> Optional[SourceType]:
        extractors: Sequence[DataExtractor[SourceType]]
        category: str
        match document_type.__name__:
            case "BookData":
                category = "books"
                supported_extensions = supported_book_extensions
                extractors = self.book_extractors  # type: ignore
            case "PaperData":
                category = "papers"
                supported_extensions = supported_paper_extensions
                extractors = self.paper_extractors  # type: ignore
            case _:
                raise UnReachable("Should never ever happen")

        category_path = self.config.metadata_path / category
        outlier_path = self.config.metadata_path / "Outliers" / category
        category_path.mkdir(parents=True, exist_ok=True)
        outlier_path.mkdir(parents=True, exist_ok=True)

        # sanity check
        if not file.is_file() or file.suffix not in supported_extensions:
            return None

        if doc_data := try_from_cache(
            category_path / f"{file.stem}.json", document_type.from_json
        ):
            return doc_data

        # get the list of previously failed extractors for a file, if any
        failed_extractors = set()
        if outlier_data := try_from_cache(
            outlier_path / (file.stem + ".json"), OutlierData.from_json
        ):
            failed_extractors = set(outlier_data.extractors_attempted)

        for extractor in extractors:
            if extractor.__name__ in failed_extractors:
                continue
            # cache and return the data if the extractor is successful
            if data := extractor(self.helper, file):
                with open(category_path / f"{file.stem}.json", "w") as f:
                    data.to_json(f)
                return data
        # if we reach this point, save the failed extractors to the outlier file
        with open(outlier_path / f"{file.stem}.json", "w") as f:
            OutlierData(
                file,
                [extractor.__name__ for extractor in extractors],
            ).to_json(f)
        return None

    def get_book(self, book: Path) -> Optional[BookData]:
        # sanity check
        return self._get_metadata(book, BookData)

    def get_paper(self, paper: Path) -> Optional[PaperData]:
        # sanity check
        return self._get_metadata(paper, PaperData)

    @property
    def books(self):
        for book in self.config.books_path.iterdir():
            if data := self.get_book(book):
                yield data

    @property
    def papers(self):
        for paper in self.config.papers_path.iterdir():
            if data := self.get_paper(paper):
                yield data
