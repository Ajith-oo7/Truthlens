from __future__ import annotations

from typing import Any

SEED_DOCUMENTS: list[dict[str, Any]] = [
    {
        "id": "usda-handbook-66",
        "title": "USDA Handbook 66: Commercial Storage and Ripening of Apples",
        "body": (
            "Apples are climacteric fruit. Under typical post-harvest conditions, starch-to-sugar conversion "
            "and full ripening require about 7 to 14 days at room temperature (around 20C). Cold storage "
            "can keep apples dormant for months. A claim that apples fully ripen in 2 days is physiologically false."
        ),
        "url": "https://www.ars.usda.gov/oc/np/handbook66/apples",
        "domain": "ars.usda.gov",
        "tier": "government",
        "topic": "postharvest physiology",
        "stance": "refutes",
        "published_at": "2016-01-01",
    },
    {
        "id": "ucdavis-apple",
        "title": "UC Davis Postharvest Technology Center: Apple ripening kinetics",
        "body": (
            "Commercial ethylene treatment (about 100 ppm) can start skin color change within 48 hours, "
            "but pulp softening and flavor development typically need more than 5 days. Household paper-bag "
            "tricks do not make apples fully ripe in two days."
        ),
        "url": "https://postharvest.ucdavis.edu/commodity/apple",
        "domain": "postharvest.ucdavis.edu",
        "tier": "university",
        "topic": "ethylene ripening",
        "stance": "refutes",
        "published_at": "2022-03-15",
    },
    {
        "id": "jpp-ethylene",
        "title": "Journal of Plant Physiology: Ethylene and starch breakdown in Malus",
        "body": (
            "Peer-reviewed assays show starch-index transition in apples takes approximately 9 days at 20C. "
            "Two-day ripening is far below the biological minimum for complete maturation."
        ),
        "url": "https://doi.org/10.1016/j.jplph.apple-ethylene",
        "domain": "sciencedirect.com",
        "tier": "peer_reviewed",
        "topic": "plant physiology",
        "stance": "refutes",
        "published_at": "2021-06-01",
    },
    {
        "id": "reuters-fruit-hacks",
        "title": "Reuters Fact Check: Household fruit ripening hacks",
        "body": (
            "Viral social posts claiming apples become fully ripe in 48 hours confuse surface softening "
            "or banana kinetics with apple metabolism. The claim is false."
        ),
        "url": "https://www.reuters.com/fact-check/apple-ripening-48-hours",
        "domain": "reuters.com",
        "tier": "major_news",
        "topic": "fact check",
        "stance": "refutes",
        "published_at": "2023-09-12",
    },
    {
        "id": "viral-kitchen",
        "title": "KitchenHacksLife: Ripen any apple in under 48 hours",
        "body": (
            "Put green apples in a paper bag and they will be sweet and soft in 2 days. "
            "No scientific measurements provided."
        ),
        "url": "https://viralhackstoday.info/ripen-apples-48-hours",
        "domain": "viralhackstoday.info",
        "tier": "unknown",
        "topic": "viral tips",
        "stance": "supports",
        "published_at": "2024-02-02",
    },
    {
        "id": "who-vaccine-example",
        "title": "WHO: Vaccines undergo multi-phase clinical evaluation",
        "body": "Licensed vaccines are evaluated in phased clinical trials and ongoing safety monitoring.",
        "url": "https://www.who.int/news-room/feature-stories/detail/vaccine-efficacy",
        "domain": "who.int",
        "tier": "government",
        "topic": "public health",
        "stance": "neutral",
        "published_at": "2024-01-10",
    },
]


import re

STOPWORDS = {
    "the", "and", "for", "are", "was", "were", "this", "that", "with", "from",
    "have", "has", "had", "been", "will", "would", "could", "should", "about",
    "into", "than", "then", "them", "they", "their", "there", "what", "when",
    "where", "which", "while", "does", "did", "not", "but", "can", "all", "any",
    "out", "how", "why", "who", "its", "you", "your", "our", "his", "her",
    "claim", "said", "says", "just", "more", "also", "over", "after", "before",
}

# Too common in the apple seed pack (and English) to prove topical overlap.
GENERIC_FILLER = STOPWORDS | {
    "day", "days", "hour", "hours", "two", "one", "three", "four", "five",
    "time", "year", "years", "month", "months", "week", "weeks", "many",
    "much", "very", "only", "even", "still", "same", "other", "most", "some",
    "used", "using", "make", "made", "false", "true", "fully", "under", "home",
    "require", "requires", "typical", "around", "without", "cannot", "below",
    "until", "into", "such", "than", "then", "them",
}


def _words(text: str) -> set[str]:
    return {
        tok
        for tok in re.findall(r"[a-z0-9]+", (text or "").lower())
        if len(tok) > 2 and tok not in GENERIC_FILLER
    }


def claim_tokens(query: str) -> set[str]:
    return _words(query)


def _overlap(query: str, *parts: str) -> set[str]:
    return _words(query) & _words(" ".join(parts))


def lexical_score(query: str, doc: dict[str, Any]) -> float:
    tokens = _words(query)
    if not tokens:
        return 0.0
    matched = _overlap(query, doc.get("title", ""), doc.get("body", ""))
    strong = {tok for tok in matched if len(tok) >= 5}
    if not strong and len(matched) < 2:
        return 0.0
    bonus = 0.15 if doc.get("tier") in {"government", "university", "peer_reviewed"} else 0.0
    return len(matched) / len(tokens) + bonus


def is_relevant_text(query: str, *parts: str, min_hits: int = 1) -> bool:
    matched = _overlap(query, *parts)
    strong = {tok for tok in matched if len(tok) >= 5}
    if strong:
        return True
    return len(matched) >= max(min_hits, 2)
