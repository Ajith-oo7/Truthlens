from __future__ import annotations

from app.models.schemas import CredibilityScore, EvidenceItem, ExtractedClaim, KnowledgeGraphContext, ReasoningStep
from app.services.llm import llm


def run_reasoning(
    claim: ExtractedClaim,
    evidence: list[EvidenceItem],
    graph: KnowledgeGraphContext,
    scores: list[CredibilityScore],
) -> list[ReasoningStep]:
    ledger_ids = {item.id for item in evidence}
    fallback = _fallback_steps(claim, evidence, graph, scores)
    parsed = llm.generate_json(
        "Reason only over provided evidence IDs. Do not invent sources or IDs.",
        (
            f"CLAIM: {claim.claim}\nEVIDENCE: {[item.model_dump() for item in evidence]}\n"
            f"GRAPH supporting={graph.supporting} contradicting={graph.contradicting}\n"
            f"SCORES: {[s.model_dump() for s in scores]}\n"
            "Return JSON {steps:[{index,title,detail,evidence_ids}]}"
        ),
        {"steps": [s.model_dump() for s in fallback]},
    )
    steps: list[ReasoningStep] = []
    for raw in parsed.get("steps", []):
        ids = [eid for eid in raw.get("evidence_ids", []) if eid in ledger_ids]
        if not ids and evidence:
            ids = [evidence[0].id]
        steps.append(
            ReasoningStep(
                index=int(raw.get("index", len(steps) + 1)),
                title=raw.get("title", "Step"),
                detail=raw.get("detail", ""),
                evidence_ids=ids,
            )
        )
    return steps or fallback


def _fallback_steps(
    claim: ExtractedClaim,
    evidence: list[EvidenceItem],
    graph: KnowledgeGraphContext,
    scores: list[CredibilityScore],
) -> list[ReasoningStep]:
    refute = [e for e in evidence if e.stance == "refutes"]
    support = [e for e in evidence if e.stance == "supports"]
    high = [s for s in scores if s.score >= 75]
    return [
        ReasoningStep(
            index=1,
            title="Normalize the checkable proposition",
            detail=f"The extracted claim is: {claim.claim}",
            evidence_ids=[evidence[0].id] if evidence else [],
        ),
        ReasoningStep(
            index=2,
            title="Weigh high-credibility sources",
            detail=f"{len(high)} sources score 75+ (government/university/journal/major news).",
            evidence_ids=[e.id for e in evidence[:3]],
        ),
        ReasoningStep(
            index=3,
            title="Compare supporting vs refuting neighbors",
            detail=(
                f"Graph supporting={len(graph.supporting)} contradicting={len(graph.contradicting)}. "
                f"Ledger refute={len(refute)} support={len(support)}."
            ),
            evidence_ids=[e.id for e in (refute[:3] or support[:3])],
        ),
    ]
