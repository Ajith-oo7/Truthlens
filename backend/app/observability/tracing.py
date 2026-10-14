from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Any, Iterator

from app.config import get_settings

logger = logging.getLogger("truthlens.otel")


def configure_observability() -> None:
    settings = get_settings()
    if settings.langsmith_api_key:
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true" if settings.langsmith_tracing else "false")

    if settings.otel_exporter_otlp_endpoint:
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider(resource=Resource.create({"service.name": settings.otel_service_name}))
            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
            )
            trace.set_tracer_provider(provider)
        except Exception as exc:  # pragma: no cover
            logger.warning("OpenTelemetry init skipped: %s", exc)


@contextmanager
def span(name: str, **attrs: Any) -> Iterator[dict[str, Any]]:
    started = time.perf_counter()
    payload = {"name": name, **attrs}
    try:
        yield payload
        payload["status"] = "ok"
    except Exception as exc:
        payload["status"] = "error"
        payload["error"] = str(exc)
        raise
    finally:
        payload["latency_ms"] = int((time.perf_counter() - started) * 1000)
        logger.info("span %s %s", name, {k: v for k, v in payload.items() if k != "name"})
