from utils.guardrails.input_guard import InputGuard


def test_safe_input():
    guard = InputGuard()

    text = "What is the company work from home policy?"

    result = guard.validate(text)

    assert result == text

    print("SAFE INPUT TEST: PASSED")
    print(f"Validated input: {result}")


def test_email_is_blocked():
    guard = InputGuard()

    text = "My email is employee@example.com. What is the leave policy?"

    try:
        guard.validate(text)

        print("PII INPUT TEST: FAILED")
        print("Email was not blocked.")

    except Exception as exc:
        print("PII INPUT TEST: PASSED")
        print("Email was blocked by Guardrails.")
        print(f"Validation error: {exc}")


def main():
    print("Testing safe input...")
    test_safe_input()

    print("\nTesting PII input...")
    test_email_is_blocked()


if __name__ == "__main__":
    main()