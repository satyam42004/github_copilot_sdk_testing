from graph.workflow import build_graph


def main():
    graph = build_graph()

    initial_state = {
        "question": (
            "Create a high priority support ticket because "
            "employees cannot connect to the corporate VPN."
        ),
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
        "mcp_action": "",
        "mcp_result": {},
    }

    print("\nStarting MCP end-to-end test...")

    result = graph.invoke(initial_state)

    print("\n--- MCP Result ---")

    print(f"Question: {result['question']}")

    print("\nFinal answer:")
    print(result["answer"])

    print(f"\nMCP action: {result['mcp_action']}")
    print(f"MCP result: {result['mcp_result']}")

    # --------------------------------------------------
    # Assertions
    # --------------------------------------------------

    assert result["mcp_action"] == "create_ticket"

    assert result["mcp_result"]

    assert result["mcp_result"]["success"] is True

    assert result["mcp_result"]["ticket_id"].startswith(
        "TKT-"
    )

    assert result["mcp_result"]["title"] == (
        "VPN connection issue"
    )

    assert result["mcp_result"]["priority"] == "high"

    assert result["mcp_result"]["status"] == "open"

    # Verify final user-facing answer

    assert (
        "created a support ticket" in result["answer"].lower()
        or "support ticket" in result["answer"].lower()
    )

    assert result["mcp_result"]["ticket_id"] in (
        result["answer"]
    )

    assert "VPN connection issue" in result["answer"]

    assert "High" in result["answer"]

    assert "Open" in result["answer"]

    print("\nMCP END-TO-END TEST: PASSED")


if __name__ == "__main__":
    main()