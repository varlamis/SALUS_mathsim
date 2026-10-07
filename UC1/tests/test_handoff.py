from copy import deepcopy
from datetime import datetime, timezone

from salus_mathsim.handoff import build_manifest, verify_manifest


def test_manifest_is_sorted_complete_and_verifiable(repo_root, tmp_path):
    manifest = build_manifest(repo_root, tmp_path / "manifest.json", datetime(2026, 9, 10, tzinfo=timezone.utc))
    paths = [row["path"] for row in manifest["artifacts"]]
    assert paths == sorted(paths)
    assert {"README.md", "pyproject.toml", "models/instances/uc1_entities.json", "configs/uc1/forged_message_attack.yaml"} <= set(paths)
    assert verify_manifest(repo_root, manifest) == []


def test_manifest_detects_tampering(repo_root, tmp_path):
    manifest = build_manifest(repo_root, tmp_path / "manifest.json")
    altered = deepcopy(manifest)
    altered["artifacts"][0]["sha256"] = "0" * 64
    assert verify_manifest(repo_root, altered)

