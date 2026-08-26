from copilot import define_tool
from pydantic import BaseModel, Field

from .repository import get_repository_path


class ReadFileParams(BaseModel):
    file_path: str = Field(
        description="Path of the file relative to the repository root"
    )


def _read_file(params: ReadFileParams, invocation) -> str:
    root = get_repository_path()
    target = (root / params.file_path).resolve()

    if not target.is_relative_to(root):
        return "Error: file is outside the repository."

    if not target.exists():
        return f"File does not exist: {params.file_path}"

    if not target.is_file():
        return f"Path is not a file: {params.file_path}"

    try:
        return target.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception as e:
        return f"Error reading file: {e}"


read_file = define_tool(
    "read_file",
    description="Read a file from the repository.",
    handler=_read_file,
    params_type=ReadFileParams,
    skip_permission=True,
)