from graph.nodes.retriever_agent import retriever_agent
from graph.state import GraphState


def main():
    state: GraphState = {
        "question": "What does the company say about working from home?",
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    updated_state = retriever_agent(state)

    print("\n--- Test Result ---")
    print(f"Question: {updated_state['question']}")
    print(
        f"Documents retrieved: "
        f"{len(updated_state['retrieved_documents'])}"
    )

    for index, document in enumerate(
        updated_state["retrieved_documents"],
        start=1,
    ):
        print(f"\n--- Retrieved Document {index} ---")
        print(document.page_content)
        print(f"Metadata: {document.metadata}")


if __name__ == "__main__":
    main()