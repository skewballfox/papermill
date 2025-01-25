from typing import Optional
from pathlib import Path


from papermill.metadata.base import ExtractionHelper, BookData
import flpc
from urllib import request
import sys
import json

isbn10or13 = flpc.compile(
    r"(?:ISBN(?:-1[03])?:?●)?(?:97[89][-●]?[0-9]{1,5}[-●]?[0-9]+[-●]?[0-9]+[-●]?[0-9X]|[0-9]{1,5}[-●]?[0-9]+[-●]?[0-9]+[-●]?[0-9X]{10}|[0-9]{13}|[0-9]+[-●][0-9]+[-●][0-9]+[-●][0-9X]{17})",
    flags=0,
)

google_books_isbn_api = "https://www.googleapis.com/books/v1/volumes?q=isbn:"


def search_isbn(helper: ExtractionHelper, book_path: Path) -> Optional["BookData"]:
    book_text = helper.get_text(book_path)
    for isbn in flpc.findall(isbn10or13, book_text):
        with request.urlopen(google_books_isbn_api + isbn) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data["totalItems"] > 0:
                if data["totalItems"] > 1:
                    print("Warning: Multiple books found with the same ISBN")
                    print(data["items"])
                    sys.exit(0)
                tmp = data["items"][0]["volumeInfo"]
                return BookData(
                    title=tmp["title"],
                    isbn=tmp["industryIdentifiers"][0]["identifier"],
                    description=tmp["description"],
                    published_date=tmp["publishedDate"],
                    authors=tmp["authors"],
                )
    return None
