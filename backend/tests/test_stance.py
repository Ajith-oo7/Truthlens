from app.agents.verdict import run_verdict
from app.models.schemas import EvidenceItem, ExtractedClaim, VerdictLabel
from app.tools.credibility import evaluate_source
from app.tools.stance import heuristic_label


def _item(**kwargs) -> EvidenceItem:
    base = dict(id="E-001", text="", url="", store="web", title="", domain="", stance="neutral")
    base.update(kwargs)
    return EvidenceItem(**base)


def test_ulta_shop_page_supports_skincare_claim():
    labeled = heuristic_label(
        "Ulta Beauty sells skincare products also",
        _item(
            title="Skincare | Ulta Beauty",
            text="Shop skincare at Ulta Beauty. Ulta Beauty sells thousands of skincare products.",
            url="https://www.ulta.com/shop/skin-care",
            domain="ulta.com",
        ),
    )
    assert labeled.stance == "supports"


def test_seed_refute_stance_is_kept():
    labeled = heuristic_label(
        "Apples ripen in 2 days.",
        _item(
            stance="refutes",
            title="USDA Handbook 66",
            text="A claim that apples fully ripen in 2 days is physiologically false.",
            url="https://www.ars.usda.gov/oc/np/handbook66/apples",
            domain="ars.usda.gov",
        ),
    )
    assert labeled.stance == "refutes"


def test_supporting_catalog_evidence_yields_true(monkeypatch):
    monkeypatch.setattr("app.agents.verdict.llm.generate_json", lambda system, user, fallback: fallback)
    evidence = [
        _item(
            id="E-001",
            stance="supports",
            title="Skincare | Ulta Beauty",
            text="Ulta Beauty sells skincare products.",
            url="https://www.ulta.com/shop/skin-care",
            domain="ulta.com",
        ),
        _item(
            id="E-002",
            stance="supports",
            title="Ulta Beauty",
            text="Shop makeup, hair, and skincare at Ulta Beauty.",
            url="https://www.ulta.com/",
            domain="ulta.com",
        ),
    ]
    scores = [evaluate_source(item.url, item.domain) for item in evidence]
    result = run_verdict(
        ExtractedClaim(claim="Ulta Beauty sells skincare products also"),
        evidence,
        scores,
        [],
    )
    assert result.verdict == VerdictLabel.TRUE
    assert result.confidence > 0.5
