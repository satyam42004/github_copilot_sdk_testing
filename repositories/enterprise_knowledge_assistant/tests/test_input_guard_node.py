from graph.nodes.input_guard import input_guard_node


def test_safe_question():
    state = {
        "question": "What is the work from home policy?",
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    result = input_guard_node(state)

    assert result["question"] == state["question"]

    print("SAFE QUESTION NODE TEST: PASSED")
    print(f"Validated question: {result['question']}")


def test_pii_question():
    state = {
        "question": "My email is employee@example.com. What is the leave policy?",
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    try:
        input_guard_node(state)

        print("PII QUESTION NODE TEST: FAILED")

    except Exception as exc:
        print("PII QUESTION NODE TEST: PASSED")
        print("PII was blocked before reaching the LLM.")
        print(f"Validation error: {exc}")


def main():
    print("Testing safe question...")
    test_safe_question()

    print("\nTesting PII question...")
    test_pii_question()


if __name__ == "__main__":
    main()