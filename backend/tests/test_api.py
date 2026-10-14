from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_ui():
    assert client.get("/health").status_code == 200
    assert client.get("/ui/").status_code == 200


def test_fact_check_json_roundtrip():
    created = client.post("/v1/fact-checks", json={"claim": "Apples ripen in 2 days."})
    assert created.status_code == 200
    fact_id = created.json()["fact_check_id"]
    dossier = client.get(f"/v1/fact-checks/{fact_id}")
    assert dossier.status_code == 200
    assert dossier.json()["original_input"].startswith("Apples")
