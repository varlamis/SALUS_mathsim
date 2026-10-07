from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


EXCLUDED = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".pytest_tmp",
    "__pycache__",
    "salus_t43_uc1.egg-info",
}


def build_manifest(root: Path, output: Path, generated_at: datetime | None = None) -> dict[str, Any]:
    rows = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file() or path.resolve() == output.resolve() or any(part in EXCLUDED for part in path.parts) or path.suffix in {".pyc", ".pyo"}:
            continue
        content = path.read_bytes()
        rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
    return {"schema_version": "1.0.0", "use_case": "UC1", "generated_at": (generated_at or datetime.now(timezone.utc)).isoformat(), "artifact_count": len(rows), "artifacts": rows}


def verify_manifest(root: Path, manifest: dict[str, Any]) -> list[str]:
    errors = []
    if manifest.get("artifact_count") != len(manifest.get("artifacts", [])):
        errors.append("artifact_count mismatch")
    for row in manifest.get("artifacts", []):
        path = root / row["path"]
        try:
            path.resolve().relative_to(root.resolve())
        except ValueError:
            errors.append(f"path escapes root: {row['path']}")
            continue
        if not path.is_file():
            errors.append(f"missing artifact: {row['path']}")
            continue
        content = path.read_bytes()
        if len(content) != row["bytes"] or hashlib.sha256(content).hexdigest() != row["sha256"]:
            errors.append(f"hash mismatch: {row['path']}")
    return errors
