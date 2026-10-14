import pytest


@pytest.fixture(autouse=True)
def stub_live_llm_and_search(monkeypatch):
    monkeypatch.setattr("app.agents.extract.llm.generate_json", lambda system, user, fallback: fallback)
    monkeypatch.setattr("app.agents.verdict.llm.generate_json", lambda system, user, fallback: fallback)
    monkeypatch.setattr("app.agents.reasoning.llm.generate_json", lambda system, user, fallback: fallback)
    monkeypatch.setattr("app.tools.stance.llm.generate_json", lambda system, user, fallback: fallback)
    monkeypatch.setattr("app.agents.evidence.search_web", lambda query: [])
    monkeypatch.setattr("app.agents.evidence.search_fact_checks", lambda query, language="en": [])
