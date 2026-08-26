from langgraph.graph import END, START, StateGraph

from graph.state import GraphState

from graph.nodes.input_guard import input_guard_node
from graph.nodes.router import request_router
from graph.nodes.retriever_agent import retriever_agent
from graph.nodes.response_agent import response_agent
from graph.nodes.output_guard import output_guard_node
from graph.nodes.evaluator_agent import evaluator_agent
from graph.nodes.mcp_agent import mcp_agent


def build_graph():
    """
    Build the Enterprise Knowledge Assistant LangGraph workflow.
    """

    workflow = StateGraph(GraphState)

    # --------------------------------------------------
    # Guardrail nodes
    # --------------------------------------------------

    workflow.add_node(
        "input_guard",
        input_guard_node,
    )

    workflow.add_node(
        "output_guard",
        output_guard_node,
    )

    # --------------------------------------------------
    # RAG nodes
    # --------------------------------------------------

    workflow.add_node(
        "retriever",
        retriever_agent,
    )

    workflow.add_node(
        "response",
        response_agent,
    )

    workflow.add_node(
        "evaluator",
        evaluator_agent,
    )

    # --------------------------------------------------
    # MCP node
    # --------------------------------------------------

    workflow.add_node(
        "mcp_agent",
        mcp_agent,
    )

    # --------------------------------------------------
    # START → Input Guard
    # --------------------------------------------------

    workflow.add_edge(
        START,
        "input_guard",
    )

    # --------------------------------------------------
    # Input Guard → Router
    # --------------------------------------------------

    workflow.add_conditional_edges(
        "input_guard",
        request_router,
        {
            "knowledge": "retriever",
            "action": "mcp_agent",
        },
    )

    # --------------------------------------------------
    # RAG pipeline
    # --------------------------------------------------

    workflow.add_edge(
        "retriever",
        "response",
    )

    workflow.add_edge(
        "response",
        "output_guard",
    )

    workflow.add_edge(
        "output_guard",
        "evaluator",
    )

    workflow.add_edge(
        "evaluator",
        END,
    )

    # --------------------------------------------------
    # MCP pipeline
    # --------------------------------------------------

    workflow.add_edge(
        "mcp_agent",
        END,
    )

    return workflow.compile()