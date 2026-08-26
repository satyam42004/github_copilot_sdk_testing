from rag.retriever import KnowledgeRetriever


def main():
    retriever = KnowledgeRetriever()

    query = "What does the company say about working from home?"

    documents = retriever.retrieve(
        query=query,
        top_k=2,
    )

    print(f"Query: {query}")
    print(f"Documents retrieved: {len(documents)}")

    for index, document in enumerate(documents, start=1):
        print(f"\n--- Retrieved Document {index} ---")
        print(document.page_content)
        print("Metadata:", document.metadata)


if __name__ == "__main__":
    main()