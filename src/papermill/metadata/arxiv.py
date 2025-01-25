from typing import Optional
from pathlib import Path

from requests import HTTPError


from papermill.metadata.base import ExtractionHelper, PaperData
import flpc
from urllib import request
import sys
import xmltodict  # type: ignore

arxiv_id = flpc.compile(r"^[0-9]{4}\.[0-9]{4,5}(v\d)?$", flags=0)
arxiv_api = "http://export.arxiv.org/api/query?id_list="


def search_arxiv_id(_: ExtractionHelper, paper_path: Path) -> Optional[PaperData]:
    if flpc.fullmatch(arxiv_id, str(paper_path.stem)):
        query = arxiv_api + str(paper_path.stem)
        try:
            with request.urlopen(query) as response:
                data = xmltodict.parse(response.read().decode("utf-8"))
                if int(data["feed"]["opensearch:totalResults"]["#text"]) > 1:
                    # TODO: Log conflicts
                    print(
                        f"Warning: Multiple papers found with the same arXiv ID {paper_path.stem}"
                    )
                data = data["feed"]["entry"]
                print(data["author"])
                return PaperData(
                    title=data["title"],
                    abstract=data["summary"],
                    publication_date=data["published"],
                    authors=[author["name"] for author in data["author"]]
                    if isinstance(data["author"], list)
                    else [data["author"]["name"]],
                )
        except HTTPError as e:
            # log malformed requests
            print(f"Error: {e}")
    return None
