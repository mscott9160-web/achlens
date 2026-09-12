"""Validate release metadata before a tagged build."""

from __future__ import annotations

import ast
import json
import os
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_package_version() -> str:
    tree = ast.parse((ROOT / "src/achlens/__init__.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__version__":
                    value = ast.literal_eval(node.value)
                    if isinstance(value, str):
                        return value
    raise ValueError("src/achlens/__init__.py does not define __version__")


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    project_version = project["version"]
    package_version = read_package_version()
    manifest = json.loads((ROOT / "server.json").read_text())
    manifest_version = manifest["version"]
    package_manifest_version = manifest["packages"][0]["version"]
    tag = os.environ.get("RELEASE_TAG", "")

    versions = {
        "pyproject.toml": project_version,
        "src/achlens/__init__.py": package_version,
        "server.json": manifest_version,
        "server.json package": package_manifest_version,
    }
    if len(set(versions.values())) != 1:
        raise SystemExit(f"release metadata versions differ: {versions}")
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise SystemExit(f"release tag must be a semantic v-prefixed version: {tag!r}")
    if tag[1:] != project_version:
        raise SystemExit(
            f"release tag {tag!r} does not match project version {project_version!r}"
        )

    print(f"Release metadata is consistent for {tag}")


if __name__ == "__main__":
    main()
