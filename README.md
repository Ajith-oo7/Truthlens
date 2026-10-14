# TruthLens

Agentic fact verification system. Users submit claims or screenshots; a six-agent LangGraph investigator gathers evidence, scores sources, and returns a grounded verdict. It is not a chatbot.

## Quick start

1. Copy `.env.example` to `.env`. Add `GEMINI_API_KEY` when you have it (optional for the seeded demo).
2. Create a virtualenv and install backend deps:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

3. Run the API from the repo root so `.env` and the UI mount resolve:

```bash
cd backend
set PYTHONPATH=.
uvicorn app.main:app --reload --port 8080
```

4. Open [http://localhost:8080/ui/](http://localhost:8080/ui/) and submit `Apples ripen in 2 days.`

Optional stores:

```bash
docker compose up -d qdrant elasticsearch neo4j chromadb
python -m app.services.seed
```

Flutter client (web-first, Stitch tokens):

```bash
cd apps/flutter
flutter pub get
flutter run -d chrome
```

## Docs

- [Credentials checklist](docs/CREDENTIALS.md) — add keys one at a time
- [Local development](docs/architecture/LOCAL_DEV.md)
- [Architecture](docs/architecture/OVERVIEW.md)
- [API](docs/architecture/API.md)
- [FlutterFlow mapping](docs/flutterflow/SCREEN_SPEC.md)
- [Stitch screens](docs/stitch/SCREENS.md)

## Verdicts

`TRUE` · `FALSE` · `PARTIALLY_TRUE` · `MISLEADING` · `UNVERIFIABLE`

Insufficient evidence always yields `UNVERIFIABLE`. Every result shows evidence, sources, and a confidence score.
