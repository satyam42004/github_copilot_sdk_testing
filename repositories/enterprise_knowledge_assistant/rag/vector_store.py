import chromadb
from langchain_core.documents import Document

from rag.embeddings import EmbeddingModel


from pathlib import Path

DEFAULT_CHROMA_DIR = str(Path(__file__).resolve().parent.parent / "data" / "chroma")


class VectorStore:
    """
    ChromaDB-based vector store for the enterprise knowledge base.
    """

    def __init__(
        self,
        persist_directory: str = DEFAULT_CHROMA_DIR,
        collection_name: str = "enterprise_knowledge",
    ):
        target_dir = Path(persist_directory)
        if not target_dir.is_absolute():
            # Check if relative to cwd exists, otherwise resolve relative to project root
            if not target_dir.exists():
                target_dir = Path(__file__).resolve().parent.parent / persist_directory
        resolved_path = str(target_dir.resolve())

        self.client = chromadb.PersistentClient(
            path=resolved_path
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name
        )

        self.embedding_model = EmbeddingModel()

    def add_documents(self, documents: list[Document]) -> None:
        """
        Generate embeddings and store documents in ChromaDB.
        """

        if not documents:
            return

        texts = [document.page_content for document in documents]

        embeddings = self.embedding_model.embed_documents(texts)

        ids = [
            f"doc_{index}"
            for index in range(len(documents))
        ]

        metadatas = [
            document.metadata
            for document in documents
        ]

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict:
        """
        Search the vector store using semantic similarity.
        """

        query_embedding = self.embedding_model.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        return results

    def count(self) -> int:
        """
        Return the number of documents stored in ChromaDB.
        """

        return self.collection.count()