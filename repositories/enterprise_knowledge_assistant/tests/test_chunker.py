from rag.document_loader import load_documents
from rag.chunker import chunk_documents


def main():
    documents = load_documents("knowledge_base")
    chunks = chunk_documents(documents)

    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks created: {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {index} ---")
        print(chunk.page_content)
        print("Metadata:", chunk.metadata)


if __name__ == "__main__":
    main()