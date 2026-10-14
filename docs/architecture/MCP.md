# MCP servers

| Server | Module | Tools |
| --- | --- | --- |
| FactCheck | `app.mcp.factcheck_server` | `search_fact_checks`, `retrieve_fact_check` |
| Evidence | `app.mcp.evidence_server` | `search_web`, `search_articles`, `retrieve_sources` |
| Neo4j | `app.mcp.neo4j_server` | `query_graph`, `find_relationships` |
| Credibility | `app.mcp.credibility_server` | `evaluate_source`, `calculate_score` |
| Retrieval | `app.mcp.retrieval_server` | `search_chromadb`, `search_qdrant`, `search_elasticsearch` |

All tools call `backend/app/tools` / retrieval / graph. LangGraph uses the Python functions directly.
