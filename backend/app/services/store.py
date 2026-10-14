from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.config import get_settings
from app.models.schemas import (
    AnalyticsSummary,
    ExtractedClaim,
    FactCheckDossier,
    FactCheckSummary,
    KnowledgeGraphContext,
    PipelineEvent,
    SourceRef,
    VerdictResult,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.fact_checks: dict[str, dict[str, Any]] = {}

    def create_fact_check(self, original_input: str, input_type: str, image_path: str | None = None) -> str:
        fact_id = str(uuid4())
        with self._lock:
            self.fact_checks[fact_id] = {
                "id": fact_id,
                "user_id": None,
                "input_type": input_type,
                "status": "queued",
                "original_input": original_input,
                "image_path": image_path,
                "claim": None,
                "evidence": [],
                "sources": [],
                "agent_runs": [],
                "verdict": None,
                "knowledge_graph": None,
                "events": [],
                "metrics": [],
                "created_at": _now(),
                "updated_at": _now(),
            }
        return fact_id

    def update_status(self, fact_id: str, status: str) -> None:
        with self._lock:
            row = self.fact_checks[fact_id]
            row["status"] = status
            row["updated_at"] = _now()

    def append_event(self, fact_id: str, event: PipelineEvent) -> None:
        with self._lock:
            self.fact_checks[fact_id]["events"].append(event)
            self.fact_checks[fact_id]["updated_at"] = _now()

    def save_claim(self, fact_id: str, claim: ExtractedClaim) -> None:
        with self._lock:
            self.fact_checks[fact_id]["claim"] = claim
            self.fact_checks[fact_id]["updated_at"] = _now()

    def save_evidence(self, fact_id: str, items: list[Any], sources: list[SourceRef]) -> None:
        with self._lock:
            self.fact_checks[fact_id]["evidence"] = items
            self.fact_checks[fact_id]["sources"] = sources
            self.fact_checks[fact_id]["updated_at"] = _now()

    def save_graph(self, fact_id: str, graph: KnowledgeGraphContext) -> None:
        with self._lock:
            self.fact_checks[fact_id]["knowledge_graph"] = graph
            self.fact_checks[fact_id]["updated_at"] = _now()

    def save_agent_run(self, fact_id: str, agent_name: str, output: Any, latency_ms: int, status: str = "ok") -> None:
        with self._lock:
            self.fact_checks[fact_id]["agent_runs"].append(
                {
                    "agent_name": agent_name,
                    "output": output.model_dump() if hasattr(output, "model_dump") else output,
                    "latency_ms": latency_ms,
                    "status": status,
                    "token_usage": {},
                }
            )

    def save_verdict(self, fact_id: str, verdict: VerdictResult) -> None:
        with self._lock:
            self.fact_checks[fact_id]["verdict"] = verdict
            self.fact_checks[fact_id]["updated_at"] = _now()

    def save_metric(self, fact_id: str, name: str, value: float, details: dict[str, Any] | None = None) -> None:
        with self._lock:
            self.fact_checks[fact_id]["metrics"].append(
                {"metric_name": name, "value": value, "details": details or {}}
            )

    def get(self, fact_id: str) -> dict[str, Any] | None:
        return self.fact_checks.get(fact_id)

    def dossier(self, fact_id: str) -> FactCheckDossier | None:
        row = self.get(fact_id)
        if not row:
            return None
        return FactCheckDossier(
            id=row["id"],
            status=row["status"],
            original_input=row["original_input"],
            input_type=row["input_type"],
            claim=row["claim"],
            verdict=row["verdict"],
            evidence=row["evidence"],
            sources=row["sources"],
            knowledge_graph=row["knowledge_graph"],
            agent_runs=row["agent_runs"],
            events=row["events"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_summaries(self, limit: int = 50) -> list[FactCheckSummary]:
        rows = sorted(self.fact_checks.values(), key=lambda r: r["created_at"], reverse=True)[:limit]
        out: list[FactCheckSummary] = []
        for row in rows:
            verdict = row["verdict"]
            runs = row["agent_runs"]
            ok = sum(1 for run in runs if run.get("status") == "ok")
            claim = row["claim"]
            out.append(
                FactCheckSummary(
                    id=row["id"],
                    status=row["status"],
                    original_input=row["original_input"],
                    input_type=row["input_type"],
                    verdict=verdict.verdict if verdict else None,
                    confidence=verdict.confidence if verdict else None,
                    category=claim.category.value if claim else None,
                    created_at=row["created_at"],
                    agent_success=f"{ok}/6",
                )
            )
        return out

    def analytics(self) -> AnalyticsSummary:
        rows = list(self.fact_checks.values())
        by_verdict: dict[str, int] = {}
        confidences: list[float] = []
        success = 0
        completed = 0
        domains: set[str] = set()
        traces: list[dict[str, Any]] = []
        for row in rows:
            verdict = row["verdict"]
            if verdict:
                by_verdict[verdict.verdict.value] = by_verdict.get(verdict.verdict.value, 0) + 1
                confidences.append(verdict.confidence)
            if row["status"] == "completed":
                completed += 1
                runs = row["agent_runs"]
                if sum(1 for run in runs if run.get("status") == "ok") >= 6:
                    success += 1
            for source in row["sources"]:
                domains.add(getattr(source, "domain", "") or "")
            traces.append(
                {
                    "id": row["id"],
                    "claim": row["original_input"][:120],
                    "verdict": verdict.verdict.value if verdict else None,
                    "latency_ms": sum(run.get("latency_ms", 0) for run in row["agent_runs"]),
                    "status": row["status"],
                }
            )
        total = len(rows) or 1
        return AnalyticsSummary(
            total=len(rows),
            by_verdict=by_verdict,
            avg_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
            agent_success_rate=success / completed if completed else 0.0,
            source_diversity=float(len({d for d in domains if d})),
            retrieval_accuracy=0.0,
            verdict_consistency=1.0 if len(by_verdict) <= 2 else 0.85,
            recent_traces=traces[:12],
        )


_STORE: MemoryStore | None = None


def get_store() -> MemoryStore:
    global _STORE
    if _STORE is None:
        get_settings()
        _STORE = MemoryStore()
    return _STORE
