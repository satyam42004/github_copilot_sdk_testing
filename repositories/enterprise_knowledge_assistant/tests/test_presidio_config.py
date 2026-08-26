from utils.guardrails.presidio_config import (
    create_presidio_analyzer,
)


def main():
    analyzer = create_presidio_analyzer()

    text = "My email is employee@example.com."

    results = analyzer.analyze(
        text=text,
        language="en",
    )

    print("Presidio analyzer created successfully.")
    print(f"Detected entities: {len(results)}")

    for result in results:
        print(
            f"Entity: {result.entity_type}, "
            f"Score: {result.score}, "
            f"Start: {result.start}, "
            f"End: {result.end}"
        )


if __name__ == "__main__":
    main()