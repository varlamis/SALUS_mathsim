from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json

from jsonschema import Draft202012Validator

from salus_t43.handoff import build_artifact_manifest, verify_artifact_manifest


def test_final_manifest_is_sorted_complete_and_verifiable(repo_root, tmp_path) -> None:
    output = tmp_path / "manifest.json"
    fixed = datetime(2026, 9, 8, tzinfo=timezone.utc)
    first = build_artifact_manifest(repo_root, output, fixed)
    second = build_artifact_manifest(repo_root, output, fixed)
    assert first == second
    assert first["artifact_count"] == len(first["artifacts"])
    paths = [row["path"] for row in first["artifacts"]]
    assert paths == sorted(paths)
    assert {
        "README.md", "CHANGELOG.md", "requirements.lock",
        "contracts/integration/uc4_integration_contracts.yaml",
        "reports/validation/UC4_validation_matrix.md",
    } <= set(paths)
    assert not any(
        "__pycache__" in path or ".egg-info" in path or ".pytest_cache" in path or ".venv" in path
        for path in paths
    )
    assert verify_artifact_manifest(repo_root, first) == []


def test_manifest_schema_and_hash_tamper_detection(repo_root, tmp_path) -> None:
    manifest = build_artifact_manifest(repo_root, tmp_path / "manifest.json")
    schema = json.loads((repo_root / "models" / "schemas" / "artifact_manifest.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER).iter_errors(manifest)) == []
    readme = next(row for row in manifest["artifacts"] if row["path"] == "README.md")
    readme["sha256"] = hashlib.sha256(b"tampered").hexdigest()
    assert "hash mismatch: README.md" in verify_artifact_manifest(repo_root, manifest)
