from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class VerdictLabel(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    PARTIALLY_TRUE = "PARTIALLY_TRUE"
    MISLEADING = "MISLEADING"
    UNVERIFIABLE = "UNVERIFIABLE"


class ClaimCategory(str, Enum):
    SOCIAL = "social"
    NEWS = "news"
    HEALTH = "health"
    SCIENCE = "science"
    POLITICS = "politics"
    SCREENSHOT = "screenshot"


class SourceTier(str, Enum):
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    PEER_REVIEWED = "peer_reviewed"
    MAJOR_NEWS = "major_news"
    CORPORATE_BLOG = "corporate_blog"
    UNKNOWN = "unknown"


TIER_SCORES: dict[SourceTier, int] = {
    SourceTier.GOVERNMENT: 95,
    SourceTier.UNIVERSITY: 90,
    SourceTier.PEER_REVIEWED: 90,
    SourceTier.MAJOR_NEWS: 75,
    SourceTier.CORPORATE_BLOG: 50,
    SourceTier.UNKNOWN: 20,
}


class Entity(BaseModel):
    name: str
    type: str = "OTHER"


class ExtractedClaim(BaseModel):
    claim: str
    entities: list[Entity] = Field(default_factory=list)
    topic: str = "general"
    category: ClaimCategory = ClaimCategory.NEWS
    claim_type: str = "assertion"


class EvidenceItem(BaseModel):
    id: str
    text: str
    url: str = ""
    source_id: str = ""
    store: str
    score: float = 0.0
    title: str = ""
    domain: str = ""
    stance: Literal["supports", "refutes", "neutral"] = "neutral"
    raw: dict[str, Any] = Field(default_factory=dict)


class EvidencePackage(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float = 1.0


class KnowledgeGraphContext(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    supporting: list[str] = Field(default_factory=list)
    contradicting: list[str] = Field(default_factory=list)


class CredibilityScore(BaseModel):
    source_id: str
    url: str = ""
    domain: str = ""
    tier: SourceTier = SourceTier.UNKNOWN
    score: int = 20
    rationale: str = ""


class ReasoningStep(BaseModel):
    index: int
    title: str
    detail: str
    evidence_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)


class SourceRef(BaseModel):
    id: str
    title: str
    url: str
    domain: str
    tier: SourceTier
    score: int


class VerdictResult(BaseModel):
    verdict: VerdictLabel
    confidence: float = Field(ge=0, le=1)
    explanation: str
    sources: list[SourceRef] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    unverifiable_reason: str | None = None
    reasoning: list[ReasoningStep] = Field(default_factory=list)


class PipelineEvent(BaseModel):
    type: str
    message: str
    agent: str | None = None
    ts: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)


class FactCheckCreate(BaseModel):
    claim: str | None = None


class FactCheckSummary(BaseModel):
    id: str
    status: str
    original_input: str
    input_type: str
    verdict: VerdictLabel | None = None
    confidence: float | None = None
    category: str | None = None
    created_at: datetime
    agent_success: str = "0/6"


class FactCheckDossier(BaseModel):
    id: str
    status: str
    original_input: str
    input_type: str
    claim: ExtractedClaim | None = None
    verdict: VerdictResult | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    knowledge_graph: KnowledgeGraphContext | None = None
    agent_runs: list[dict[str, Any]] = Field(default_factory=list)
    events: list[PipelineEvent] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AnalyticsSummary(BaseModel):
    total: int = 0
    by_verdict: dict[str, int] = Field(default_factory=dict)
    avg_confidence: float = 0.0
    agent_success_rate: float = 0.0
    source_diversity: float = 0.0
    retrieval_accuracy: float = 0.0
    verdict_consistency: float = 0.0
    recent_traces: list[dict[str, Any]] = Field(default_factory=list)


class HealthStatus(BaseModel):
    ok: bool
    services: dict[str, str]


class SessionRequest(BaseModel):
    access_token: str | None = None
