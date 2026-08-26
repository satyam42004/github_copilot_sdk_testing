from rag.embeddings import EmbeddingModel


def main():
    embedding_model = EmbeddingModel()

    text = "Employees can work remotely according to company policy."

    embedding = embedding_model.embed_query(text)

    print(f"Embedding type: {type(embedding)}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 10 values: {embedding[:10]}")


if __name__ == "__main__":
    main()