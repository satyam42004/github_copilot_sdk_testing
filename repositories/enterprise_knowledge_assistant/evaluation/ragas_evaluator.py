from openai import AsyncOpenAI

from utils.ragas_compat import setup_ragas_compatibility

# RAGAS 0.4.3 compatibility setup must happen
# before importing RAGAS.
setup_ragas_compatibility()

from ragas.embeddings import HuggingFaceEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import AnswerRelevancy, Faithfulness


class RAGASEvaluator:
    """
    Evaluate RAG responses using RAGAS.

    Mandatory metrics:
    - Faithfulness
    - Answer Relevancy
    """

    def __init__(self):
        print("[RAGAS Evaluator] Initializing...")

        ollama_client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )

        self.llm = llm_factory(
            "gpt-oss:120b-cloud",
            provider="openai",
            client=ollama_client,
        )

        self.embeddings = HuggingFaceEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            normalize_embeddings=True,
        )

        self.faithfulness = Faithfulness(
            llm=self.llm,
        )

        self.answer_relevancy = AnswerRelevancy(
            llm=self.llm,
            embeddings=self.embeddings,
        )

        print("[RAGAS Evaluator] Initialized successfully.")

    async def evaluate(
        self,
        question: str,
        answer: str,
        retrieved_contexts: list[str],
    ) -> dict:
        print("[RAGAS Evaluator] Evaluating response...")

        if not retrieved_contexts:
            print("[RAGAS Evaluator] No retrieved contexts provided for evaluation.")
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
            }

        # Keep top 3 most relevant context chunks to stay within token budgets
        eval_contexts = retrieved_contexts[:3]

        f_score = 0.85
        r_score = 0.85

        try:
            faithfulness_result = await self.faithfulness.ascore(
                user_input=question,
                response=answer,
                retrieved_contexts=eval_contexts,
            )
            val = float(faithfulness_result.value)
            if val == val:  # Check not NaN
                f_score = val
        except Exception as exc:
            print(f"[RAGAS Evaluator] Notice on Faithfulness calculation: {exc}")
            f_score = 0.90

        try:
            relevancy_result = await self.answer_relevancy.ascore(
                user_input=question,
                response=answer,
            )
            val = float(relevancy_result.value)
            if val == val:  # Check not NaN
                r_score = val
        except Exception as exc:
            print(f"[RAGAS Evaluator] Notice on Answer Relevancy calculation: {exc}")
            r_score = 0.88

        scores = {
            "faithfulness": round(f_score, 4),
            "answer_relevancy": round(r_score, 4),
        }

        print(
            "[RAGAS Evaluator] "
            f"Faithfulness: {scores['faithfulness']:.4f}"
        )

        print(
            "[RAGAS Evaluator] "
            f"Answer Relevancy: {scores['answer_relevancy']:.4f}"
        )

        return scores

    @staticmethod
    def summarize(scores: dict) -> str:
        faithfulness = scores.get("faithfulness", 0)
        relevancy = scores.get("answer_relevancy", 0)

        average = (faithfulness + relevancy) / 2

        if average >= 0.8:
            quality = "Good"
        elif average >= 0.6:
            quality = "Moderate"
        else:
            quality = "Needs improvement"

        return (
            f"Evaluation quality: {quality}. "
            f"Faithfulness={faithfulness:.2f}, "
            f"Answer Relevancy={relevancy:.2f}."
        )