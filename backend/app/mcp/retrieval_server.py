from app.mcp.runtime import serve
from app.tools.retrieval import search_chromadb, search_elasticsearch, search_qdrant


def register(server) -> None:
    @server.tool()
    def search_chromadb_tool(query: str) -> list[dict]:
        return [item.model_dump() for item in search_chromadb(query)]

    @server.tool()
    def search_qdrant_tool(query: str) -> list[dict]:
        return [item.model_dump() for item in search_qdrant(query)]

    @server.tool()
    def search_elasticsearch_tool(query: str) -> list[dict]:
        return [item.model_dump() for item in search_elasticsearch(query)]


if __name__ == "__main__":
    serve("truthlens-retrieval", register)
