from graph.state import GraphState
from rag.retriever import KnowledgeRetriever


def retriever_agent(state: GraphState) -> GraphState:
    """
    Retrieve relevant documents for the user's question.
    """

    question = state["question"]

    print("\n[Retriever Agent] Starting...")
    print(f"[Retriever Agent] Question: {question}")

    retriever = KnowledgeRetriever()

    documents = retriever.retrieve(
        query=question,
        top_k=5,
    )

    print(
        f"[Retriever Agent] Retrieved {len(documents)} documents."
    )

    return {
        **state,
        "retrieved_documents": documents,
    }