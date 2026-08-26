from utils.guardrails.pii_validator import PIIValidator


def main():
    validator = PIIValidator()

    test_cases = [
        (
            "Normal question",
            "What is the company leave policy?",
        ),
        (
            "Email",
            "My email is employee@example.com. What is the leave policy?",
        ),
        (
            "Phone",
            "My phone number is 9876543210.",
        ),
        (
            "Credit card",
            "My credit card number is 4532 1234 5678 9012.",
        ),
        (
            "IP address",
            "My IP address is 192.168.1.100.",
        ),
        (
            "PAN",
            "My PAN is ABCDE1234F.",
        ),
        (
            "Aadhaar",
            "My Aadhaar number is 1234 5678 9012.",
        ),
        (
            "Passport",
            "My passport number is A1234567.",
        ),
    ]

    print("\nStarting PII sanitization test...\n")

    for name, text in test_cases:

        print("=" * 60)
        print(f"TEST: {name}")
        print(f"Original:   {text}")

        try:
            result = validator.fix(text)

            print(f"Sanitized:  {result}")

        except Exception as exc:
            print(f"ERROR: {exc}")

    print("\nPII SANITIZATION TEST COMPLETED")


if __name__ == "__main__":
    main()