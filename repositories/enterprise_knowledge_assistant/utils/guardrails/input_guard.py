from guardrails import Guard

from utils.guardrails.pii_validator import (
    PIIValidator,
)


class InputGuard:
    """
    Guardrails-based input protection.

    User input is inspected for PII before it is sent
    to any LLM.

    Detected PII is sanitized rather than blocking
    the entire request.
    """

    def __init__(self):
        validator = PIIValidator(
            on_fail="fix",
        )

        self.guard = Guard().use(validator)

    def validate(self, user_input: str) -> str:
        """
        Validate and sanitize user input.

        Returns the original input when no PII is found.

        Returns a sanitized version when PII is detected.
        """

        result = self.guard.validate(user_input)

        return result.validated_output