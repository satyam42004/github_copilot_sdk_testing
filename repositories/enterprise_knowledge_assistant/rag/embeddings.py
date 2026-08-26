from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """
    Wrapper around the Sentence Transformer embedding model.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.
        """

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
        )

        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """
        Generate an embedding for a single query.
        """

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
        )

        return embedding.tolist()