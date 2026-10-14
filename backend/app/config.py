from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    cors_origins: str = "http://localhost:3000,http://localhost:8080,http://localhost:5173"
    dev_bypass_auth: bool = True
    min_evidence_count: int = 2
    confidence_inconclusive_band: float = 0.15

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "screenshots"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "truthlens"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_enabled: bool = False

    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_api_key: str = ""
    elasticsearch_enabled: bool = False

    neo4j_enabled: bool = False

    chroma_path: str = str(ROOT / "backend" / "data" / "chroma")
    chroma_host: str = ""
    chroma_port: int = 8001
    chroma_enabled: bool = False

    google_factcheck_api_key: str = ""
    tavily_api_key: str = ""
    serpapi_api_key: str = ""
    google_cse_id: str = ""
    google_cse_api_key: str = ""

    langsmith_api_key: str = ""
    langsmith_project: str = "truthlens"
    langsmith_tracing: bool = False
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "truthlens-api"

    google_application_credentials: str = ""

    upload_dir: Path = Field(default_factory=lambda: ROOT / "backend" / "data" / "uploads")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_supabase(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
    return settings
