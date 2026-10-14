"""Seed local retrieval stores from the trusted corpus."""

from __future__ import annotations

from app.retrieval.chroma_store import search_chromadb
from app.retrieval.elastic_store import search_elasticsearch
from app.retrieval.qdrant_store import search_qdrant


def main() -> None:
    query = "Apples ripen in 2 days"
    print("chroma", len(search_chromadb(query)))
    print("qdrant", len(search_qdrant(query)))
    print("elasticsearch", len(search_elasticsearch(query)))


if __name__ == "__main__":
    main()
