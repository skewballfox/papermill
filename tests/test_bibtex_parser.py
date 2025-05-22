

"""
- Parse a Better BibTeX-formatted .bib file exported from Zotero and prepare a clean corpus ready for BERTopic.
- The script removes LaTeX commands, excessive braces, in text numeric citations, math expressions, and normalizes keywords.
- Each line of the JSONL output contains:
    {
        "id": "<BibTeX citekey>",
        "title": "<cleaned title>",
        "venue": "<journal/booktitle/publisher/etc.>",
        "abstract": "<cleaned abstract>",
        "keywords": ["keyword one", "keyword two", ...]
    }
"""

import argparse
import json
import re
import sys
from pathlib import Path
import bibtexparser


# ---------------------------- Regex helpers -----------------------------
BRACE_RE = re.compile(r"[{}]")                                                          # strip braces entirely
MATH_RE = re.compile(r"\$[^$]*\$")                                                      # remove inline $…$ maths
LATEX_CMD_RE = re.compile(r"\\[A-Za-z]+(?:\[[^]]*])?(?:\{[^}]*})?")                     # \texttimes{×}, etc.
CITATION_RE = re.compile(r"\[[0-9,;\s]+]|\\cite[t]?(?:\[[^]]*])?\{[^}]*}\s*", re.X)     # [1] or \cite{…}
WS_RE = re.compile(r"\s+")                                                              # compress whitespace

ESCAPED_CHARS = {"\\&": "&", "\\%": "%", "\\_": "_", "\\#": "#"}

# priority order for the publication "venue"
VENUE_FIELDS = [
    "journal",
    "booktitle",
    "publisher",
    "archiveprefix",
    "series",
    "organization",
]

# ---------------------------- Cleaning utils ----------------------------

def clean_text(text: str) -> str:
    """ Remove LaTeX, braces, citations, and tidy whitespace """
    if not text:
        return ""
    text = BRACE_RE.sub("", text)
    text = MATH_RE.sub(" ", text)
    text = LATEX_CMD_RE.sub(" ", text)
    text = CITATION_RE.sub(" ", text)
    for k, v in ESCAPED_CHARS.items():
        text = text.replace(k, v)
    text = WS_RE.sub(" ", text)
    return text.strip()


def split_keywords(raw: str):
    """ split & normalize keyword strings to a sorted list of unique keywords """
    if not raw:
        return []
    raw = raw.replace("_", " ")
    # split on common delimiters
    parts = re.split(r"[;,/]|\\n", raw)
    clean_set = {WS_RE.sub(" ", p.lower()).strip() for p in parts if p.strip()}
    return sorted(clean_set)


# ----------------------------- Core parser ------------------------------

def record_from_entry(entry: dict) -> dict:
    """ convert raw bibtexparser entry to a cleaned record """
    rec = {
        "id": entry.get("ID") or entry.get("key"),
        "title": clean_text(entry.get("title", "")),
        "abstract": clean_text(entry.get("abstract", "")),
        "venue": "",
        "keywords": split_keywords(entry.get("keywords", "")),
    }
    for f in VENUE_FIELDS:
        if entry.get(f):
            rec["venue"] = clean_text(entry[f])
            break
    return rec


def parse_bib(path: Path):
    """ parse .bib file and return a list of cleaned records """
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    with path.open(encoding="utf-8") as fh:
        bib_db = bibtexparser.load(fh, parser=parser)
    # TODO: add duplicate removal
    return [record_from_entry(e) for e in bib_db.entries]


# ------------------------------ CLI entry -------------------------------

def main():
    ap = argparse.ArgumentParser(description="Convert a .bib file to BERTopic-ready JSONL corpus")
    ap.add_argument("bibfile", type=Path, help="Input Better BibTeX file")
    ap.add_argument("--out", type=Path, default=Path(r"tests/corpus.jsonl"), help="Destination JSONL file")
    args = ap.parse_args()
    records = parse_bib(args.bibfile)
    try:
        with args.out.open("w", encoding="utf-8") as f:
            for r in records:
                json.dump(r, f, ensure_ascii=False)
                f.write("\n")
        print(f"SUCCESS - Wrote {len(records)} records to {args.out}")
    except OSError as e:
        print(f"ERROR - Failed to write to {args.out}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
