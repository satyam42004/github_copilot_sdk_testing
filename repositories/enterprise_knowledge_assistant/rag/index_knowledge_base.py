from rag.document_loader import load_documents
from rag.chunker import chunk_documents
from rag.vector_store import VectorStore


def index_knowledge_base() -> None:
    """
    Load, chunk, embed, and store the knowledge base
    in the production ChromaDB collection.
    """

    print("Loading documents...")

    documents = load_documents("knowledge_base")

    print(f"Documents loaded: {len(documents)}")

    print("Creating chunks...")

    chunks = chunk_documents(
        documents,
        chunk_size=500,
        chunk_overlap=50,
    )

    print(f"Chunks created: {len(chunks)}")

    print("Creating vector store...")

    vector_store = VectorStore(
        persist_directory="./data/chroma",
        collection_name="enterprise_knowledge",
    )

    print("Storing documents in ChromaDB...")

    vector_store.add_documents(chunks)

    print(
        f"Documents stored: {vector_store.count()}"
    )

    print("Knowledge base indexing completed.")


if __name__ == "__main__":
    index_knowledge_base()