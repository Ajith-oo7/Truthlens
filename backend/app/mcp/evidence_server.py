from app.mcp.runtime import serve
from app.tools.evidence import retrieve_sources, search_articles, search_web


def register(server) -> None:
    @server.tool()
    def search_web_tool(query: str) -> list[dict]:
        return [item.model_dump() for item in search_web(query)]

    @server.tool()
    def search_articles_tool(query: str) -> list[dict]:
        return [item.model_dump() for item in search_articles(query)]

    @server.tool()
    def retrieve_sources_tool(urls: list[str]) -> list[dict]:
        return retrieve_sources(urls)


if __name__ == "__main__":
    serve("truthlens-evidence", register)
