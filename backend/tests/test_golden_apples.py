from app.agents.graph import run_investigation
from app.models.schemas import VerdictLabel


def test_apples_ripen_in_two_days_is_false_or_unverifiable():
    state = run_investigation(
        {
            "fact_check_id": "golden-apples",
            "original_input": "Apples ripen in 2 days.",
            "input_type": "text",
            "extra_uncertainty": False,
            "events": [],
        }
    )
    assert state["extracted"].claim
    assert len(state["evidence"]) >= 2
    assert state["verdict"].evidence_ids
    assert state["verdict"].sources
    assert 0 <= state["verdict"].confidence <= 1
    assert state["verdict"].verdict in {
        VerdictLabel.FALSE,
        VerdictLabel.MISLEADING,
        VerdictLabel.UNVERIFIABLE,
    }
    ledger = {item.url for item in state["evidence"] if item.url}
    for source in state["verdict"].sources:
        if source.url:
            assert source.url in ledger


def test_pipeline_emits_required_steps():
    events = []

    def sink(event_type, message, agent):
        events.append(event_type)

    run_investigation(
        {
            "fact_check_id": "events",
            "original_input": "Apples ripen in 2 days.",
            "input_type": "text",
            "events": [],
        },
        sink=sink,
    )
    for required in (
        "extracting_claim",
        "searching_fact_databases",
        "searching_evidence",
        "building_knowledge_graph",
        "evaluating_sources",
        "generating_verdict",
        "completed",
    ):
        assert required in events


def test_generic_days_claim_does_not_cite_apple_corpus():
    state = run_investigation(
        {
            "fact_check_id": "unrelated-days",
            "original_input": "How many days until Christmas?",
            "input_type": "text",
            "extra_uncertainty": False,
            "events": [],
        }
    )
    blob = " ".join(f"{item.title} {item.text}" for item in state["evidence"]).lower()
    assert "apple" not in blob
    assert "ripen" not in blob
    assert state["verdict"].verdict == VerdictLabel.UNVERIFIABLE


def test_unrelated_claim_does_not_cite_apple_corpus():
    state = run_investigation(
        {
            "fact_check_id": "unrelated-moon",
            "original_input": "The moon is made of cheese.",
            "input_type": "text",
            "extra_uncertainty": False,
            "events": [],
        }
    )
    blob = " ".join(f"{item.title} {item.text}" for item in state["evidence"]).lower()
    assert "apple" not in blob
    assert "malus" not in blob
    assert "ripen" not in blob
    assert state["verdict"].verdict == VerdictLabel.UNVERIFIABLE
