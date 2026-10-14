# Deployment

## MVP

- FastAPI on Cloud Run (or any container host)
- Flutter web on a CDN / Firebase Hosting
- Supabase for Auth, Postgres, Storage
- Docker or Cloud counterparts for Qdrant, Elasticsearch, Neo4j

## Production

- Qdrant Cloud, Elastic Cloud, Neo4j Aura
- LangSmith + OTLP collector
- Cloud Armor / rate limits
- Human review queue for contested political/health claims

See `infra/docker/api.Dockerfile` and `docker-compose.yml`.
