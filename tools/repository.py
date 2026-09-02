from pathlib import Path


REPOSITORY_PATH = Path(
    r"C:\Users\satya\Desktop\copilot_empty_test"
).resolve()


def get_repository_path() -> Path:
    if not REPOSITORY_PATH.exists():
        raise FileNotFoundError(
            f"Repository does not exist: {REPOSITORY_PATH}"
        )

    if not REPOSITORY_PATH.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {REPOSITORY_PATH}"
        )

    return REPOSITORY_PATH