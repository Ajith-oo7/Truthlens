from __future__ import annotations

from app.models.schemas import EvidenceItem, EvidencePackage, ExtractedClaim
from app.retrieval.hybrid import hybrid_search
from app.services.corpus import is_relevant_text
from app.tools.evidence import search_web
from app.tools.factcheck import search_fact_checks
from app.tools.stance import assign_stances


def _on_topic(query: str, item: EvidenceItem) -> bool:
    return is_relevant_text(query, item.title, item.text, item.domain)


def run_evidence_retrieval(claim: ExtractedClaim) -> tuple[EvidencePackage, dict[str, list[EvidenceItem]]]:
    query = claim.claim
    fact_hits = [item for item in search_fact_checks(query) if _on_topic(query, item)]
    web_hits = [item for item in search_web(query) if _on_topic(query, item)]
    fused, layers = hybrid_search(query)
    fused = [item for item in fused if _on_topic(query, item)]
    combined = fact_hits + web_hits + fused
    dedup: dict[str, EvidenceItem] = {}
    for item in combined:
        key = item.url or item.text[:80]
        if key not in dedup or item.score > dedup[key].score:
            dedup[key] = item
    ranked = sorted(dedup.values(), key=lambda i: i.score, reverse=True)
    normalized = [item.model_copy(update={"id": f"E-{idx:03d}"}) for idx, item in enumerate(ranked, start=1)]
    normalized = assign_stances(query, normalized)
    layers["factcheck"] = fact_hits
    layers["web"] = web_hits
    layers["fused"] = fused
    return EvidencePackage(items=normalized), layers
