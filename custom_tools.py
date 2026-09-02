"""Custom filesystem tools for Copilot SDK."""

from pathlib import Path

from pydantic import BaseModel, Field
from copilot import define_tool

from file_security import FileAccessDenied, FileAccessPolicy
from observability import record_tool_span


class CreateFileParams(BaseModel):
    """Parameters required to create a new file."""

    path: str = Field(
        description=(
            "The exact path where the new file should be created. "
            "Use the path requested by the user."
        )
    )

    file_text: str = Field(
        description=(
            "The complete contents of the file. "
            "For HTML files, provide the complete HTML document."
        )
    )


def build_create_tool(
    repository_path: str,
    file_access_policy: FileAccessPolicy,
):
    """Build the policy-aware file creation tool."""

    repository = (
        Path(repository_path)
        .expanduser()
        .resolve()
    )

    @define_tool(
        name="create",
        description=(
            "Create a NEW file at the requested path. "
            "This is the ONLY tool that should be used to create new files. "
            "The destination must be inside a configured allowed write folder. "
            "The tool supports HTML, CSS, JavaScript, Markdown, JSON, "
            "and plain text files. "
            "Always provide both the exact file path and complete file contents."
        ),
        overrides_built_in_tool=True,
    )
    def create(params: CreateFileParams) -> str:

        with record_tool_span("create"):

            print("=" * 60)
            print("[CREATE TOOL]")
            print(f"Path: {params.path}")
            print(f"Content length: {len(params.file_text)}")
            print("=" * 60)

            target = Path(
                params.path
            ).expanduser()

            # Relative paths are repository-relative.
            if not target.is_absolute():
                target = repository / target

            target = target.resolve(
                strict=False
            )

            # --------------------------------------------------
            # FILESYSTEM SECURITY
            # --------------------------------------------------

            try:

                target = file_access_policy.validate(
                    target,
                    "write",
                )

            except FileAccessDenied as exc:

                print(
                    f"[CREATE BLOCKED] {exc}"
                )

                return (
                    f"BLOCKED: {exc}"
                )

            # --------------------------------------------------
            # EXISTING FILE PROTECTION
            # --------------------------------------------------

            if target.exists():

                print(
                    f"[CREATE BLOCKED] File already exists: {target}"
                )

                return (
                    f"BLOCKED: File already exists: {target}"
                )

            # --------------------------------------------------
            # CREATE FILE
            # --------------------------------------------------

            try:

                target.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                target.write_text(
                    params.file_text,
                    encoding="utf-8",
                )

            except Exception as exc:

                print(
                    f"[CREATE ERROR] {exc}"
                )

                return (
                    f"FAILED: Could not create file: {exc}"
                )

            # --------------------------------------------------
            # VERIFY CREATION
            # --------------------------------------------------

            if not target.exists():

                return (
                    "FAILED: File creation completed "
                    "without the file appearing on disk."
                )

            print(
                f"[CREATE SUCCESS] {target}"
            )

            return (
                f"SUCCESS: Created file: {target}"
            )

    return create