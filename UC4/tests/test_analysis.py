from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from salus_t43.uc4.analysis import mean_confidence_interval, pearson, run_monte_carlo, wilson_interval


def test_statistical_helpers_preserve_undefined_values() -> None:
    interval = mean_confidence_interval([1.0, None, 3.0])
    assert interval["n"] == 2
    assert interval["undefined"] == 1
    assert interval["mean"] == 2.0
    assert wilson_interval(0, 0)["proportion"] is None
    assert pearson([1, 2, 3], [2, 4, 6]) == 1.0
    assert pearson([1, 1], [2, 3]) is None


def test_seeded_monte_carlo_is_reproducible(repo_root) -> None:
    design = repo_root / "configs" / "uc4" / "monte_carlo.yaml"
    first = run_monte_carlo(repo_root, design, sample_count=4)
    second = run_monte_carlo(repo_root, design, sample_count=4)
    assert first.summary["samples_sha256"] == second.summary["samples_sha256"]
    assert first.summary["nominal"]["canonical_result_sha256"] == second.summary["nominal"]["canonical_result_sha256"]
    assert first.summary["simulation_seeds"] == [44000, 44001, 44002, 44003]
    assert all(sample["outcomes"]["unauthorized_disclosure_bytes"] == 0 for sample in first.samples)
    assert all(interval["n"] + interval["undefined"] == 4 for interval in first.summary["confidence_intervals"].values())
    acquisition = first.nominal.documents["metrics"]["network"]["acquisition"]
    assert {"maximum_queue_occupancy_bytes", "dropped_bytes", "loss_rate"} <= set(acquisition)
    ET.fromstring(first.sensitivity_svg)
    json.dumps(first.summary, allow_nan=False)
