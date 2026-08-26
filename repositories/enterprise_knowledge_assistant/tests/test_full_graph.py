from graph.workflow import build_graph


def main():
    graph = build_graph()

    initial_state = {
        "question": (
            "My email is employee@example.com. "
            "What does the company say about working from home?"
        ),
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    print("\nStarting PII protection test...")

    try:
        graph.invoke(initial_state)

        print("\nPII TEST: FAILED")
        print("The graph allowed private information to continue.")

    except Exception as exc:
        print("\nPII TEST: PASSED")
        print("Private information was blocked before the LLM.")
        print(f"Validation error: {exc}")


if __name__ == "__main__":
    main()