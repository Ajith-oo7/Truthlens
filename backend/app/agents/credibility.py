from app.models.schemas import CredibilityScore, EvidenceItem
from app.tools.credibility import evaluate_source


def run_credibility(evidence: list[EvidenceItem]) -> list[CredibilityScore]:
    seen: set[str] = set()
    scores: list[CredibilityScore] = []
    for item in evidence:
        key = item.url or item.domain
        if key in seen:
            continue
        seen.add(key)
        scores.append(evaluate_source(item.url, item.domain, item.title))
    return scores
