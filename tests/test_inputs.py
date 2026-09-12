"""Focused MCP-01 configuration and input-resolution tests."""

from pathlib import Path

import pytest

from achlens.server.config import ServerConfig
from achlens.server.inputs import InputResolutionError, resolve_input


def _error(callable_object, *args, **kwargs) -> InputResolutionError:
    with pytest.raises(InputResolutionError) as caught:
        callable_object(*args, **kwargs)
    return caught.value


def test_content_input_and_exactly_one_input_contract() -> None:
    assert resolve_input(content="synthetic").content == "synthetic"
    assert _error(resolve_input).error.code == "INPUT_MISSING"
    assert _error(resolve_input, content="a", path="file.ach").error.code == "INPUT_CONFLICT"


def test_content_size_limit_is_checked_in_bytes() -> None:
    config = ServerConfig(max_bytes=3)
    assert _error(resolve_input, content="abcd", config=config).error.code == "TOO_LARGE"
    assert _error(resolve_input, content="éé", config=config).error.code == "TOO_LARGE"


def test_path_mode_requires_allowed_root(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.ach"
    file_path.write_text("synthetic", encoding="utf-8")
    assert _error(resolve_input, path=str(file_path)).error.code == "PATH_NOT_ALLOWED"


def test_allowlisted_path_is_read_and_size_checked(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.ach"
    file_path.write_text("synthetic", encoding="utf-8")
    config = ServerConfig(allowed_roots=(tmp_path.resolve(),), max_bytes=20)
    resolved = resolve_input(path=str(file_path), config=config)
    assert resolved.content == "synthetic"
    assert resolved.path == file_path.resolve()
    too_small = ServerConfig(allowed_roots=(tmp_path.resolve(),), max_bytes=2)
    assert _error(resolve_input, path=str(file_path), config=too_small).error.code == "TOO_LARGE"


def test_path_traversal_and_missing_paths_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    outside = tmp_path / "outside.ach"
    outside.write_text("synthetic", encoding="utf-8")
    config = ServerConfig(allowed_roots=(root.resolve(),))
    assert _error(resolve_input, path=str(outside), config=config).error.code == "PATH_NOT_ALLOWED"
    assert _error(resolve_input, path=str(root / "missing.ach"), config=config).error.code == "PATH_NOT_FOUND"


def test_symlink_escape_is_rejected_when_supported(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()
    outside = tmp_path / "outside.ach"
    outside.write_text("synthetic", encoding="utf-8")
    link = root / "linked.ach"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable")
    config = ServerConfig(allowed_roots=(root.resolve(),))
    assert _error(resolve_input, path=str(link), config=config).error.code == "PATH_NOT_ALLOWED"


def test_directories_and_non_utf8_files_are_rejected(tmp_path: Path) -> None:
    config = ServerConfig(allowed_roots=(tmp_path.resolve(),))
    assert _error(resolve_input, path=str(tmp_path), config=config).error.code == "PATH_NOT_ALLOWED"
    binary = tmp_path / "binary.ach"
    binary.write_bytes(b"\xff")
    assert _error(resolve_input, path=str(binary), config=config).error.code == "UNSUPPORTED"


def test_environment_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ACHLENS_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setenv("ACHLENS_ALLOW_REVEAL", "1")
    monkeypatch.setenv("ACHLENS_MAX_BYTES", "123")
    monkeypatch.setenv("ACHLENS_MAX_FINDINGS", "7")
    monkeypatch.setenv("ACHLENS_LOG_LEVEL", "info")
    config = ServerConfig.from_environment()
    assert config.allowed_roots == (tmp_path.resolve(),)
    assert config.allow_reveal
    assert config.max_bytes == 123
    assert config.max_findings == 7
    assert config.log_level == "INFO"
