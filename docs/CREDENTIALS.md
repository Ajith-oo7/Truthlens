# TruthLens credentials checklist

Paste values into a local `.env` only. Never commit secrets or send them in chat.

Copy `.env.example` to `.env`, then fill keys in the order below. Each missing key disables that integration; the API still starts.

## Hand-over order

1. Gemini (required for live LLM verdicts)
2. Supabase (auth, Postgres, screenshot storage)
3. Search / Fact Check APIs (live evidence)
4. LangSmith (traces)
5. Optional OCR / OpenTelemetry

Docker Compose covers Neo4j, Qdrant, Elasticsearch, and Chroma locally.

---

## 1. Required for a real investigation

| Variable | Where to get it | Fallback if missing |
| --- | --- | --- |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) | Deterministic mock investigation (sample claim still works) |
| `GEMINI_MODEL` | Default `gemini-3.8-flash` | Tries 3.8 → 3.6 → 3.5-lite if the named model 404s |
| `GEMINI_EMBEDDING_MODEL` | Default `gemini-embedding-001` | Hash embeddings for local seed corpus |

---

## 2. Required for persistence, auth, screenshots

| Variable | Where to get it | Fallback if missing |
| --- | --- | --- |
| `SUPABASE_URL` | Supabase project Settings → API | In-memory store (lost on restart) |
| `SUPABASE_ANON_KEY` | Same page | Local-dev anonymous user |
| `SUPABASE_SERVICE_ROLE_KEY` | Same page (server only) | In-memory store |
| `SUPABASE_STORAGE_BUCKET` | Default `screenshots` | Local `backend/data/uploads` |

Apply `infra/supabase/migrations/001_init.sql` in the Supabase SQL editor after the project exists.

---

## 3. Local Docker (no cloud key required)

Start with `docker compose up -d qdrant elasticsearch neo4j chromadb`.

| Variable | Local default | Cloud alternative |
| --- | --- | --- |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Aura URI |
| `NEO4J_USER` | `neo4j` | Aura username |
| `NEO4J_PASSWORD` | `truthlens` | Aura password |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant Cloud URL |
| `QDRANT_API_KEY` | empty | Qdrant Cloud API key |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | Elastic Cloud URL |
| `ELASTICSEARCH_API_KEY` | empty | Elastic Cloud API key |
| `CHROMA_PATH` | `./backend/data/chroma` | Persistent volume path |
| `CHROMA_HOST` | empty (embedded) | `chromadb` compose service |
| `CHROMA_PORT` | `8001` | Compose mapped port |
| `CHROMA_ENABLED` / `QDRANT_ENABLED` / `ELASTICSEARCH_ENABLED` / `NEO4J_ENABLED` | `false` until Docker/cloud is up | Seeded lexical corpus is used instead |

If a store is down, that retrieval port is skipped. The run continues.

---

## 4. Required for live web / fact-check databases

Provide **one** web search option plus the Fact Check Tools key when you want live evidence.

| Variable | Where to get it | Fallback if missing |
| --- | --- | --- |
| `GOOGLE_FACTCHECK_API_KEY` | [Google Fact Check Tools API](https://developers.google.com/fact-check/tools/api) | Empty fact-check package |
| `TAVILY_API_KEY` | [Tavily](https://tavily.com/) | Preferred web search |
| `SERPAPI_API_KEY` | [SerpAPI](https://serpapi.com/) | Used if Tavily absent |
| `GOOGLE_CSE_ID` | Google Programmable Search | Used if Tavily/SerpAPI absent |
| `GOOGLE_CSE_API_KEY` | Google Cloud / CSE | Used with `GOOGLE_CSE_ID` |

Without these, hybrid retrieval uses only the seeded trusted corpus (Chroma / Qdrant / Elasticsearch / Neo4j).

---

## 5. Optional

| Variable | Purpose | Fallback |
| --- | --- | --- |
| `LANGSMITH_API_KEY` | LangSmith traces | Local logging only |
| `LANGSMITH_PROJECT` | Default `truthlens` | Default name |
| `LANGSMITH_TRACING` | `true` to enable | Disabled |
| `GOOGLE_APPLICATION_CREDENTIALS` | Cloud Vision OCR | Gemini multimodal OCR |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector | Console spans |
| `OTEL_SERVICE_NAME` | Default `truthlens-api` | Default |

Stitch is already configured in Cursor MCP. Do not put that key in git. Rotate the key that was pasted in chat.

---

## 6. App / security

| Variable | Purpose | Default |
| --- | --- | --- |
| `APP_ENV` | `local` / `production` | `local` |
| `API_HOST` | Bind address | `0.0.0.0` |
| `API_PORT` | HTTP port | `8080` |
| `CORS_ORIGINS` | Comma-separated origins | `http://localhost:3000,http://localhost:8080,http://localhost:5173` |
| `DEV_BYPASS_AUTH` | Allow anonymous local calls | `true` in local |
| `MIN_EVIDENCE_COUNT` | Below this → `UNVERIFIABLE` | `2` |
| `CONFIDENCE_INCONCLUSIVE_BAND` | Forced unverifiable band | `0.15` |

---

## What I need from you next

Send **Gemini first** (into `.env`, not chat). After that, Supabase. Search keys can wait; the apples-ripen demo uses the seeded corpus.
