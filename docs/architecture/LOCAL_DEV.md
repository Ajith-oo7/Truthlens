# Local development

## Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=.
uvicorn app.main:app --reload --port 8080
```

Tests:

```bash
cd backend
set PYTHONPATH=.
pytest -q
```

## Docker data plane

```bash
docker compose up -d qdrant elasticsearch neo4j chromadb
```

Neo4j browser: http://localhost:7474 (`neo4j` / `truthlens`)

## Flutter

```bash
cd apps/flutter
flutter pub get
flutter run -d chrome --dart-define=API=http://localhost:8080
```

The Stitch-matched web client is served at `/ui/` from FastAPI for immediate verification.

## MCP servers

From `backend` with `PYTHONPATH=.`:

```bash
python -m app.mcp.factcheck_server
python -m app.mcp.evidence_server
python -m app.mcp.neo4j_server
python -m app.mcp.credibility_server
python -m app.mcp.retrieval_server
```

## Seed

```bash
python -m app.services.seed
```
