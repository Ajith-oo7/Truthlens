from __future__ import annotations

from app.models.schemas import EvidenceItem
from app.services.corpus import SEED_DOCUMENTS, lexical_score
from app.tools.credibility import evaluate_source


def search_seed(query: str, store: str, prefix: str, limit: int = 5) -> list[EvidenceItem]:
    ranked = sorted(((lexical_score(query, doc), doc) for doc in SEED_DOCUMENTS), key=lambda x: x[0], reverse=True)
    items: list[EvidenceItem] = []
    for score, doc in ranked[:limit]:
        if score < 0.25:
            continue
        cred = evaluate_source(doc["url"], doc["domain"])
        items.append(
            EvidenceItem(
                id=f"{prefix}-{len(items)+1:03d}",
                text=doc["body"],
                url=doc["url"],
                source_id=cred.source_id,
                store=store,
                score=round(score, 4),
                title=doc["title"],
                domain=doc["domain"],
                stance=doc["stance"],
                raw=doc,
            )
        )
    return items
