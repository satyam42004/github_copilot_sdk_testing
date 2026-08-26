from graph.state import GraphState


def main():
    state: GraphState = {
        "question": "What is the work from home policy?",
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    print("GraphState created successfully.")
    print(f"Question: {state['question']}")
    print(f"Retrieved documents: {state['retrieved_documents']}")
    print(f"Answer: {state['answer']}")
    print(f"Evaluation scores: {state['evaluation_scores']}")
    print(f"Evaluation summary: {state['evaluation_summary']}")


if __name__ == "__main__":
    main()