from pathlib import Path

from langchain_core.documents import Document


def load_documents(knowledge_base_path: str) -> list[Document]:
    """
    Load all text documents from the knowledge base.
    """

    knowledge_base = Path(knowledge_base_path)
    if not knowledge_base.is_absolute() and not knowledge_base.exists():
        fallback_path = Path(__file__).resolve().parent.parent / knowledge_base_path
        if fallback_path.exists():
            knowledge_base = fallback_path

    documents = []

    for file_path in knowledge_base.rglob("*.txt"):
        text = file_path.read_text(encoding="utf-8")

        document = Document(
            page_content=text,
            metadata={
                "source": str(file_path)
            }
        )

        documents.append(document)

    return documents