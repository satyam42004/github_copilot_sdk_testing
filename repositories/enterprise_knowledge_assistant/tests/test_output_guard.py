from utils.guardrails.output_guard import OutputGuard


def test_safe_output():
    guard = OutputGuard()

    response = (
        "The company requires employees to follow "
        "the latest approved work-from-home policy."
    )

    result = guard.validate(response)

    assert result == response

    print("SAFE OUTPUT TEST: PASSED")
    print(f"Validated response: {result}")


def test_pii_output_is_blocked():
    guard = OutputGuard()

    response = (
        "The employee's email address is "
        "john.doe@example.com."
    )

    try:
        guard.validate(response)

        print("PII OUTPUT TEST: FAILED")
        print("PII was not blocked.")

    except Exception as exc:
        print("PII OUTPUT TEST: PASSED")
        print("PII was blocked by Output Guardrails.")
        print(f"Validation error: {exc}")


def main():
    print("Testing safe output...")
    test_safe_output()

    print("\nTesting PII output...")
    test_pii_output_is_blocked()


if __name__ == "__main__":
    main()