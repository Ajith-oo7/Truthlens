from __future__ import annotations

import hashlib
import logging

from app.config import get_settings
from app.models.schemas import EvidenceItem
from app.retrieval.memory_index import search_seed
from app.services.corpus import SEED_DOCUMENTS
from app.tools.credibility import evaluate_source

logger = logging.getLogger("truthlens.qdrant")
COLLECTION = "trusted_corpus"


def _embed(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [((digest[i % len(digest)] / 255.0) * 2 - 1) for i in range(64)]
    return values


def _client():
    settings = get_settings()
    if not settings.qdrant_enabled:
        return None
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, PointStruct, VectorParams

        client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None, timeout=3)
        existing = [c.name for c in client.get_collections().collections]
        if COLLECTION not in existing:
            client.create_collection(COLLECTION, vectors_config=VectorParams(size=64, distance=Distance.COSINE))
            client.upsert(
                COLLECTION,
                points=[
                    PointStruct(id=idx, vector=_embed(f"{d['title']} {d['body']}"), payload=d)
                    for idx, d in enumerate(SEED_DOCUMENTS, start=1)
                ],
            )
        return client
    except Exception as exc:
        logger.warning("Qdrant unavailable: %s", exc)
        return None


def search_qdrant(query: str, limit: int = 5) -> list[EvidenceItem]:
    client = _client()
    if client is None:
        return search_seed(query, "qdrant", "QD", limit)
    try:
        hits = client.search(COLLECTION, query_vector=_embed(query), limit=limit)
        items: list[EvidenceItem] = []
        for idx, hit in enumerate(hits, start=1):
            payload = hit.payload or {}
            cred = evaluate_source(payload.get("url", ""), payload.get("domain"))
            items.append(
                EvidenceItem(
                    id=f"QD-{idx:03d}",
                    text=payload.get("body", ""),
                    url=payload.get("url", ""),
                    source_id=cred.source_id,
                    store="qdrant",
                    score=round(float(hit.score or 0), 4),
                    title=payload.get("title", ""),
                    domain=payload.get("domain", ""),
                    stance=payload.get("stance", "neutral"),
                    raw=payload,
                )
            )
        return items
    except Exception as exc:
        logger.warning("Qdrant search failed: %s", exc)
        return search_seed(query, "qdrant", "QD", limit)
