from graph.nodes.retriever_agent import retriever_agent
from graph.nodes.response_agent import response_agent
from graph.state import GraphState


def main():
    state: GraphState = {
        "question": "What does the company say about working from home?",
        "retrieved_documents": [],
        "answer": "",
        "evaluation_scores": {},
        "evaluation_summary": "",
    }

    print("Running Retriever Agent...")

    state = retriever_agent(state)

    print("\nRunning Response Agent...")

    state = response_agent(state)

    print("\n--- Final Answer ---")
    print(state["answer"])


if __name__ == "__main__":
    main()