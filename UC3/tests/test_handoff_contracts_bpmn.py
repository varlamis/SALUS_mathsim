from copy import deepcopy
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import yaml
from salus_t43.handoff import build_manifest, verify_manifest


def test_contracts_have_all_boundaries(repo_root):
    data = yaml.safe_load((repo_root / "contracts/integration/uc3_integration_contracts.yaml").read_text(encoding="utf-8"))
    assert len(data["contracts"]) == 8
    assert {row["consumer"] for row in data["contracts"]} >= {"T4.4 DTE", "T4.2 SDaaSS", "T3.3 AI/XAI"}


def test_all_bpmn_xml_parses(repo_root):
    paths = list((repo_root / "diagrams").rglob("*.bpmn"))
    assert len(paths) == 8
    for path in paths:
        assert ET.parse(path).getroot().tag.endswith("definitions")


def test_manifest_sorted_complete_and_verifiable(repo_root, tmp_path):
    manifest = build_manifest(repo_root, tmp_path / "manifest.json", datetime(2026, 9, 10, tzinfo=timezone.utc))
    paths = [row["path"] for row in manifest["artifacts"]]
    assert paths == sorted(paths)
    assert "README.md" in paths and "models/formal/uc3_mathematical_model.md" in paths
    assert verify_manifest(repo_root, manifest) == []


def test_manifest_detects_tampering(repo_root, tmp_path):
    manifest = build_manifest(repo_root, tmp_path / "manifest.json")
    changed = deepcopy(manifest)
    changed["artifacts"][0]["sha256"] = "0" * 64
    assert verify_manifest(repo_root, changed)
