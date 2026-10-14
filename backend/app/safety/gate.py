from __future__ import annotations

import re
from dataclasses import dataclass

INJECTION_PATTERNS = [
    r"ignore (all|previous|above) instructions",
    r"system prompt",
    r"you are now",
    r"jailbreak",
    r"reveal (the )?(hidden|secret) (key|prompt)",
]

DISALLOWED_ADVICE = [
    r"\bhow to make (a )?bomb\b",
    r"\bsell (me )?(fentanyl|heroin|meth)\b",
]


@dataclass
class SafetyDecision:
    allowed: bool
    sanitized_text: str
    flags: list[str]
    extra_uncertainty: bool = False


class SafetyGate:
    def sanitize(self, text: str) -> SafetyDecision:
        raw = (text or "").strip()
        flags: list[str] = []
        extra = False
        lowered = raw.lower()

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                flags.append("prompt_injection")
                raw = re.sub(pattern, "[filtered]", raw, flags=re.I)

        for pattern in DISALLOWED_ADVICE:
            if re.search(pattern, lowered):
                flags.append("disallowed_content")
                return SafetyDecision(False, "", flags, extra_uncertainty=True)

        if any(word in lowered for word in ("vaccine", "cancer", "covid", "election", "president")):
            extra = True
            flags.append("sensitive_domain")

        if len(raw) < 3:
            flags.append("too_short")
            return SafetyDecision(False, raw, flags)

        return SafetyDecision(True, raw[:4000], flags, extra_uncertainty=extra)

    def force_unverifiable(self, evidence_count: int, min_count: int, confidence: float, band: float) -> str | None:
        if evidence_count < min_count:
            return "Insufficient independent evidence in the citation ledger."
        if abs(confidence - 0.5) < band and evidence_count < min_count + 2:
            return "Support and refutation scores are inconclusive."
        return None
