"""Secure resolution of content and local file inputs."""

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .config import ServerConfig


@dataclass(frozen=True)
class InputError:
    code: str
    message: str
    hint: str


class InputResolutionError(ValueError):
    """Structured input failure suitable for conversion to an MCP response."""

    def __init__(self, error: InputError) -> None:
        super().__init__(error.message)
        self.error = error


@dataclass(frozen=True)
class ResolvedInput:
    content: str
    path: Path | None = None


def _fail(code: str, message: str, hint: str) -> InputResolutionError:
    return InputResolutionError(InputError(code, message, hint))


def _allowed(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def _resolve_path(path_value: str, config: ServerConfig) -> Path:
    if not config.allowed_roots:
        raise _fail("PATH_NOT_ALLOWED", "Path input is disabled.", "Use content input or configure ACHLENS_ALLOWED_ROOTS.")
    requested = Path(path_value).expanduser()
    resolved = requested.resolve(strict=False)
    if not _allowed(resolved, config.allowed_roots):
        raise _fail("PATH_NOT_ALLOWED", "Path is outside the configured allowed roots.", "Use a file beneath an allowed root.")
    if not resolved.exists():
        raise _fail("PATH_NOT_FOUND", "The requested path does not exist.", "Check the path and try again.")
    try:
        metadata = resolved.stat()
    except OSError as error:
        raise _fail("PATH_NOT_FOUND", "The requested path could not be inspected.", "Check permissions and try again.") from error
    if not stat.S_ISREG(metadata.st_mode):
        raise _fail("PATH_NOT_ALLOWED", "The requested path is not a regular file.", "Provide a regular ACH file.")
    if metadata.st_size > config.max_bytes:
        raise _fail("TOO_LARGE", "The input file exceeds the configured size limit.", "Use a smaller file or raise ACHLENS_MAX_BYTES.")
    return resolved


def resolve_input(
    *,
    content: str | None = None,
    path: str | None = None,
    config: ServerConfig | None = None,
) -> ResolvedInput:
    """Resolve exactly one content or allowlisted path input."""
    if (content is None) == (path is None):
        code = "INPUT_MISSING" if content is None and path is None else "INPUT_CONFLICT"
        message = "Provide exactly one of content or path."
        raise _fail(code, message, "Set one input and leave the other unset.")
    settings = config or ServerConfig.from_environment()
    if content is not None:
        if len(content.encode("utf-8")) > settings.max_bytes:
            raise _fail("TOO_LARGE", "The content exceeds the configured size limit.", "Use smaller content or raise ACHLENS_MAX_BYTES.")
        return ResolvedInput(content=content)
    assert path is not None
    resolved = _resolve_path(path, settings)
    try:
        data = resolved.read_bytes()
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _fail("UNSUPPORTED", "The input file is not valid UTF-8 text.", "Provide text encoded for ACH processing.") from error
    except OSError as error:
        raise _fail("PATH_NOT_FOUND", "The input file could not be read.", "Check permissions and try again.") from error
    return ResolvedInput(content=text, path=resolved)


__all__ = ["InputError", "InputResolutionError", "ResolvedInput", "resolve_input"]