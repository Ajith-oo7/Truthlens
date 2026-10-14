from __future__ import annotations

import re

from app.models.schemas import EvidenceItem
from app.services.corpus import _words, claim_tokens
from app.services.llm import llm

LOCATION_CLAIM = re.compile(
    r"\b(is in|is located in|located in|capital of|based in|lives in|headquartered in)\b",
    re.I,
)
REFUTE_CUES = (
    "never sold",
    "not located",
    "is not in",
    "isn't in",
    "debunked",
    "false claim",
    "no evidence",
    "pants on fire",
    "mostly false",
    "fact check: false",
    "rated false",
)
WEAK_GENERIC = {
    "sells",
    "sold",
    "sale",
    "shop",
    "store",
    "product",
    "products",
    "company",
    "brand",
    "also",
    "beauty",
    "online",
    "official",
}


def assign_stances(claim: str, items: list[EvidenceItem]) -> list[EvidenceItem]:
    labeled = [heuristic_label(claim, item) for item in items]
    if any(item.stance == "neutral" for item in labeled):
        labeled = _overlay_llm(claim, labeled)
    return labeled


def heuristic_label(claim: str, item: EvidenceItem) -> EvidenceItem:
    if item.stance in {"supports", "refutes"}:
        return item
    rating = _rating_stance(item)
    if rating:
        return item.model_copy(update={"stance": rating})
    blob = f"{item.title} {item.text}".lower()
    if any(cue in blob for cue in REFUTE_CUES):
        return item.model_copy(update={"stance": "refutes"})
    if LOCATION_CLAIM.search(claim):
        return item.model_copy(update={"stance": _location_stance(claim, blob)})
    core = {tok for tok in claim_tokens(claim) if tok not in WEAK_GENERIC}
    if not core:
        core = claim_tokens(claim)
    overlap = core & _words(blob)
    official = _entity_in_domain(claim, item.domain)
    # Official sites that mention the claim's distinctive terms corroborate catalog/company facts.
    # Generic token overlap (e.g. "Christmas") is not enough — that path stays fail-closed.
    if official and overlap:
        return item.model_copy(update={"stance": "supports"})
    return item


def _rating_stance(item: EvidenceItem) -> str | None:
    review = item.raw.get("claimReview") if isinstance(item.raw, dict) else None
    rating = ""
    if isinstance(review, list) and review:
        rating = str(review[0].get("textualRating") or "")
    rating = (rating or item.text or "").lower()
    if not rating:
        return None
    if any(tag in rating for tag in ("pants on fire", "false", "incorrect", "fake")):
        return "refutes"
    if rating.strip() in {"true", "mostly true", "correct", "accurate"}:
        return "supports"
    return None


def _location_stance(claim: str, blob: str) -> str:
    tokens = [tok for tok in claim_tokens(claim) if tok not in {"located"}]
    if len(tokens) < 2:
        return "neutral"
    place = tokens[-1]
    subject = " ".join(tokens[:-1])
    if subject and place and f"{subject} is in {place}" in blob:
        return "supports"
    rival = re.search(rf"{re.escape(subject)} is in ([a-z]+)", blob)
    if rival and rival.group(1) != place:
        return "refutes"
    return "neutral"


def _entity_in_domain(claim: str, domain: str) -> bool:
    host = (domain or "").lower().removeprefix("www.")
    return any(tok in host for tok in claim_tokens(claim) if len(tok) >= 4)


def _overlay_llm(claim: str, items: list[EvidenceItem]) -> list[EvidenceItem]:
    payload = [
        {"id": item.id, "title": item.title, "text": item.text[:400], "url": item.url, "stance": item.stance}
        for item in items
    ]
    parsed = llm.generate_json(
        "Label each source supports, refutes, or neutral toward the claim. Use only the given text.",
        f"CLAIM={claim}\nSOURCES={payload}\nReturn JSON {{labels:[{{id,stance}}]}}",
        {"labels": [{"id": item.id, "stance": item.stance} for item in items]},
    )
    by_id = {
        row.get("id"): row.get("stance")
        for row in parsed.get("labels", [])
        if row.get("stance") in {"supports", "refutes", "neutral"}
    }
    out: list[EvidenceItem] = []
    for item in items:
        stance = by_id.get(item.id, item.stance)
        if item.stance != "neutral":
            stance = item.stance
        out.append(item.model_copy(update={"stance": stance}))
    return out
