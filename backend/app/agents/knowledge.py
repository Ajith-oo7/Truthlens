from app.graph.neo4j_client import upsert_investigation
from app.models.schemas import EvidenceItem, ExtractedClaim, KnowledgeGraphContext


def run_knowledge_graph(claim: ExtractedClaim, evidence: list[EvidenceItem]) -> KnowledgeGraphContext:
    return upsert_investigation(claim, evidence)
