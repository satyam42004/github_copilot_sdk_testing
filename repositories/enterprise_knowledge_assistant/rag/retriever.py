from langchain_core.documents import Document

from rag.vector_store import VectorStore


class KnowledgeRetriever:
    """
    Retrieves relevant documents from the enterprise knowledge base.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        collection_name: str = "enterprise_knowledge",
    ):
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[Document]:
        """
        Retrieve the most relevant documents for a query.
        """

        results = self.vector_store.search(
            query=query,
            top_k=top_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        retrieved_documents = []

        for content, metadata in zip(documents, metadatas):
            retrieved_documents.append(
                Document(
                    page_content=content,
                    metadata=metadata,
                )
            )

        return retrieved_documents