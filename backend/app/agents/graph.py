from __future__ import annotations

from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.credibility import run_credibility
from app.agents.evidence import run_evidence_retrieval
from app.agents.extract import run_claim_extraction
from app.agents.knowledge import run_knowledge_graph
from app.agents.reasoning import run_reasoning
from app.agents.verdict import run_verdict
from app.models.schemas import (
    CredibilityScore,
    EvidenceItem,
    ExtractedClaim,
    KnowledgeGraphContext,
    PipelineEvent,
    ReasoningStep,
    VerdictResult,
)
from app.observability.tracing import span


class InvestigationState(TypedDict, total=False):
    fact_check_id: str
    original_input: str
    input_type: str
    extra_uncertainty: bool
    extracted: ExtractedClaim
    evidence: list[EvidenceItem]
    layers: dict[str, list[EvidenceItem]]
    graph: KnowledgeGraphContext
    credibility: list[CredibilityScore]
    reasoning: list[ReasoningStep]
    verdict: VerdictResult
    events: list[PipelineEvent]


EventSink = Callable[[str, str, str | None], None]


def _emit(state: InvestigationState, sink: EventSink | None, event_type: str, message: str, agent: str) -> None:
    event = PipelineEvent(type=event_type, message=message, agent=agent)
    state.setdefault("events", []).append(event)
    if sink:
        sink(event_type, message, agent)


def build_graph(sink: EventSink | None = None):
    def extract(state: InvestigationState) -> InvestigationState:
        _emit(state, sink, "extracting_claim", "Extracting Claim...", "claim_extraction")
        with span("agent.claim_extraction") as meta:
            extracted = run_claim_extraction(state["original_input"], state.get("input_type", "text"))
            meta["tokens"] = 0
        state["extracted"] = extracted
        return state

    def factcheck(state: InvestigationState) -> InvestigationState:
        _emit(state, sink, "searching_fact_databases", "Searching Fact Databases...", "factcheck_mcp")
        return state

    def evidence(state: InvestigationState) -> InvestigationState:
        _emit(state, sink, "searching_evidence", "Searching Evidence...", "evidence_retrieval")
        with span("agent.evidence_retrieval"):
            package, layers = run_evidence_retrieval(state["extracted"])
        state["evidence"] = package.items
        state["layers"] = layers
        return state

    def knowledge(state: InvestigationState) -> InvestigationState:
        _emit(state, sink, "building_knowledge_graph", "Building Knowledge Graph...", "knowledge_graph")
        with span("graph.query"):
            state["graph"] = run_knowledge_graph(state["extracted"], state.get("evidence", []))
        return state

    def credibility(state: InvestigationState) -> InvestigationState:
        _emit(state, sink, "evaluating_sources", "Evaluating Sources...", "credibility")
        with span("agent.credibility"):
            state["credibility"] = run_credibility(state.get("evidence", []))
        return state

    def reasoning(state: InvestigationState) -> InvestigationState:
        with span("agent.reasoning"):
            state["reasoning"] = run_reasoning(
                state["extracted"],
                state.get("evidence", []),
                state.get("graph") or KnowledgeGraphContext(),
                state.get("credibility", []),
            )
        return state

    def verdict(state: InvestigationState) -> InvestigationState:
        _emit(state, sink, "generating_verdict", "Generating Verdict...", "verdict")
        with span("verdict.generate"):
            state["verdict"] = run_verdict(
                state["extracted"],
                state.get("evidence", []),
                state.get("credibility", []),
                state.get("reasoning", []),
                extra_uncertainty=state.get("extra_uncertainty", False),
            )
        _emit(state, sink, "completed", "Investigation sealed.", "verdict")
        return state

    graph = StateGraph(InvestigationState)
    graph.add_node("node_extract", extract)
    graph.add_node("node_factcheck", factcheck)
    graph.add_node("node_evidence", evidence)
    graph.add_node("node_knowledge", knowledge)
    graph.add_node("node_credibility", credibility)
    graph.add_node("node_reasoning", reasoning)
    graph.add_node("node_verdict", verdict)
    graph.add_edge(START, "node_extract")
    graph.add_edge("node_extract", "node_factcheck")
    graph.add_edge("node_factcheck", "node_evidence")
    graph.add_edge("node_evidence", "node_knowledge")
    graph.add_edge("node_knowledge", "node_credibility")
    graph.add_edge("node_credibility", "node_reasoning")
    graph.add_edge("node_reasoning", "node_verdict")
    graph.add_edge("node_verdict", END)
    return graph.compile()


def run_investigation(payload: dict[str, Any], sink: EventSink | None = None) -> InvestigationState:
    compiled = build_graph(sink)
    return compiled.invoke(payload)
