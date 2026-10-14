from __future__ import annotations

from collections import defaultdict

from app.models.schemas import EvidenceItem
from app.retrieval.chroma_store import search_chromadb
from app.retrieval.elastic_store import search_elasticsearch
from app.retrieval.qdrant_store import search_qdrant
from app.tools.credibility import evaluate_source


def reciprocal_rank_fusion(groups: list[list[EvidenceItem]], k: int = 60) -> list[EvidenceItem]:
    scores: dict[str, float] = defaultdict(float)
    best: dict[str, EvidenceItem] = {}
    for group in groups:
        for rank, item in enumerate(group, start=1):
            key = item.url or item.text[:80]
            scores[key] += 1.0 / (k + rank)
            if key not in best or item.score > best[key].score:
                best[key] = item
    fused: list[EvidenceItem] = []
    for idx, (key, rrf) in enumerate(sorted(scores.items(), key=lambda kv: kv[1], reverse=True), start=1):
        item = best[key]
        cred = evaluate_source(item.url, item.domain)
        fused.append(
            item.model_copy(
                update={
                    "id": f"E-{idx:03d}",
                    "score": round(rrf * (cred.score / 100.0), 4),
                    "source_id": cred.source_id,
                    "domain": cred.domain or item.domain,
                }
            )
        )
    return fused


def hybrid_search(query: str) -> tuple[list[EvidenceItem], dict[str, list[EvidenceItem]]]:
    chroma = search_chromadb(query)
    qdrant = search_qdrant(query)
    elastic = search_elasticsearch(query)
    fused = reciprocal_rank_fusion([chroma, qdrant, elastic])
    return fused, {"chroma": chroma, "qdrant": qdrant, "elasticsearch": elastic}
