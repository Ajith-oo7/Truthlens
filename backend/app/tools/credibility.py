from __future__ import annotations

from urllib.parse import urlparse

from app.models.schemas import CredibilityScore, SourceTier, TIER_SCORES

GOV_SUFFIXES = (".gov", ".gov.uk", ".mil", ".int")
UNI_HINTS = (".edu", "ac.uk", "university", "ucdavis", "harvard", "mit.edu", "stanford")
JOURNAL_HINTS = ("doi.org", "pubmed", "nature.com", "sciencedirect", "springer", "wiley", "arxiv.org")
NEWS_HINTS = (
    "reuters.com",
    "apnews.com",
    "bbc.",
    "nytimes.com",
    "washingtonpost.com",
    "theguardian.com",
    "npr.org",
    "factcheck.org",
    "snopes.com",
    "politifact.com",
)
CORPORATE_HINTS = ("medium.com", "substack.com", "blog.", "wordpress.", "blogspot.")


def classify_domain(url: str, domain: str | None = None) -> SourceTier:
    host = (domain or urlparse(url).netloc or url).lower().removeprefix("www.")
    if any(host.endswith(sfx) or sfx in host for sfx in GOV_SUFFIXES) or host.endswith(".who.int") or "who.int" in host:
        return SourceTier.GOVERNMENT
    if any(hint in host for hint in UNI_HINTS):
        return SourceTier.UNIVERSITY
    if any(hint in host for hint in JOURNAL_HINTS):
        return SourceTier.PEER_REVIEWED
    if any(hint in host for hint in NEWS_HINTS):
        return SourceTier.MAJOR_NEWS
    if any(hint in host for hint in CORPORATE_HINTS):
        return SourceTier.CORPORATE_BLOG
    return SourceTier.UNKNOWN


def evaluate_source(url: str, domain: str | None = None, title: str = "") -> CredibilityScore:
    tier = classify_domain(url, domain)
    score = TIER_SCORES[tier]
    host = domain or urlparse(url).netloc
    return CredibilityScore(
        source_id=host or url,
        url=url,
        domain=host,
        tier=tier,
        score=score,
        rationale=f"{tier.value} domain scored {score}",
    )


def calculate_score(domain: str, metadata: dict | None = None) -> int:
    extra = metadata or {}
    base = TIER_SCORES[classify_domain(domain, domain)]
    if extra.get("peer_reviewed"):
        return max(base, 90)
    return base
