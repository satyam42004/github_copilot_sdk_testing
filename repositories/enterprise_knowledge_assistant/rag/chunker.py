from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Document]:
    """
    Split documents into smaller chunks for retrieval.

    Args:
        documents: Documents loaded from the knowledge base.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Number of characters shared between chunks.

    Returns:
        A list of chunked LangChain Document objects.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = text_splitter.split_documents(documents)

    return chunks