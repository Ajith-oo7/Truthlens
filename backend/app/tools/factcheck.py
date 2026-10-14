from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings
from app.models.schemas import EvidenceItem
from app.services.corpus import SEED_DOCUMENTS
from app.tools.credibility import evaluate_source

logger = logging.getLogger("truthlens.factcheck")


def search_fact_checks(query: str, language: str = "en") -> list[EvidenceItem]:
    settings = get_settings()
    items: list[EvidenceItem] = []
    if settings.google_factcheck_api_key:
        try:
            resp = httpx.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={"query": query, "languageCode": language, "key": settings.google_factcheck_api_key},
                timeout=12.0,
            )
            resp.raise_for_status()
            for idx, claim in enumerate(resp.json().get("claims", [])[:8], start=1):
                review = (claim.get("claimReview") or [{}])[0]
                url = review.get("url") or ""
                cred = evaluate_source(url)
                items.append(
                    EvidenceItem(
                        id=f"FC-{idx:03d}",
                        text=review.get("textualRating") or claim.get("text") or "",
                        url=url,
                        source_id=cred.source_id,
                        store="factcheck",
                        score=0.7,
                        title=review.get("title") or claim.get("text", ""),
                        domain=cred.domain,
                        stance="neutral",
                        raw=claim,
                    )
                )
        except Exception as exc:
            logger.warning("Fact Check Tools API unavailable: %s", exc)

    # No Fact Check API key: do not substitute the apple seed pack as a fact-check hit.
    return items


def retrieve_fact_check(fact_id: str) -> dict[str, Any] | None:
    for doc in SEED_DOCUMENTS:
        if doc["id"] == fact_id:
            return doc
    return None
