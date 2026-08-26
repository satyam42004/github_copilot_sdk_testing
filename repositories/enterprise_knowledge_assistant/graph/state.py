from typing import TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    question: str
    retrieved_documents: list[Document]
    answer: str

    evaluation_scores: dict
    evaluation_summary: str

    # MCP integration
    mcp_action: str
    mcp_result: dict