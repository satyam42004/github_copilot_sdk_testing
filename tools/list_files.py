from pathlib import Path

from copilot import define_tool

from .repository import get_repository_path


def _list_files(params, invocation) -> str:
    root = get_repository_path()

    ignored = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
    }

    files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in ignored for part in path.parts):
            continue

        files.append(str(path.relative_to(root)))

    if not files:
        return "No files found."

    return "\n".join(sorted(files))


list_files = define_tool(
    "list_files",
    description="List all relevant files in the repository.",
    handler=_list_files,
    params_type=None,
    skip_permission=True,
)