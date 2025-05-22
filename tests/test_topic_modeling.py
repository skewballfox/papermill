

"""
    Script to run a quick BERTopic test on parsed BibTeX data
        1. (currently in test_bibtex_parser.py) Parse a Zotero Better BibTeX export (`.bib`) into a cleaned JSONL corpus ready for BERTopic.
            No personal IDs, authors, or dates are preserved - only *title*, *venue*, *abstract*, and *keywords*.
        2. Run a BERTopic test on that corpus, clustering the documents and writing a human-readable topic report.
"""

import argparse
import json
import pathlib
import re
from numpy import ndarray
from collections import defaultdict
from pprint import pprint
from typing import Dict, Iterable, List, Tuple


KW_REPEAT_RE = re.compile(r"\b(\w+)( \1\b)+")


def refine_keywords(keywords: List[Tuple[str, float]], min_score: float = 0.1) -> Dict[str, float]:
    """ Refines (keyword, weight) pairs: drops low scores & redundant phrases """
    seen_tokens: set[str] = set()
    refined: Dict[str, float] = {}
    for kw, score in sorted(keywords, key=lambda x: -x[1]):
        if score < min_score:
            continue
        normalized = KW_REPEAT_RE.sub(r"\1", kw.lower())
        tokens = frozenset(normalized.split())
        if tokens & seen_tokens == tokens:  # completely covered → skip
            continue
        refined[normalized] = round(float(score), 4)
        seen_tokens.update(tokens)
    return refined


def _build_doc(rec: Dict[str, str | List[str]]) -> str:
    # TODO: need to handle failures for other document types that may not have an "abstract" field
    parts: List[str] = [rec.get("title", ""), rec.get("abstract", "")]
    if kw := rec.get("keywords"):
        kw_str = " ".join(kw) if isinstance(kw, list) else str(kw)
        parts.append(kw_str)
    if rec.get("venue"):
        parts.append(str(rec["venue"]))
    return " ".join(parts)


# def create_vectorizer(corpus: Iterable[str], min_df: float = 2):
def create_vectorizer(min_df: float = 2):
    """ Create a vectorizer for the corpus, returning the vocabulary and reverse mapping """
    from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
    DOMAIN_STOPWORDS = {
        # generic academic filler
        "approach", "based", "using", "method", "methods", "novel", "study",
        "results", "paper", "proposed", "effect", "effects",
        "et", "al", "fig", "table" # possible numeric & LaTeX leftovers
    }
    custom_stopwords = list(ENGLISH_STOP_WORDS.union(DOMAIN_STOPWORDS))
    return CountVectorizer(
        stop_words=custom_stopwords,
        min_df=min_df,
        ngram_range = (1, 3),
        token_pattern = r"(?u)\b[a-zA-Z]{3,}\b"      # only 3+ letter alphabetic tokens
    )
    # NOTE: not sure if the vectorizer should be fit on the corpus before being input to the transformer
    # X = vectorizer.fit_transform(corpus)
    # vocab = vectorizer.vocabulary_
    # reverse_vocab = {v: k for k, v in vocab.items()}
    # return vocab, reverse_vocab


def _generate_report(
    clusters: Dict[int, List[int]],
    topic_kw: Dict[int, Dict[str, float]],
    docs_raw: List[Dict[str, str]],
    probabilities: List[ndarray] = None,
) -> List[Dict]:
    """ Generate a human-readable report of the topics and their keywords """
    report = []
    # Sort topics by cluster size (largest first)
    for tid, idxs in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        if tid == -1:  # skip outliers
            continue
        report.append({
            "topic_id": tid,
            "size": len(idxs),
            "keywords": topic_kw.get(tid, {}),
            "doc_titles": [docs_raw[i].get("title", "") for i in idxs],
            "probabilities": [round(float(probabilities[i].max()), 4) for i in idxs] if probabilities is not None else [],
        })
    return report


def _debug_topic_lists(topics_dict: Dict[int, List[Tuple[str, ndarray]]], topic_kws: Dict[int, Dict[str, float]]):
    """ Debugging function to print topic keywords and their weights """
    output_topics = {k: vi[0] for k, v in topics_dict.items() for vi in v}
    pprint(f"Topics dict (before refinement): {output_topics}", indent=2)
    pprint(f"Topic keywords (after refinement): {topic_kws}", indent=2)


def run_bertopic(docs_raw: List[Dict[str, str]], min_kw: float = 0.02):
    """ Fit BERTopic on `corpus_path` and dump a JSON report (or print) """
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    # append all fields' text to a single string for each document
    docs = [_build_doc(rec) for rec in docs_raw]
    topic_model = BERTopic(
        min_topic_size=5,
        embedding_model=SentenceTransformer("allenai-specter"), #"all-mpnet-base-v2"),  #"allenai-specter"), # "allenai/specter2"
        vectorizer_model=create_vectorizer(),
        #nr_topics='auto',
        calculate_probabilities=True,
        n_gram_range=(1, 3),
        verbose=True
    )
    topics, probabilities = topic_model.fit_transform(docs)
    # map cluster members to their topic IDs
    clusters: Dict[int, List[int]] = defaultdict(list)
    for idx, tid in enumerate(topics):
        clusters[tid].append(idx)
    # gather topic keywords and refine them
    topics_dict = topic_model.get_topics()
    # refine keywords for each topic ID while dropping outliers (-1) (BERTopic's default ID for outliers)
    topic_kw = {tid: refine_keywords(kws, min_kw) for tid, kws in topics_dict.items() if tid != -1}
    return _generate_report(clusters, topic_kw, docs_raw, probabilities)





def _cli_bertopic(args: argparse.Namespace):
    docs_raw = [json.loads(l) for l in pathlib.Path(args.corpus).read_text(encoding="utf-8").splitlines()]
    print(f"Loaded {len(docs_raw)} documents from {args.corpus}")
    report = run_bertopic(docs_raw, args.min_kw)
    if args.out:
        pathlib.Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Topic report saved to {args.out}")
    else:
        print(json.dumps(report, indent=2))


def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Parse BibTeX & run BERTopic test.")
    sub = parser.add_subparsers(required=True)
    # might add this back later
    # p_parse = sub.add_parser("parse", help="Convert .bib -> cleaned corpus.jsonl")
    # --- bertopic sub‑command ---
    p_bt = sub.add_parser("bertopic", help="Run BERTopic on an existing corpus.jsonl")
    p_bt.add_argument("corpus", help="Path to corpus.jsonl produced by 'parse'")
    p_bt.add_argument("--out", default="clusters.json", help="Output JSON report path")
    p_bt.add_argument("--min-kw", type=float, default=0.02, help="Minimum keyword weight")
    p_bt.set_defaults(func=_cli_bertopic)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__": # pragma: no cover
    main()
