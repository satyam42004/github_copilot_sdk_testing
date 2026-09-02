from pathlib import Path

import pytest

from file_security import FileAccessDenied, FileAccessPolicy


def test_allowed_child_is_allowed(tmp_path):
    policy = FileAccessPolicy([tmp_path], [tmp_path])
    target = tmp_path / "folder" / "test.html"

    assert policy.validate(target, "write") == target.resolve()


def test_sibling_folder_is_blocked(tmp_path):
    allowed = tmp_path / "allowed"
    blocked = tmp_path / "blocked"
    allowed.mkdir()
    blocked.mkdir()

    policy = FileAccessPolicy([allowed], [allowed])

    with pytest.raises(FileAccessDenied):
        policy.validate(blocked / "test.html", "write")


def test_parent_traversal_is_blocked(tmp_path):
    allowed = tmp_path / "allowed"
    blocked = tmp_path / "blocked"
    allowed.mkdir()
    blocked.mkdir()

    policy = FileAccessPolicy([allowed], [allowed])

    with pytest.raises(FileAccessDenied):
        policy.validate(
            allowed / ".." / "blocked" / "test.html",
            "write",
        )


def test_read_and_write_roots_can_differ(tmp_path):
    read_root = tmp_path / "read"
    write_root = tmp_path / "write"
    read_root.mkdir()
    write_root.mkdir()

    policy = FileAccessPolicy(
        allowed_read_paths=[read_root],
        allowed_write_paths=[write_root],
    )

    assert policy.is_allowed(read_root / "a.txt", "read")
    assert not policy.is_allowed(read_root / "a.txt", "write")
    assert policy.is_allowed(write_root / "a.txt", "write")