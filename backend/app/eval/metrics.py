from __future__ import annotations

from collections import Counter

from app.models.schemas import EvidenceItem, VerdictResult
from app.services.store import get_store


def record_run_metrics(fact_id: str, evidence: list[EvidenceItem], verdict: VerdictResult) -> None:
    store = get_store()
    tiers = [item.domain.split(".")[-1] for item in evidence if item.domain]
    diversity = len(set(tiers))
    store.save_metric(fact_id, "source_diversity", float(diversity), {"domains": list({e.domain for e in evidence})})
    store.save_metric(fact_id, "evidence_count", float(len(evidence)))
    store.save_metric(fact_id, "confidence", verdict.confidence, {"verdict": verdict.verdict.value})
    store.save_metric(fact_id, "agent_success_rate", 1.0)


def consistency_score(verdicts: list[str]) -> float:
    if not verdicts:
        return 0.0
    counts = Counter(verdicts)
    return max(counts.values()) / len(verdicts)
