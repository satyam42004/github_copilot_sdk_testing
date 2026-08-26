from graph.workflow import build_graph


def main():
    graph = build_graph()

    initial_state = {
        "question": "What does the company say about working from home?",
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    print("\nStarting safe end-to-end test...")

    result = graph.invoke(initial_state)

    print("\n--- Final Result ---")
    print(f"Question: {result['question']}")
    print(f"Documents retrieved: {len(result['retrieved_documents'])}")
    print(f"Answer: {result['answer']}")
    print(f"Evaluation scores: {result['evaluation_scores']}")
    print(f"Evaluation summary: {result['evaluation_summary']}")

    assert result["retrieved_documents"], "No documents were retrieved."
    assert result["answer"], "No answer was generated."
    assert result["evaluation_scores"], "No evaluation scores were produced."
    assert "faithfulness" in result["evaluation_scores"]
    assert "answer_relevancy" in result["evaluation_scores"]
    assert result["evaluation_summary"], "No evaluation summary was produced."

    print("\nSAFE END-TO-END TEST: PASSED")


if __name__ == "__main__":
    main()