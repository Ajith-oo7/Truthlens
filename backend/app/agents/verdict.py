from __future__ import annotations

from app.config import get_settings
from app.models.schemas import (
    CredibilityScore,
    EvidenceItem,
    ExtractedClaim,
    ReasoningStep,
    SourceRef,
    VerdictLabel,
    VerdictResult,
)
from app.safety.gate import SafetyGate
from app.services.llm import llm


def run_verdict(
    claim: ExtractedClaim,
    evidence: list[EvidenceItem],
    scores: list[CredibilityScore],
    reasoning: list[ReasoningStep],
    extra_uncertainty: bool = False,
) -> VerdictResult:
    settings = get_settings()
    ledger_urls = {item.url for item in evidence if item.url}
    sources = [
        SourceRef(
            id=score.source_id,
            title=next((e.title for e in evidence if e.domain == score.domain), score.domain),
            url=score.url,
            domain=score.domain,
            tier=score.tier,
            score=score.score,
        )
        for score in scores
        if score.url in ledger_urls or not ledger_urls
    ]

    support = sum(s.score for e, s in _pairs(evidence, scores) if e.stance == "supports")
    refute = sum(s.score for e, s in _pairs(evidence, scores) if e.stance == "refutes")
    total = support + refute
    confidence = 0.5
    label = VerdictLabel.UNVERIFIABLE
    reason = None
    if total > 0:
        delta = (refute - support) / total
        confidence = min(0.96, 0.5 + abs(delta) / 2 + min(len(evidence), 6) * 0.03)
        if refute > support * 1.4:
            label = VerdictLabel.FALSE
        elif support > refute * 1.4:
            label = VerdictLabel.TRUE
        elif abs(delta) < 0.25:
            label = VerdictLabel.PARTIALLY_TRUE if min(support, refute) > 0 else VerdictLabel.MISLEADING
        else:
            label = VerdictLabel.MISLEADING

    forced = SafetyGate().force_unverifiable(
        len(evidence), settings.min_evidence_count, confidence, settings.confidence_inconclusive_band
    )
    if forced or extra_uncertainty and len(evidence) < settings.min_evidence_count + 1:
        label = VerdictLabel.UNVERIFIABLE
        reason = forced or "Sensitive domain with insufficient high-tier evidence."
        confidence = min(confidence, 0.42)

    fallback = VerdictResult(
        verdict=label,
        confidence=round(confidence, 3),
        explanation=_explain(claim, label, evidence),
        sources=sources,
        evidence_ids=[e.id for e in evidence],
        unverifiable_reason=reason,
        reasoning=reasoning,
    )
    parsed = llm.generate_json(
        "Issue a grounded verdict using only provided evidence IDs and URLs. "
        "If on-topic sources support the claim, return TRUE. If they contradict it, return FALSE. "
        "UNVERIFIABLE only when the ledger does not actually address the claim.",
        f"CLAIM={claim.claim} EVIDENCE={[e.model_dump() for e in evidence]} SCORES={[s.model_dump() for s in scores]} "
        f"REASONING={[s.model_dump() for s in reasoning]} SUGGESTED={fallback.model_dump()}",
        fallback.model_dump(),
    )
    try:
        result = VerdictResult.model_validate({**fallback.model_dump(), **parsed, "reasoning": reasoning, "sources": sources})
    except Exception:
        result = fallback

    if (
        result.verdict == VerdictLabel.UNVERIFIABLE
        and fallback.verdict != VerdictLabel.UNVERIFIABLE
        and len(evidence) >= settings.min_evidence_count
    ):
        result = fallback

    if any(src.url and src.url not in ledger_urls for src in result.sources) and ledger_urls:
        result.sources = sources
    if result.verdict != VerdictLabel.UNVERIFIABLE and len(evidence) < settings.min_evidence_count:
        result.verdict = VerdictLabel.UNVERIFIABLE
        result.unverifiable_reason = "Insufficient evidence; refusing to speculate."
        result.confidence = min(result.confidence, 0.4)
    return result


def _pairs(evidence: list[EvidenceItem], scores: list[CredibilityScore]):
    by_domain = {s.domain: s for s in scores}
    for item in evidence:
        yield item, by_domain.get(item.domain, CredibilityScore(source_id=item.id, score=20))


def _explain(claim: ExtractedClaim, label: VerdictLabel, evidence: list[EvidenceItem]) -> str:
    if label == VerdictLabel.UNVERIFIABLE:
        return f"The claim “{claim.claim}” cannot be verified from the current citation ledger."
    heads = "; ".join(e.title or e.id for e in evidence[:3])
    return f"Verdict {label.value} for “{claim.claim}” based on ledger sources: {heads}."
