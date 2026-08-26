from rag.document_loader import load_documents


def main():
    documents = load_documents("knowledge_base")

    print(f"Documents loaded: {len(documents)}")

    for index, document in enumerate(documents, start=1):
        print(f"\n--- Document {index} ---")
        print(document.page_content)
        print("Metadata:", document.metadata)


if __name__ == "__main__":
    main()