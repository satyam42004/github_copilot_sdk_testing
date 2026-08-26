from graph.state import GraphState
from utils.guardrails.input_guard import InputGuard


input_guard = InputGuard()


def input_guard_node(state: GraphState) -> GraphState:
    """
    Validate the user's question before it reaches
    the Retriever/Response pipeline.

    If PII is detected, Guardrails raises an exception
    and the graph stops before the LLM is called.
    """

    question = state["question"]

    validated_question = input_guard.validate(question)
    # print(f"[Input Guard] Sanitized question: {validated_question}")
    return {
        **state,
        "question": validated_question,
    }