from graph.nodes.output_guard import output_guard_node


def test_safe_answer():
    state = {
        "question": "What is the work from home policy?",
        "retrieved_documents": [],
        "answer": (
            "Employees are expected to follow the "
            "latest approved work-from-home policy."
        ),
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    result = output_guard_node(state)

    assert result["answer"] == state["answer"]

    print("SAFE ANSWER NODE TEST: PASSED")
    print(f"Validated answer: {result['answer']}")


def test_pii_answer():
    state = {
        "question": "What is the work from home policy?",
        "retrieved_documents": [],
        "answer": (
            "The employee's email address is "
            "john.doe@example.com."
        ),
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    try:
        output_guard_node(state)

        print("PII ANSWER NODE TEST: FAILED")

    except Exception as exc:
        print("PII ANSWER NODE TEST: PASSED")
        print("PII was blocked before reaching the user.")
        print(f"Validation error: {exc}")


def main():
    print("Testing safe answer...")
    test_safe_answer()

    print("\nTesting PII answer...")
    test_pii_answer()


if __name__ == "__main__":
    main()