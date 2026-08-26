from rag.document_loader import load_documents
from rag.chunker import chunk_documents
from rag.vector_store import VectorStore


def main():
    documents = load_documents("knowledge_base")

    chunks = chunk_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    vector_store = VectorStore(
        persist_directory="./data/chroma",
        collection_name="test_collection",
    )

    vector_store.add_documents(chunks)

    print(f"Chunks created: {len(chunks)}")
    print(f"Documents stored: {vector_store.count()}")

    query = "What does the company say about work from home?"

    results = vector_store.search(
        query=query,
        top_k=2,
    )

    print("\n--- Search Results ---")

    for index, document in enumerate(
        results["documents"][0],
        start=1,
    ):
        print(f"\nResult {index}:")
        print(document)

    print("\n--- Metadata ---")

    for index, metadata in enumerate(
        results["metadatas"][0],
        start=1,
    ):
        print(f"Result {index}: {metadata}")


if __name__ == "__main__":
    main()