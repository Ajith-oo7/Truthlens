# Data flow

1. Claim or screenshot enters the safety gate.
2. OCR (Gemini vision) may replace image bytes with text.
3. Claim Extraction writes `claims`.
4. Retrieval writes `evidence` and `sources` (Chroma, Qdrant, ES, web, Fact Check Tools).
5. Neo4j upsert writes `knowledge_graph_links`.
6. Credibility scores attach to sources.
7. Reasoning + Verdict write `verdicts` and `agent_runs`.
8. Evaluation writes `evaluation_metrics`.
9. Client reads the dossier and SSE events.

Without Supabase, `MemoryStore` keeps the same shape in process memory.
