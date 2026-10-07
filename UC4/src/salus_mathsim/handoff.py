"""Generation and verification of the final UC4 artifact inventory."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator

from . import __version__


TOP_LEVEL_FILES = (".gitignore", "README.md", "CHANGELOG.md", "pyproject.toml", "requirements.lock")
ARTIFACT_ROOTS = ("configs", "contracts", "data", "diagrams", "docs", "models", "reports", "src", "tests")
EXCLUDED_PARTS = {".git", ".pytest_cache", ".pytest_tmp", ".venv", "venv", "__pycache__", "salus_mathsim.egg-info"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def _included(path: Path, output_path: Path) -> bool:
    return (
        path.is_file()
        and path.resolve() != output_path.resolve()
        and not any(part in EXCLUDED_PARTS for part in path.parts)
        and path.suffix.lower() not in EXCLUDED_SUFFIXES
    )


def artifact_paths(root: Path, output_path: Path) -> Iterable[Path]:
    for name in TOP_LEVEL_FILES:
        path = root / name
        if _included(path, output_path):
            yield path
    for name in ARTIFACT_ROOTS:
        directory = root / name
        if directory.is_dir():
            yield from (path for path in directory.rglob("*") if _included(path, output_path))


def build_artifact_manifest(root: Path, output_path: Path, generated_at: datetime | None = None) -> dict[str, Any]:
    rows = []
    for path in sorted(artifact_paths(root, output_path), key=lambda item: item.relative_to(root).as_posix()):
        content = path.read_bytes()
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })
    moment = generated_at or datetime.now(timezone.utc)
    return {
        "schema_version": "1.0.0", "use_case": "UC4",
        "generator": f"salus-mathsim/{__version__}",
        "generated_at_utc": moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "hash_algorithm": "SHA-256", "self_excluded": True,
        "artifact_count": len(rows), "artifacts": rows,
    }


def verify_artifact_manifest(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    schema = json.loads((root / "models" / "schemas" / "artifact_manifest.schema.json").read_text(encoding="utf-8"))
    errors.extend(error.message for error in Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(manifest))
    if manifest.get("artifact_count") != len(manifest.get("artifacts", [])):
        errors.append("artifact_count does not equal artifacts length")
    seen: set[str] = set()
    for row in manifest.get("artifacts", []):
        relative = row.get("path", "")
        if relative in seen:
            errors.append(f"duplicate artifact path: {relative}")
            continue
        seen.add(relative)
        path = root / relative
        try:
            resolved = path.resolve()
            resolved.relative_to(root.resolve())
        except ValueError:
            errors.append(f"artifact escapes repository: {relative}")
            continue
        if not path.is_file():
            errors.append(f"artifact does not exist: {relative}")
            continue
        content = path.read_bytes()
        if len(content) != row.get("bytes"):
            errors.append(f"size mismatch: {relative}")
        if hashlib.sha256(content).hexdigest() != row.get("sha256"):
            errors.append(f"hash mismatch: {relative}")
    return errors


def write_artifact_manifest(root: Path, output_path: Path) -> dict[str, Any]:
    manifest = build_artifact_manifest(root, output_path)
    errors = verify_artifact_manifest(root, manifest)
    if errors:
        raise ValueError("artifact manifest verification failed: " + "; ".join(errors))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest
