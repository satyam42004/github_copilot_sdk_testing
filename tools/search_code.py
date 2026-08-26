from copilot import define_tool
from pydantic import BaseModel, Field

from .repository import get_repository_path


class SearchCodeParams(BaseModel):
    query: str = Field(
        description="Text, class name, function name, or symbol to search for"
    )


def _search_code(params: SearchCodeParams, invocation) -> str:
    root = get_repository_path()

    ignored = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
    }

    results = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in ignored for part in path.parts):
            continue

        try:
            lines = path.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines()
        except Exception:
            continue

        for line_number, line in enumerate(lines, start=1):
            if params.query.lower() in line.lower():
                results.append(
                    f"{path.relative_to(root)}:"
                    f"{line_number}: "
                    f"{line.strip()}"
                )

    if not results:
        return f"No matches found for: {params.query}"

    return "\n".join(results[:200])


search_code = define_tool(
    "search_code",
    description="Search for code or text across the repository.",
    handler=_search_code,
    params_type=SearchCodeParams,
    skip_permission=True,
)