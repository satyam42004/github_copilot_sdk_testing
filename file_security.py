"""Central filesystem access policy for the Copilot agent.

The model is not trusted to enforce filesystem boundaries.
Every filesystem tool must validate its target path here.

Default policy:
- Current repository: read/write allowed
- Desktop: read/write allowed
- Everything else: denied

Additional folders can be explicitly added by the application.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


class FileAccessDenied(PermissionError):
    """Raised when a filesystem operation targets a disallowed path."""


class FileAccessPolicy:
    def __init__(
        self,
        allowed_read_paths: Iterable[str | Path],
        allowed_write_paths: Iterable[str | Path] | None = None,
    ):
        self.allowed_read_paths = self._normalize_roots(allowed_read_paths)
        self.allowed_write_paths = self._normalize_roots(
            allowed_write_paths
            if allowed_write_paths is not None
            else allowed_read_paths
        )

        if not self.allowed_read_paths:
            raise ValueError("At least one allowed read folder is required.")
        if not self.allowed_write_paths:
            raise ValueError("At least one allowed write folder is required.")

    @staticmethod
    def _normalize_roots(paths: Iterable[str | Path]) -> tuple[Path, ...]:
        roots: list[Path] = []

        for value in paths:
            raw = str(value).strip()
            if not raw:
                continue

            path = Path(os.path.expandvars(raw)).expanduser().resolve(strict=False)

            if path not in roots:
                roots.append(path)

        return tuple(roots)

    @staticmethod
    def _is_within(target: Path, root: Path) -> bool:
        try:
            target.relative_to(root)
            return True
        except ValueError:
            return False

    def validate(self, target: str | Path, operation: str = "read") -> Path:
        """Normalize and validate a path for a read or write operation."""
        if operation not in {"read", "write"}:
            raise ValueError(f"Unsupported filesystem operation: {operation}")

        target_path = Path(target)
        target_path = Path(
            os.path.expandvars(str(target_path))
        ).expanduser().resolve(strict=False)

        roots = (
            self.allowed_write_paths
            if operation == "write"
            else self.allowed_read_paths
        )

        if not any(self._is_within(target_path, root) for root in roots):
            allowed = "\n".join(f"  - {root}" for root in roots)
            raise FileAccessDenied(
                f"Access denied: {operation} operation is not allowed for:\n"
                f"  {target_path}\n\n"
                f"Allowed {operation} folders:\n{allowed}"
            )

        return target_path

    def is_allowed(self, target: str | Path, operation: str = "read") -> bool:
        try:
            self.validate(target, operation)
            return True
        except (FileAccessDenied, ValueError):
            return False

    def describe(self) -> dict[str, list[str]]:
        return {
            "read": [str(p) for p in self.allowed_read_paths],
            "write": [str(p) for p in self.allowed_write_paths],
        }


def get_desktop_path() -> Path:
    """Resolve the Windows Desktop, including OneDrive Desktop."""
    home = Path.home()

    candidates = [
        home / "Desktop",
        home / "OneDrive" / "Desktop",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return candidates[0].resolve(strict=False)


def build_default_file_access_policy(
    repository_path: str | Path,
) -> FileAccessPolicy:
    """Safe default: repository + Desktop."""
    repository = Path(repository_path).expanduser().resolve()

    return FileAccessPolicy(
        allowed_read_paths=[repository, get_desktop_path()],
        allowed_write_paths=[repository, get_desktop_path()],
    )


def parse_allowed_folders(
    configured_folders: Iterable[str] | None,
    repository_path: str | Path,
) -> list[Path]:
    """Return configured folders plus the repository, with duplicates removed."""
    repository = Path(repository_path).expanduser().resolve()
    folders: list[Path] = [repository]

    for value in configured_folders or []:
        raw = str(value).strip()
        if not raw:
            continue

        path = Path(
            os.path.expandvars(raw)
        ).expanduser().resolve(strict=False)

        if path not in folders:
            folders.append(path)

    return folders
