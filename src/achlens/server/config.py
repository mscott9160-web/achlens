"""Environment-backed server configuration."""

import os
from dataclasses import dataclass
from pathlib import Path


def _integer(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


@dataclass(frozen=True)
class ServerConfig:
    allowed_roots: tuple[Path, ...] = ()
    allow_reveal: bool = False
    max_bytes: int = 5_000_000
    max_findings: int = 200
    log_level: str = "WARNING"

    @classmethod
    def from_environment(cls) -> "ServerConfig":
        raw_roots = os.environ.get("ACHLENS_ALLOWED_ROOTS", "")
        roots = tuple(
            Path(value).expanduser().resolve()
            for value in raw_roots.split(os.pathsep)
            if value.strip()
        )
        return cls(
            allowed_roots=roots,
            allow_reveal=os.environ.get("ACHLENS_ALLOW_REVEAL", "0") == "1",
            max_bytes=_integer("ACHLENS_MAX_BYTES", 5_000_000),
            max_findings=_integer("ACHLENS_MAX_FINDINGS", 200),
            log_level=os.environ.get("ACHLENS_LOG_LEVEL", "WARNING").upper(),
        )


__all__ = ["ServerConfig"]
