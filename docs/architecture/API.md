# API

Base URL: `http://localhost:8080`

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Dependency probe |
| POST | `/v1/auth/session` | Dev bypass or Supabase JWT |
| POST | `/v1/fact-checks` | `{ "claim": "..." }` |
| POST | `/v1/fact-checks/screenshot` | multipart `image` |
| GET | `/v1/fact-checks/{id}` | Full dossier |
| GET | `/v1/fact-checks/{id}/events` | SSE progress |
| GET | `/v1/fact-checks` | History |
| GET | `/v1/analytics/summary` | KPIs |

SSE event types: `extracting_claim`, `searching_fact_databases`, `searching_evidence`, `building_knowledge_graph`, `evaluating_sources`, `generating_verdict`, `completed`, `failed`.
