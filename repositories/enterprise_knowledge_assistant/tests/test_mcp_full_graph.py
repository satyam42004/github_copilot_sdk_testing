from graph.workflow import build_graph


def make_state(question: str) -> dict:
    return {
        "question": question,
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
        "mcp_action": "",
        "mcp_result": {},
    }


def run_test(
    graph,
    question: str,
    expected_action: str,
):
    print("\n" + "=" * 70)
    print(f"QUESTION: {question}")
    print("=" * 70)

    result = graph.invoke(
        make_state(question)
    )

    print(
        f"MCP ACTION: "
        f"{result.get('mcp_action', '')}"
    )

    print(
        f"MCP RESULT: "
        f"{result.get('mcp_result', {})}"
    )

    print(
        f"ANSWER:\n"
        f"{result.get('answer', '')}"
    )

    assert (
        result.get("mcp_action")
        == expected_action
    ), (
        f"Expected MCP action "
        f"'{expected_action}', "
        f"got '{result.get('mcp_action')}'"
    )

    return result


def main():
    print(
        "\nStarting full LangGraph "
        "MCP integration test..."
    )

    graph = build_graph()

    # ==================================================
    # 1. NORMAL RAG REQUEST
    # ==================================================

    rag_result = graph.invoke(
        make_state(
            "How many annual leave days does a "
            "full-time employee receive?"
        )
    )

    print("\nRAG TEST")
    print("-" * 70)

    print(
        f"MCP ACTION: "
        f"{rag_result.get('mcp_action', '')}"
    )

    print(
        f"ANSWER:\n"
        f"{rag_result.get('answer', '')}"
    )

    # --------------------------------------------------
    # MCP should NOT execute for a knowledge request.
    #
    # Since the MCP node is skipped by the graph,
    # mcp_action remains "".
    # --------------------------------------------------

    assert (
        rag_result.get("mcp_action", "")
        in ("", "none")
    ), (
        "Normal knowledge request "
        "incorrectly triggered MCP."
    )

    # --------------------------------------------------
    # Verify that RAG returned the expected answer.
    # --------------------------------------------------

    assert (
        "20" in rag_result.get(
            "answer",
            "",
        )
    ), (
        "Expected annual leave "
        "information was not found."
    )

    print(
        "RAG TEST: PASSED"
    )

    # ==================================================
    # 2. CREATE TICKET
    # ==================================================

    create_result = run_test(
        graph,
        (
            "Create a high priority support ticket "
            "because employees cannot connect to "
            "the corporate VPN."
        ),
        "create_ticket",
    )

    # --------------------------------------------------
    # Verify ticket creation
    # --------------------------------------------------

    create_mcp_result = (
        create_result.get(
            "mcp_result",
            {},
        )
    )

    assert (
        create_mcp_result.get(
            "success"
        )
        is True
    ), "Ticket creation failed."

    ticket_id = create_mcp_result.get(
        "ticket_id"
    )

    assert ticket_id, (
        "Created ticket does not contain "
        "a ticket ID."
    )

    print(
        f"\nCreated ticket: {ticket_id}"
    )

    print(
        "CREATE TICKET TEST: PASSED"
    )

    # ==================================================
    # 3. GET TICKET
    # ==================================================

    get_result = run_test(
        graph,
        f"Give me the details of {ticket_id}.",
        "get_ticket",
    )

    # --------------------------------------------------
    # Verify ticket retrieval
    # --------------------------------------------------

    get_mcp_result = (
        get_result.get(
            "mcp_result",
            {},
        )
    )

    assert (
        get_mcp_result.get(
            "success"
        )
        is True
    ), "Ticket retrieval failed."

    assert (
        get_mcp_result.get(
            "ticket_id"
        )
        == ticket_id
    ), (
        "Retrieved ticket ID does not "
        "match the created ticket."
    )

    print(
        "GET TICKET TEST: PASSED"
    )

    # ==================================================
    # 4. SEARCH TICKETS
    # ==================================================

    search_result = run_test(
        graph,
        "Find all support tickets related to VPN.",
        "search_tickets",
    )

    # --------------------------------------------------
    # MCP search returns:
    #
    # {
    #     "result": [...]
    # }
    # --------------------------------------------------

    search_mcp_result = (
        search_result.get(
            "mcp_result",
            {},
        )
    )

    search_results = (
        search_mcp_result.get(
            "result",
            [],
        )
    )

    assert isinstance(
        search_results,
        list,
    ), (
        "Search result is not a list."
    )

    assert len(search_results) > 0, (
        "Expected VPN tickets, "
        "but search returned none."
    )

    print(
        f"\nFound "
        f"{len(search_results)} "
        f"VPN ticket(s)."
    )

    print(
        "SEARCH TICKETS TEST: PASSED"
    )

    # ==================================================
    # FINAL RESULT
    # ==================================================

    print("\n" + "=" * 70)
    print(
        "FULL LANGGRAPH MCP "
        "INTEGRATION TEST: PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()