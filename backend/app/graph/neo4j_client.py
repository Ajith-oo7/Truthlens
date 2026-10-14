from __future__ import annotations

import logging
from typing import Any

from app.config import get_settings
from app.models.schemas import EvidenceItem, ExtractedClaim, GraphEdge, GraphNode, KnowledgeGraphContext
from app.tools.credibility import evaluate_source

logger = logging.getLogger("truthlens.neo4j")


def _driver():
    settings = get_settings()
    if not settings.neo4j_enabled:
        return None
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))
        driver.verify_connectivity()
        return driver
    except Exception as exc:
        logger.warning("Neo4j unavailable: %s", exc)
        return None


def query_graph(cypher_template: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    driver = _driver()
    if driver is None:
        return []
    allowed_prefix = ("MATCH ", "MERGE ", "CREATE CONSTRAINT")
    if not cypher_template.strip().upper().startswith(allowed_prefix):
        raise ValueError("Only MATCH/MERGE graph templates are allowed")
    with driver.session() as session:
        return [record.data() for record in session.run(cypher_template, params or {})]


def find_relationships(entity: str, depth: int = 2) -> list[dict[str, Any]]:
    return query_graph(
        "MATCH (n)-[r]-(m) WHERE toLower(n.name) CONTAINS toLower($entity) "
        "RETURN n, r, m LIMIT 50",
        {"entity": entity},
    )


def upsert_investigation(claim: ExtractedClaim, evidence: list[EvidenceItem]) -> KnowledgeGraphContext:
    nodes: list[GraphNode] = [
        GraphNode(id="claim", label=claim.claim[:80], type="Claim", properties={"topic": claim.topic})
    ]
    edges: list[GraphEdge] = []
    supporting: list[str] = []
    contradicting: list[str] = []
    topic_id = f"topic:{claim.topic}"
    nodes.append(GraphNode(id=topic_id, label=claim.topic, type="Topic"))
    edges.append(GraphEdge(source="claim", target=topic_id, type="MENTIONS"))

    for item in evidence:
        art_id = f"article:{item.id}"
        src_id = f"source:{item.domain or item.id}"
        nodes.append(GraphNode(id=art_id, label=item.title or item.id, type="Article", properties={"url": item.url}))
        cred = evaluate_source(item.url, item.domain)
        org_type = "Organization"
        nodes.append(GraphNode(id=src_id, label=item.domain or cred.domain, type=org_type, properties={"tier": cred.tier}))
        rel = "SUPPORTED_BY" if item.stance == "supports" else "REFUTED_BY" if item.stance == "refutes" else "REFERENCES"
        edges.append(GraphEdge(source="claim", target=art_id, type=rel, weight=item.score))
        edges.append(GraphEdge(source=art_id, target=src_id, type="PUBLISHED_BY"))
        if item.stance == "supports":
            supporting.append(art_id)
        elif item.stance == "refutes":
            contradicting.append(art_id)

    driver = _driver()
    if driver is not None:
        try:
            with driver.session() as session:
                session.run(
                    "MERGE (c:Claim {id: $id}) SET c.text = $text, c.topic = $topic",
                    {"id": claim.claim[:64], "text": claim.claim, "topic": claim.topic},
                )
                for edge in edges:
                    session.run(
                        "MERGE (a {id: $src}) MERGE (b {id: $dst}) "
                        f"MERGE (a)-[r:{edge.type}]->(b)",
                        {"src": edge.source, "dst": edge.target},
                    )
        except Exception as exc:
            logger.warning("Neo4j upsert failed: %s", exc)

    return KnowledgeGraphContext(nodes=nodes, edges=edges, supporting=supporting, contradicting=contradicting)
