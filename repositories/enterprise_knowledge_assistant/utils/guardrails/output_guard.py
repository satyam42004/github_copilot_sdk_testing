from guardrails import Guard

from utils.guardrails.pii_validator import PIIValidator


class OutputGuard:
    """
    Validates the final LLM response before it is returned
    to the user.

    If PII is detected, the response is blocked.
    """

    def __init__(self):
        validator = PIIValidator(
            on_fail="exception",
        )

        self.guard = Guard().use(validator)

    def validate(self, response: str) -> str:
        """
        Validate the generated response.

        Returns:
            The original response if it passes validation.

        Raises:
            Exception if PII is detected.
        """

        result = self.guard.validate(response)

        return result.validated_output