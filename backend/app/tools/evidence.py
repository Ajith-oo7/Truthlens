from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.models.schemas import EvidenceItem
from app.services.corpus import SEED_DOCUMENTS
from app.tools.credibility import evaluate_source

logger = logging.getLogger("truthlens.evidence")


def search_web(query: str) -> list[EvidenceItem]:
    settings = get_settings()
    items: list[EvidenceItem] = []
    try:
        if settings.tavily_api_key:
            resp = httpx.post(
                "https://api.tavily.com/search",
                json={"api_key": settings.tavily_api_key, "query": query, "max_results": 6},
                timeout=12.0,
            )
            resp.raise_for_status()
            for idx, hit in enumerate(resp.json().get("results", []), start=1):
                items.append(_from_web(idx, hit.get("url", ""), hit.get("title", ""), hit.get("content", ""), hit))
        elif settings.serpapi_api_key:
            resp = httpx.get(
                "https://serpapi.com/search.json",
                params={"q": query, "api_key": settings.serpapi_api_key, "engine": "google"},
                timeout=12.0,
            )
            resp.raise_for_status()
            for idx, hit in enumerate(resp.json().get("organic_results", [])[:6], start=1):
                items.append(_from_web(idx, hit.get("link", ""), hit.get("title", ""), hit.get("snippet", ""), hit))
        elif settings.google_cse_id and settings.google_cse_api_key:
            resp = httpx.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"q": query, "cx": settings.google_cse_id, "key": settings.google_cse_api_key},
                timeout=12.0,
            )
            resp.raise_for_status()
            for idx, hit in enumerate(resp.json().get("items", [])[:6], start=1):
                items.append(
                    _from_web(idx, hit.get("link", ""), hit.get("title", ""), hit.get("snippet", ""), hit)
                )
    except Exception as exc:
        logger.warning("Web search unavailable: %s", exc)

    # No live search key: do not pretend the apple seed pack is "the web".
    return items


def search_articles(query: str) -> list[EvidenceItem]:
    return [item.model_copy(update={"store": "article", "id": item.id.replace("WEB", "ART")}) for item in search_web(query)]


def retrieve_sources(urls: list[str]) -> list[dict[str, Any]]:
    found = []
    by_url = {doc["url"]: doc for doc in SEED_DOCUMENTS}
    for url in urls:
        if url in by_url:
            found.append(by_url[url])
        else:
            cred = evaluate_source(url)
            found.append({"url": url, "domain": cred.domain, "tier": cred.tier.value, "score": cred.score})
    return found


def _from_web(idx: int, url: str, title: str, text: str, raw: dict[str, Any]) -> EvidenceItem:
    cred = evaluate_source(url)
    return EvidenceItem(
        id=f"WEB-{idx:03d}",
        text=text,
        url=url,
        source_id=cred.source_id,
        store="web",
        score=0.55,
        title=title,
        domain=cred.domain or urlparse(url).netloc,
        stance="neutral",
        raw=raw,
    )
