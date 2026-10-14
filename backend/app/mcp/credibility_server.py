from typing import Any

from app.mcp.runtime import serve
from app.tools.credibility import calculate_score, evaluate_source


def register(server) -> None:
    @server.tool()
    def evaluate_source_tool(url: str, domain: str | None = None) -> dict:
        return evaluate_source(url, domain).model_dump()

    @server.tool()
    def calculate_score_tool(domain: str, metadata: dict[str, Any] | None = None) -> int:
        return calculate_score(domain, metadata)


if __name__ == "__main__":
    serve("truthlens-credibility", register)
