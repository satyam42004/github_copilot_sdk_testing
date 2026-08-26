import re

from graph.state import GraphState


def request_router(state: GraphState) -> str:
    """
    Route the user's request to either the RAG pipeline
    or the MCP action pipeline.

    Returns:
        "knowledge" -> RAG pipeline
        "action"    -> MCP pipeline
    """

    question = state["question"].lower().strip()

    # --------------------------------------------------
    # Ticket ID detection
    # --------------------------------------------------

    has_ticket_id = bool(
        re.search(r"\btkt-\d+\b", question)
    )

    # --------------------------------------------------
    # CREATE TICKET
    # --------------------------------------------------

    create_patterns = [
        r"\bcreate\b.*\bticket\b",
        r"\braise\b.*\bticket\b",
        r"\bopen\b.*\bticket\b",
        r"\breport\b.*\bissue\b",
        r"\breport\b.*\bproblem\b",
    ]

    is_create_request = any(
        re.search(pattern, question)
        for pattern in create_patterns
    )

    # --------------------------------------------------
    # GET TICKET
    # --------------------------------------------------

    get_keywords = [
        "get",
        "details",
        "detail",
        "information",
        "info",
        "status",
        "priority",
        "show",
        "tell me",
    ]

    is_get_request = (
        has_ticket_id
        and any(
            keyword in question
            for keyword in get_keywords
        )
    )

    # --------------------------------------------------
    # SEARCH TICKETS
    # --------------------------------------------------

    search_keywords = [
        "search",
        "find",
        "look for",
        "list",
    ]

    ticket_keywords = [
        "ticket",
        "tickets",
        "support ticket",
        "support tickets",
    ]

    is_search_request = (
        any(
            keyword in question
            for keyword in search_keywords
        )
        and any(
            keyword in question
            for keyword in ticket_keywords
        )
    )

    # --------------------------------------------------
    # MCP ACTION ROUTE
    # --------------------------------------------------

    if (
        is_create_request
        or is_get_request
        or is_search_request
    ):
        print(
            "[Router] Request classified as: ACTION"
        )

        return "action"

    # --------------------------------------------------
    # DEFAULT RAG ROUTE
    # --------------------------------------------------

    print(
        "[Router] Request classified as: KNOWLEDGE"
    )

    return "knowledge"