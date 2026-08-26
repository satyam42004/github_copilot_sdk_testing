from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
)
from presidio_analyzer.nlp_engine import (
    NlpEngineProvider,
)


def create_presidio_analyzer() -> AnalyzerEngine:
    """
    Create a Presidio AnalyzerEngine using the lightweight
    spaCy English model.

    In addition to Presidio's built-in recognizers, this
    configuration adds explicit recognizers for structured
    Indian identifiers and credit cards.
    """

    # --------------------------------------------------
    # spaCy configuration
    # --------------------------------------------------

    configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {
                "lang_code": "en",
                "model_name": "en_core_web_sm",
            }
        ],
    }

    provider = NlpEngineProvider(
        nlp_configuration=configuration
    )

    nlp_engine = provider.create_engine()

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        supported_languages=["en"],
    )

    # --------------------------------------------------
    # Credit Card
    # --------------------------------------------------

    credit_card_pattern = Pattern(
        name="credit_card_pattern",
        regex=r"\b(?:\d{4}[\s-]?){3}\d{4}\b",
        score=0.85,
    )

    credit_card_recognizer = PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=[credit_card_pattern],
    )

    analyzer.registry.add_recognizer(
        credit_card_recognizer
    )

    # --------------------------------------------------
    # Indian PAN
    # Example:
    # ABCDE1234F
    # --------------------------------------------------

    pan_pattern = Pattern(
        name="indian_pan_pattern",
        regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        score=0.95,
    )

    pan_recognizer = PatternRecognizer(
        supported_entity="IN_PAN",
        patterns=[pan_pattern],
    )

    analyzer.registry.add_recognizer(
        pan_recognizer
    )

    # --------------------------------------------------
    # Indian Aadhaar
    # Examples:
    # 1234 5678 9012
    # 1234-5678-9012
    # 123456789012
    # --------------------------------------------------

    aadhaar_pattern = Pattern(
        name="indian_aadhaar_pattern",
        regex=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        score=0.90,
    )

    aadhaar_recognizer = PatternRecognizer(
        supported_entity="IN_AADHAAR",
        patterns=[aadhaar_pattern],
    )

    analyzer.registry.add_recognizer(
        aadhaar_recognizer
    )

    # --------------------------------------------------
    # Indian Passport
    #
    # Common format:
    # A1234567
    #
    # We require the value to appear in a passport-like
    # context to reduce false positives.
    # --------------------------------------------------

    passport_pattern = Pattern(
        name="indian_passport_pattern",
        regex=r"\b[A-Z][0-9]{7}\b",
        score=0.80,
    )

    passport_recognizer = PatternRecognizer(
        supported_entity="IN_PASSPORT",
        patterns=[passport_pattern],
        context=[
            "passport",
            "passport number",
            "travel document",
        ],
    )

    analyzer.registry.add_recognizer(
        passport_recognizer
    )

    return analyzer