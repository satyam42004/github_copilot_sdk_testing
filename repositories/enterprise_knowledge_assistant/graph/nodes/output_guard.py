from graph.state import GraphState
from utils.guardrails.output_guard import OutputGuard


output_guard = OutputGuard()


def output_guard_node(state: GraphState) -> GraphState:
    """
    Validate the generated answer before it can leave
    the LangGraph workflow.

    If PII is detected, Guardrails raises an exception
    and the unsafe answer is not returned to the user.
    """

    answer = state["answer"]

    validated_answer = output_guard.validate(answer)

    return {
        **state,
        "answer": validated_answer,
    }