from typing import Any

from app.graph.neo4j_client import find_relationships, query_graph
from app.mcp.runtime import serve


def register(server) -> None:
    @server.tool()
    def query_graph_tool(cypher_template: str, params: dict[str, Any] | None = None) -> list[dict]:
        return query_graph(cypher_template, params)

    @server.tool()
    def find_relationships_tool(entity: str, depth: int = 2) -> list[dict]:
        return find_relationships(entity, depth)


if __name__ == "__main__":
    serve("truthlens-neo4j", register)
