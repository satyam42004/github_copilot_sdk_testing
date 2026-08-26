from graph.nodes.evaluator_agent import evaluator_agent


def main():
    state = {
        "question": "What does the company say about working from home?",
        "retrieved_documents": [
            type(
                "Document",
                (),
                {
                    "page_content": (
                        "Employees are expected to follow "
                        "company policies related to work from home."
                    )
                },
            )()
        ],
        "answer": (
            "Employees are expected to follow the company's "
            "work-from-home policy."
        ),
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    print("\nStarting RAGAS evaluator test...")

    result = evaluator_agent(state)

    scores = result["evaluation_scores"]

    assert scores, "No evaluation scores were produced."
    assert "faithfulness" in scores
    assert "answer_relevancy" in scores
    assert 0 <= scores["faithfulness"] <= 1
    assert 0 <= scores["answer_relevancy"] <= 1
    assert result["evaluation_summary"], "No evaluation summary was produced."

    print("\n--- Evaluation Result ---")
    print(f"Scores: {scores}")
    print(f"Summary: {result['evaluation_summary']}")
    print("\nRAGAS EVALUATOR TEST: PASSED")


if __name__ == "__main__":
    main()