from __future__ import annotations

import logging

from app.config import get_settings
from app.models.schemas import EvidenceItem
from app.retrieval.memory_index import search_seed
from app.services.corpus import SEED_DOCUMENTS
from app.tools.credibility import evaluate_source

logger = logging.getLogger("truthlens.chroma")
_COLLECTION = None


def _collection():
    global _COLLECTION
    if _COLLECTION is not None:
        return _COLLECTION
    settings = get_settings()
    if not settings.chroma_enabled and not settings.chroma_host:
        return None
    try:
        import chromadb

        if settings.chroma_host:
            client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        else:
            client = chromadb.PersistentClient(path=settings.chroma_path)
        col = client.get_or_create_collection("trusted_corpus")
        if col.count() == 0:
            col.add(
                ids=[d["id"] for d in SEED_DOCUMENTS],
                documents=[f"{d['title']}. {d['body']}" for d in SEED_DOCUMENTS],
                metadatas=[{k: d[k] for k in ("url", "domain", "tier", "topic", "stance")} for d in SEED_DOCUMENTS],
            )
        _COLLECTION = col
        return col
    except Exception as exc:
        logger.warning("Chroma unavailable: %s", exc)
        return None


def search_chromadb(query: str, limit: int = 5) -> list[EvidenceItem]:
    col = _collection()
    if col is None:
        return search_seed(query, "chroma", "CH", limit)
    try:
        result = col.query(query_texts=[query], n_results=limit)
        items: list[EvidenceItem] = []
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        for idx, (doc, meta, dist) in enumerate(zip(docs, metas, dists), start=1):
            url = (meta or {}).get("url", "")
            cred = evaluate_source(url, (meta or {}).get("domain"))
            items.append(
                EvidenceItem(
                    id=f"CH-{idx:03d}",
                    text=doc,
                    url=url,
                    source_id=cred.source_id,
                    store="chroma",
                    score=round(1 / (1 + float(dist or 1)), 4),
                    title=url,
                    domain=cred.domain,
                    stance=(meta or {}).get("stance", "neutral"),
                    raw=meta or {},
                )
            )
        return items
    except Exception as exc:
        logger.warning("Chroma query failed: %s", exc)
        return search_seed(query, "chroma", "CH", limit)
