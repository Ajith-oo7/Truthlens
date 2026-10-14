from __future__ import annotations

import logging

from app.config import get_settings
from app.models.schemas import EvidenceItem
from app.retrieval.memory_index import search_seed
from app.services.corpus import SEED_DOCUMENTS
from app.tools.credibility import evaluate_source

logger = logging.getLogger("truthlens.es")
INDEX = "truthlens_articles"


def _client():
    settings = get_settings()
    if not settings.elasticsearch_enabled:
        return None
    try:
        from elasticsearch import Elasticsearch

        kwargs: dict = {"hosts": [settings.elasticsearch_url], "request_timeout": 3}
        if settings.elasticsearch_api_key:
            kwargs["api_key"] = settings.elasticsearch_api_key
        client = Elasticsearch(**kwargs)
        if not client.ping():
            return None
        if not client.indices.exists(index=INDEX):
            client.indices.create(index=INDEX)
            for doc in SEED_DOCUMENTS:
                client.index(index=INDEX, id=doc["id"], document=doc, refresh=True)
        return client
    except Exception as exc:
        logger.warning("Elasticsearch unavailable: %s", exc)
        return None


def search_elasticsearch(query: str, limit: int = 5) -> list[EvidenceItem]:
    client = _client()
    if client is None:
        return search_seed(query, "elasticsearch", "ES", limit)
    try:
        result = client.search(
            index=INDEX,
            query={"multi_match": {"query": query, "fields": ["title^2", "body", "topic"]}},
            size=limit,
        )
        items: list[EvidenceItem] = []
        for idx, hit in enumerate(result.get("hits", {}).get("hits", []), start=1):
            src = hit.get("_source", {})
            cred = evaluate_source(src.get("url", ""), src.get("domain"))
            items.append(
                EvidenceItem(
                    id=f"ES-{idx:03d}",
                    text=src.get("body", ""),
                    url=src.get("url", ""),
                    source_id=cred.source_id,
                    store="elasticsearch",
                    score=round(float(hit.get("_score") or 0) / 10.0, 4),
                    title=src.get("title", ""),
                    domain=src.get("domain", ""),
                    stance=src.get("stance", "neutral"),
                    raw=src,
                )
            )
        return items
    except Exception as exc:
        logger.warning("Elasticsearch search failed: %s", exc)
        return search_seed(query, "elasticsearch", "ES", limit)
