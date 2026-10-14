from __future__ import annotations

from app.models.schemas import ClaimCategory, Entity, ExtractedClaim
from app.services.llm import llm


def _heuristic(text: str, input_type: str) -> ExtractedClaim:
    lowered = text.lower()
    category = ClaimCategory.SCREENSHOT if input_type == "image" else ClaimCategory.NEWS
    if any(w in lowered for w in ("apple", "ripen", "vaccine", "study", "research")):
        category = ClaimCategory.SCIENCE
    if any(w in lowered for w in ("president", "election", "senate", "vote")):
        category = ClaimCategory.POLITICS
    if any(w in lowered for w in ("covid", "cancer", "diet", "health")):
        category = ClaimCategory.HEALTH
    if any(w in lowered for w in ("instagram", "tiktok", "tweet", "facebook")):
        category = ClaimCategory.SOCIAL
    entities = []
    for token in ("apple", "ethylene", "usda", "vaccine"):
        if token in lowered:
            entities.append(Entity(name=token, type="CONCEPT"))
    topic = "postharvest physiology" if "apple" in lowered else "general"
    return ExtractedClaim(claim=text.strip(), entities=entities, topic=topic, category=category)


def run_claim_extraction(text: str, input_type: str = "text") -> ExtractedClaim:
    fallback = _heuristic(text, input_type).model_dump()
    parsed = llm.generate_json(
        "You extract a single checkable claim. Never invent facts.",
        f"Normalize this user input into JSON keys claim, entities (name,type), topic, category "
        f"(social|news|health|science|politics|screenshot), claim_type.\nINPUT:\n{text}",
        fallback,
    )
    try:
        entities = [Entity(**e) if isinstance(e, dict) else Entity(name=str(e)) for e in parsed.get("entities", [])]
        category = ClaimCategory(parsed.get("category", fallback["category"]))
        return ExtractedClaim(
            claim=parsed.get("claim") or text.strip(),
            entities=entities,
            topic=parsed.get("topic") or fallback["topic"],
            category=category,
            claim_type=parsed.get("claim_type") or "assertion",
        )
    except Exception:
        return ExtractedClaim.model_validate(fallback)
