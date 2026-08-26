import asyncio
import re

from graph.state import GraphState
from mcp_client.ticket_client import (
    create_ticket,
    get_ticket,
    search_tickets,
)


def extract_ticket_title(question: str) -> str:
    """
    Generate a simple meaningful ticket title from the user's request.
    """

    question_lower = question.lower()

    if "vpn" in question_lower:
        return "VPN connection issue"

    if "password" in question_lower:
        return "Password issue"

    if "login" in question_lower:
        return "Login issue"

    if "email" in question_lower:
        return "Email issue"

    if "network" in question_lower:
        return "Network issue"

    if "laptop" in question_lower:
        return "Laptop issue"

    return "Enterprise support request"


def detect_priority(question: str) -> str:
    """
    Detect ticket priority from the user's request.
    """

    question_lower = question.lower()

    if "critical" in question_lower:
        return "critical"

    if (
        "high priority" in question_lower
        or "high-priority" in question_lower
        or (
            "high" in question_lower
            and "priority" in question_lower
        )
    ):
        return "high"

    if (
        "low priority" in question_lower
        or "low-priority" in question_lower
        or (
            "low" in question_lower
            and "priority" in question_lower
        )
    ):
        return "low"

    return "medium"


def extract_ticket_id(question: str) -> str | None:
    """
    Extract a ticket ID such as TKT-0001 from the user's request.
    """

    match = re.search(
        r"\bTKT-\d+\b",
        question,
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(0).upper()


def detect_mcp_action(question: str) -> str:
    """
    Determine which MCP operation the user requested.

    Returns:
        create_ticket
        get_ticket
        search_tickets
        none
    """

    question_lower = question.lower().strip()

    # --------------------------------------------------
    # GET TICKET
    # --------------------------------------------------

    ticket_id = extract_ticket_id(question)

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

    # If the user mentions a specific ticket ID together
    # with an information-related word, this is GET.
    if (
        ticket_id
        and any(
            keyword in question_lower
            for keyword in get_keywords
        )
    ):
        return "get_ticket"

    # --------------------------------------------------
    # SEARCH TICKETS
    # --------------------------------------------------

    search_keywords = [
        "search",
        "find",
        "look for",
        "list",
    ]

    ticket_search_keywords = [
        "ticket",
        "tickets",
        "support ticket",
        "support tickets",
    ]

    if (
        any(
            keyword in question_lower
            for keyword in search_keywords
        )
        and any(
            keyword in question_lower
            for keyword in ticket_search_keywords
        )
    ):
        return "search_tickets"

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

    if any(
        re.search(
            pattern,
            question_lower,
        )
        for pattern in create_patterns
    ):
        return "create_ticket"

    return "none"    """
    Determine which MCP operation the user requested.

    Returns:
        create_ticket
        get_ticket
        search_tickets
        none
    """

    question_lower = question.lower()

    # --------------------------------------------------
    # GET TICKET
    # --------------------------------------------------

    ticket_id = extract_ticket_id(question)

    get_keywords = [
        "get ticket",
        "get the ticket",
        "ticket details",
        "details of ticket",
        "details for ticket",
        "information about ticket",
        "information on ticket",
        "status of ticket",
        "status for ticket",
        "priority of ticket",
        "show ticket",
        "show me ticket",
        "tell me about ticket",
    ]

    if ticket_id and any(
        keyword in question_lower
        for keyword in get_keywords
    ):
        return "get_ticket"

    # --------------------------------------------------
    # SEARCH TICKETS
    # --------------------------------------------------

    search_keywords = [
        "search tickets",
        "search ticket",
        "find tickets",
        "find ticket",
        "look for tickets",
        "look for ticket",
        "list tickets",
        "list ticket",
        "find all tickets",
        "search support tickets",
        "find support tickets",
    ]

    if any(
        keyword in question_lower
        for keyword in search_keywords
    ):
        return "search_tickets"

    # --------------------------------------------------
    # CREATE TICKET
    # --------------------------------------------------

    create_keywords = [
        "create a ticket",
        "create ticket",
        "raise a ticket",
        "raise ticket",
        "open a ticket",
        "open ticket",
        "report an issue",
        "report issue",
        "it ticket",
        "support ticket",
    ]

    if any(
        keyword in question_lower
        for keyword in create_keywords
    ):
        return "create_ticket"

    return "none"


def extract_search_query(question: str) -> str:
    """
    Extract a useful search query from a natural-language
    ticket search request.

    For example:

    'Find all support tickets related to VPN'
        -> 'VPN'

    'Search for tickets related to laptop problems'
        -> 'laptop problems'
    """

    question_lower = question.lower()

    patterns = [
        r"(?:related to|about|regarding|concerning)\s+(.+?)(?:\?|$)",
        r"(?:for|on)\s+(.+?)(?:\?|$)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            question_lower,
        )

        if match:
            query = match.group(1).strip()

            # Remove common trailing words.
            query = re.sub(
                r"\b(tickets?|issues?)$",
                "",
                query,
            ).strip()

            if query:
                return query

    # Fallback: remove common search phrases.
    query = question_lower

    removable_phrases = [
        "find all support tickets",
        "find support tickets",
        "search support tickets",
        "find all tickets",
        "find tickets",
        "search tickets",
        "search ticket",
        "find ticket",
        "look for tickets",
        "look for ticket",
        "list tickets",
        "list ticket",
    ]

    for phrase in removable_phrases:
        query = query.replace(
            phrase,
            "",
        )

    query = query.strip(
        " .?!"
    )

    return query or question


def extract_structured_content(result) -> dict:
    """
    Extract structured MCP output safely.
    """

    structured_content = getattr(
        result,
        "structuredContent",
        None,
    )

    if isinstance(
        structured_content,
        dict,
    ):
        return structured_content

    return {}


def format_ticket_result(
    ticket: dict,
) -> str:
    """
    Format a single ticket for the final answer.
    """

    ticket_id = ticket.get(
        "ticket_id",
        "Unknown",
    )

    title = ticket.get(
        "title",
        "Unknown",
    )

    description = ticket.get(
        "description",
        "No description available.",
    )

    priority = ticket.get(
        "priority",
        "Unknown",
    )

    status = ticket.get(
        "status",
        "Unknown",
    )

    return (
        "🎫 **Ticket Information**\n\n"
        f"**Ticket ID:** {ticket_id}\n\n"
        f"**Title:** {title}\n\n"
        f"**Description:** {description}\n\n"
        f"**Priority:** {priority.title()}\n\n"
        f"**Status:** {status.title()}"
    )


def mcp_agent(state: GraphState) -> GraphState:
    """
    Handle MCP-related user requests.

    Supported MCP operations:

    1. create_ticket
    2. get_ticket
    3. search_tickets

    The existing create-ticket behavior is preserved while
    adding retrieval and search capabilities.
    """

    print("\n[MCP Agent] Starting...")

    question = state["question"]

    # --------------------------------------------------
    # Detect MCP operation
    # --------------------------------------------------

    action = detect_mcp_action(question)

    print(
        f"[MCP Agent] Detected action: {action}"
    )

    # --------------------------------------------------
    # No MCP request
    # --------------------------------------------------

    if action == "none":

        print(
            "[MCP Agent] No MCP request detected."
        )

        return {
            **state,
            "mcp_action": "none",
            "mcp_result": {},
        }

    # --------------------------------------------------
    # GET TICKET
    # --------------------------------------------------

    if action == "get_ticket":

        ticket_id = extract_ticket_id(
            question
        )

        if not ticket_id:

            return {
                **state,
                "mcp_action": "get_ticket",
                "mcp_result": {
                    "success": False,
                    "error": (
                        "No valid ticket ID was found."
                    ),
                },
                "answer": (
                    "I could not find a valid ticket ID "
                    "in your request. Please provide a "
                    "ticket ID such as TKT-0001."
                ),
            }

        print(
            f"[MCP Agent] Retrieving ticket: {ticket_id}"
        )

        result = asyncio.run(
            get_ticket(ticket_id)
        )

        structured_content = (
            extract_structured_content(result)
        )

        print(
            "[MCP Agent] Ticket retrieved:",
            structured_content,
        )

        if structured_content.get("success"):

            answer = format_ticket_result(
                structured_content
            )

        else:

            error_message = structured_content.get(
                "error",
                "Ticket was not found.",
            )

            answer = (
                "I could not retrieve the ticket.\n\n"
                f"Reason: {error_message}"
            )

        return {
            **state,
            "answer": answer,
            "mcp_action": "get_ticket",
            "mcp_result": structured_content,
        }

    # --------------------------------------------------
    # SEARCH TICKETS
    # --------------------------------------------------

    if action == "search_tickets":

        search_query = extract_search_query(
            question
        )

        print(
            f"[MCP Agent] Searching tickets for: "
            f"{search_query}"
        )

        result = asyncio.run(
            search_tickets(search_query)
        )

        structured_content = (
            extract_structured_content(result)
        )

        print(
            "[MCP Agent] Search result:",
            structured_content,
        )

        # --------------------------------------------------
        # MCP search responses may contain a list directly
        # rather than a success wrapper.
        # --------------------------------------------------

        tickets = []

        if isinstance(
            structured_content,
            list,
        ):
            tickets = structured_content

        elif isinstance(
            structured_content.get("result"),
            list,
        ):
            tickets = structured_content["result"]

        elif isinstance(
            structured_content.get("tickets"),
            list,
        ):
            tickets = structured_content["tickets"]

        elif isinstance(
             structured_content.get("results"),
            list,
        ):
             tickets = structured_content["results"]
        # --------------------------------------------------
        # Handle search results
        # --------------------------------------------------

        if tickets:

            lines = [
                "🎫 **Ticket Search Results**\n",
                f"Search query: **{search_query}**\n",
                f"Found **{len(tickets)}** ticket(s).\n",
            ]

            for ticket in tickets:

                ticket_id = ticket.get(
                    "ticket_id",
                    "Unknown",
                )

                title = ticket.get(
                    "title",
                    "Unknown",
                )

                priority = ticket.get(
                    "priority",
                    "Unknown",
                )

                status = ticket.get(
                    "status",
                    "Unknown",
                )

                lines.append(
                    "\n"
                    f"**{ticket_id}** — {title}\n"
                    f"Priority: {priority.title()} | "
                    f"Status: {status.title()}"
                )

            answer = "\n".join(lines)

        else:

            answer = (
                f"I could not find any support tickets "
                f"matching **{search_query}**."
            )

        return {
            **state,
            "answer": answer,
            "mcp_action": "search_tickets",
            "mcp_result": structured_content,
        }

    # --------------------------------------------------
    # CREATE TICKET
    # --------------------------------------------------

    if action == "create_ticket":

        print(
            "[MCP Agent] Ticket request detected."
        )

        # --------------------------------------------------
        # Detect priority
        # --------------------------------------------------

        priority = detect_priority(
            question
        )

        print(
            f"[MCP Agent] Detected priority: "
            f"{priority}"
        )

        # --------------------------------------------------
        # Generate title
        # --------------------------------------------------

        title = extract_ticket_title(
            question
        )

        print(
            f"[MCP Agent] Ticket title: {title}"
        )

        # --------------------------------------------------
        # Call MCP create_ticket
        # --------------------------------------------------

        print(
            "[MCP Agent] Calling MCP "
            "create_ticket tool..."
        )

        result = asyncio.run(
            create_ticket(
                title=title,
                description=question,
                priority=priority,
            )
        )

        structured_content = (
            extract_structured_content(result)
        )

        print(
            "[MCP Agent] Ticket created:",
            structured_content,
        )

        # --------------------------------------------------
        # Update final answer
        # --------------------------------------------------

        if structured_content.get(
            "success"
        ):

            ticket_id = structured_content.get(
                "ticket_id",
                "Unknown",
            )

            ticket_title = structured_content.get(
                "title",
                title,
            )

            ticket_priority = structured_content.get(
                "priority",
                priority,
            )

            ticket_status = structured_content.get(
                "status",
                "open",
            )

            ticket_message = (
                "\n\n"
                "I have created a support ticket "
                "for you.\n\n"
                f"Ticket ID: {ticket_id}\n"
                f"Title: {ticket_title}\n"
                f"Priority: {ticket_priority.title()}\n"
                f"Status: {ticket_status.title()}"
            )

            answer = (
                state.get(
                    "answer",
                    "",
                )
                + ticket_message
            )

        else:

            error_message = structured_content.get(
                "error",
                "Unknown MCP error.",
            )

            answer = (
                state.get(
                    "answer",
                    "",
                )
                + "\n\n"
                "I could not create the support "
                "ticket. "
                f"Reason: {error_message}"
            )

        return {
            **state,
            "answer": answer,
            "mcp_action": "create_ticket",
            "mcp_result": structured_content,
        }

    # --------------------------------------------------
    # Safety fallback
    # --------------------------------------------------

    return {
        **state,
        "mcp_action": "none",
        "mcp_result": {},
    }