"""Custom repository tools for Copilot SDK."""

from pathlib import Path
from copilot import define_tool


def build_create_tool(repository_path: str):
    repository = Path(repository_path).resolve()

    @define_tool(
        name="create",
        description=(
            "Create a text file inside the configured repository. "
            "Use for HTML, CSS, JavaScript, Markdown, JSON, and text files."
        ),
        overrides_built_in_tool=True,
    )
    def create(path: str, file_text: str) -> str:
        target = (repository / path).resolve()

        try:
            target.relative_to(repository)
        except ValueError:
            raise ValueError(
                "File creation outside the configured repository is not allowed."
            )

        if target.exists():
            raise FileExistsError(f"File already exists: {target}")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file_text, encoding="utf-8")
        return f"Created file: {target}"

    return create
