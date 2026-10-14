from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.agents.graph import run_investigation
from app.api.events import broker
from app.config import get_settings
from app.eval.metrics import record_run_metrics
from app.models.schemas import (
    AnalyticsSummary,
    FactCheckCreate,
    FactCheckDossier,
    FactCheckSummary,
    HealthStatus,
    PipelineEvent,
    SessionRequest,
)
from app.observability.tracing import span
from app.safety.gate import SafetyGate
from app.services.llm import llm
from app.services.store import get_store

router = APIRouter()
safety = SafetyGate()


@router.post("/v1/auth/session")
def session(payload: SessionRequest) -> dict:
    settings = get_settings()
    if settings.dev_bypass_auth:
        return {"ok": True, "mode": "dev", "user": "local-analyst"}
    if not payload.access_token:
        raise HTTPException(401, "Missing access token")
    return {"ok": True, "mode": "supabase"}


@router.post("/v1/fact-checks")
async def create_fact_check(background: BackgroundTasks, payload: FactCheckCreate) -> dict:
    return _enqueue(background, payload.claim or "", "text", None)


@router.post("/v1/fact-checks/screenshot")
async def create_screenshot_check(
    background: BackgroundTasks,
    image: UploadFile = File(...),
    claim: str | None = Form(default=None),
) -> dict:
    settings = get_settings()
    data = await image.read()
    dest = settings.upload_dir / f"{uuid4().hex}_{image.filename or 'shot.bin'}"
    dest.write_bytes(data)
    ocr = llm.ocr_image(data, image.content_type or "image/png")
    text = (ocr or claim or "").strip() or "Unreadable screenshot; no claim text extracted."
    return _enqueue(background, text, "image", str(dest))


def _enqueue(background: BackgroundTasks, text: str, input_type: str, image_path: str | None) -> dict:
    decision = safety.sanitize(text)
    if not decision.allowed:
        raise HTTPException(400, f"Claim rejected: {', '.join(decision.flags)}")
    store = get_store()
    fact_id = store.create_fact_check(decision.sanitized_text, input_type, image_path)
    store.append_event(fact_id, PipelineEvent(type="queued", message="Investigation queued."))
    background.add_task(_run, fact_id, decision.sanitized_text, input_type, decision.extra_uncertainty)
    return {"fact_check_id": fact_id, "status": "queued"}


@router.get("/v1/fact-checks/{fact_id}", response_model=FactCheckDossier)
def get_fact_check(fact_id: str) -> FactCheckDossier:
    dossier = get_store().dossier(fact_id)
    if not dossier:
        raise HTTPException(404, "Fact check not found")
    return dossier


@router.get("/v1/fact-checks/{fact_id}/events")
async def stream_events(fact_id: str) -> StreamingResponse:
    if not get_store().get(fact_id):
        raise HTTPException(404, "Fact check not found")

    async def gen():
        queue = broker.subscribe(fact_id)
        try:
            while True:
                event: PipelineEvent = await queue.get()
                yield f"event: {event.type}\ndata: {event.model_dump_json()}\n\n"
                if event.type in {"completed", "failed"}:
                    break
        finally:
            broker.unsubscribe(fact_id, queue)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/v1/fact-checks", response_model=list[FactCheckSummary])
def list_fact_checks(limit: int = 50) -> list[FactCheckSummary]:
    return get_store().list_summaries(limit)


@router.get("/v1/analytics/summary", response_model=AnalyticsSummary)
def analytics() -> AnalyticsSummary:
    return get_store().analytics()


@router.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    settings = get_settings()
    services = {
        "gemini": "ok" if settings.has_gemini else "disabled",
        "supabase": "ok" if settings.has_supabase else "memory",
        "chroma": "embedded",
        "qdrant": settings.qdrant_url,
        "elasticsearch": settings.elasticsearch_url,
        "neo4j": settings.neo4j_uri,
    }
    return HealthStatus(ok=True, services=services)


def _run(fact_id: str, text: str, input_type: str, extra_uncertainty: bool) -> None:
    store = get_store()
    store.update_status(fact_id, "running")

    def sink(event_type: str, message: str, agent: str | None) -> None:
        event = PipelineEvent(type=event_type, message=message, agent=agent)
        store.append_event(fact_id, event)
        broker.publish(fact_id, event)

    try:
        with span("investigation.run", fact_check_id=fact_id):
            state = run_investigation(
                {
                    "fact_check_id": fact_id,
                    "original_input": text,
                    "input_type": input_type,
                    "extra_uncertainty": extra_uncertainty,
                    "events": [],
                },
                sink=sink,
            )
        extracted = state["extracted"]
        store.save_claim(fact_id, extracted)
        store.save_evidence(fact_id, state.get("evidence", []), state["verdict"].sources)
        store.save_graph(fact_id, state["graph"])
        for agent_name, key in [
            ("claim_extraction", "extracted"),
            ("evidence_retrieval", "evidence"),
            ("knowledge_graph", "graph"),
            ("credibility", "credibility"),
            ("reasoning", "reasoning"),
            ("verdict", "verdict"),
        ]:
            store.save_agent_run(fact_id, agent_name, state.get(key), 0)
        store.save_verdict(fact_id, state["verdict"])
        record_run_metrics(fact_id, state.get("evidence", []), state["verdict"])
        store.update_status(fact_id, "completed")
    except Exception as exc:
        store.update_status(fact_id, "failed")
        event = PipelineEvent(type="failed", message=str(exc), agent="orchestrator")
        store.append_event(fact_id, event)
        broker.publish(fact_id, event)
