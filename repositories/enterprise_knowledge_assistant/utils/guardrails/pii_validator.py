from typing import Any

from guardrails.validators import (
    Validator,
    PassResult,
    FailResult,
)
from guardrails.validator_base import register_validator

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from utils.guardrails.presidio_config import (
    create_presidio_analyzer,
)


# --------------------------------------------------
# PII entities that we want to protect
# --------------------------------------------------

PII_ENTITIES = {
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "PERSON",
    "IN_PAN",
    "IN_AADHAAR",
    "IN_PASSPORT",
}


@register_validator(
    name="PIIValidator",
    data_type="string",
)
class PIIValidator(Validator):
    """
    Custom Guardrails validator for detecting and
    sanitizing PII.

    Presidio Analyzer:
        Detects PII.

    Presidio Anonymizer:
        Sanitizes detected PII.

    Guardrails:
        Uses fix_value when on_fail="fix".
    """

    def __init__(self, on_fail: Any = "exception"):
        super().__init__(on_fail=on_fail)

        self.analyzer = create_presidio_analyzer()

        self.anonymizer = AnonymizerEngine()

    # --------------------------------------------------
    # PII detection
    # --------------------------------------------------

    def _detect_pii(self, value: str):
        """
        Detect configured PII entities in the input.
        """

        results = self.analyzer.analyze(
            text=value,
            language="en",
        )

        return [
            result
            for result in results
            if result.entity_type in PII_ENTITIES
        ]

    # --------------------------------------------------
    # Sanitization
    # --------------------------------------------------

    def _sanitize(
        self,
        value: str,
        detected_pii: list,
    ) -> str:
        """
        Replace detected PII with safe placeholders.
        """

        if not detected_pii:
            return value

        operators = {
            # ------------------------------------------
            # Email
            # ------------------------------------------

            "EMAIL_ADDRESS": OperatorConfig(
                "replace",
                {
                    "new_value": "[EMAIL_REDACTED]",
                },
            ),

            # ------------------------------------------
            # Phone
            # ------------------------------------------

            "PHONE_NUMBER": OperatorConfig(
                "replace",
                {
                    "new_value": "[PHONE_REDACTED]",
                },
            ),

            # ------------------------------------------
            # Credit card
            # ------------------------------------------

            "CREDIT_CARD": OperatorConfig(
                "replace",
                {
                    "new_value": "[CARD_REDACTED]",
                },
            ),

            # ------------------------------------------
            # IP address
            # ------------------------------------------

            "IP_ADDRESS": OperatorConfig(
                "replace",
                {
                    "new_value": "[IP_REDACTED]",
                },
            ),

            # ------------------------------------------
            # Person
            # ------------------------------------------

            "PERSON": OperatorConfig(
                "replace",
                {
                    "new_value": "[PERSON_REDACTED]",
                },
            ),

            # ------------------------------------------
            # PAN
            # ------------------------------------------

            "IN_PAN": OperatorConfig(
                "replace",
                {
                    "new_value": "[PAN_REDACTED]",
                },
            ),

            # ------------------------------------------
            # Aadhaar
            # ------------------------------------------

            "IN_AADHAAR": OperatorConfig(
                "replace",
                {
                    "new_value": "[AADHAAR_REDACTED]",
                },
            ),

            # ------------------------------------------
            # Passport
            # ------------------------------------------

            "IN_PASSPORT": OperatorConfig(
                "replace",
                {
                    "new_value": "[PASSPORT_REDACTED]",
                },
            ),
        }

        result = self.anonymizer.anonymize(
            text=value,
            analyzer_results=detected_pii,
            operators=operators,
        )

        return result.text

    # --------------------------------------------------
    # Guardrails validation
    # --------------------------------------------------

    def validate(
        self,
        value: Any,
        metadata: dict | None = None,
    ):
        """
        Detect PII.

        If no PII exists:
            PassResult()

        If PII exists:
            FailResult with fix_value containing
            the sanitized text.
        """

        if not isinstance(value, str):
            return PassResult()

        detected_pii = self._detect_pii(value)

        if not detected_pii:
            return PassResult()

        detected_types = sorted(
            {
                result.entity_type
                for result in detected_pii
            }
        )

        sanitized_value = self._sanitize(
            value,
            detected_pii,
        )

        return FailResult(
            error_message=(
                "Private information detected in content: "
                + ", ".join(detected_types)
            ),
            fix_value=sanitized_value,
        )

    # --------------------------------------------------
    # Direct fix support
    # --------------------------------------------------

    def fix(
        self,
        value: Any,
        metadata: dict | None = None,
    ) -> str:
        """
        Directly sanitize a value.

        This also allows the validator to be tested
        independently from Guardrails.
        """

        if not isinstance(value, str):
            return value

        detected_pii = self._detect_pii(value)

        if not detected_pii:
            return value

        return self._sanitize(
            value,
            detected_pii,
        )