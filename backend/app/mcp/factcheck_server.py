from app.mcp.runtime import serve
from app.tools.factcheck import retrieve_fact_check, search_fact_checks


def register(server) -> None:
    @server.tool()
    def search_fact_checks_tool(query: str, language: str = "en") -> list[dict]:
        return [item.model_dump() for item in search_fact_checks(query, language)]

    @server.tool()
    def retrieve_fact_check_tool(fact_id: str) -> dict | None:
        return retrieve_fact_check(fact_id)


if __name__ == "__main__":
    serve("truthlens-factcheck", register)
