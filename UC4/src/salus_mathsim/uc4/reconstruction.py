"""Evidence-only time normalization and explainable claim scoring."""

from __future__ import annotations

from typing import Any

from .collection import CollectedEvidence
from .models import ReconstructionConfig


ALTERNATIVES = [
    "authorized or benign entry followed by device failure",
    "false-positive presence detection",
    "sensor battery or connectivity failure",
    "Home Assistant automation misconfiguration",
    "clock skew or delayed ingestion",
    "record eviction or queue loss",
]

CLAIM_EXPECTATIONS = {
    "entry": ("door.open", "presence.motion", "cpe.flow"),
    "automation": ("automation.triggered", "light.on"),
    "tamper": ("device.tamper", "device.offline", "cpe.flow"),
}


def _label(score: float | None) -> str:
    if score is None:
        return "indeterminate"
    if score < 0.25:
        return "unsupported"
    if score < 0.50:
        return "weak"
    if score < 0.75:
        return "moderate"
    return "strong"


def reconstruct(
    evidence: list[CollectedEvidence], config: ReconstructionConfig, *, uncertainty_seconds: float = 0.0,
    clock_offsets: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Reconstruct strictly from verified evidence; ground truth is not an argument."""
    verified = [item for item in evidence if item.verify_content() and item.item.custody_status == "verified"]
    observations: list[dict[str, Any]] = []
    for evidence_item in verified:
        content = evidence_item.content
        reported_time = content.get("event_time")
        timestamp_source = str(content.get("source", evidence_item.item.source_entity))
        offset = (clock_offsets or {}).get(timestamp_source, 0.0)
        estimated_time = reported_time - offset if isinstance(reported_time, (int, float)) else reported_time
        interval = None
        if isinstance(estimated_time, (int, float)):
            interval = {
                "start": max(0.0, estimated_time - uncertainty_seconds),
                "end": estimated_time + uncertainty_seconds,
            }
        observations.append({
            "evidence_id": evidence_item.item.evidence_id,
            "event_type": content.get("event_type"),
            "reported_time": reported_time,
            "estimated_time": estimated_time,
            "clock_offset_correction": offset,
            "uncertainty_interval": interval,
            "source_entity": evidence_item.item.source_entity,
            "quality": content.get("quality", "estimated"),
        })
    observations.sort(key=lambda item: (item["estimated_time"] if isinstance(item["estimated_time"], (int, float)) else float("inf"), item["evidence_id"]))

    ordering = []
    for left, right in zip(observations, observations[1:]):
        left_interval = left["uncertainty_interval"]
        right_interval = right["uncertainty_interval"]
        certain = bool(left_interval and right_interval and left_interval["end"] < right_interval["start"])
        ordering.append({
            "before_evidence_id": left["evidence_id"],
            "after_evidence_id": right["evidence_id"],
            "classification": "certain" if certain else "ambiguous",
        })

    claims = []
    for claim_name, expected in CLAIM_EXPECTATIONS.items():
        supporting = [item for item in observations if item["event_type"] in expected]
        present_types = {item["event_type"] for item in supporting}
        missing = [event_type for event_type in expected if event_type not in present_types]
        denominator = sum(config.support_weights.get(_weight_key(event_type), 1.0) for event_type in expected)
        positive = sum(
            config.support_weights.get(_weight_key(item["event_type"]), 1.0)
            * config.source_reliability.get(item["source_entity"], 0.5)
            for item in supporting
        )
        penalty = config.missing_evidence_penalty * sum(
            config.support_weights.get(_weight_key(event_type), 1.0) for event_type in missing
        )
        score = min(1.0, max(0.0, (positive - penalty) / denominator)) if denominator else None
        intervals = [item["uncertainty_interval"] for item in supporting if item["uncertainty_interval"]]
        claims.append({
            "claim_id": f"UC4-CLAIM-{claim_name.upper()}",
            "claim_type": claim_name,
            "support_score": score,
            "qualification": _label(score),
            "evidence_ids": [item["evidence_id"] for item in supporting],
            "time_interval": ({
                "start": min(item["start"] for item in intervals),
                "end": max(item["end"] for item in intervals),
            } if intervals else None),
            "missing_expected_observations": missing,
            "contradictions": [],
            "alternative_explanations": list(ALTERNATIVES),
        })
    return {
        "schema_version": "1.0.0",
        "method": "evidence_only_interval_and_support_scoring",
        "observations": observations,
        "ordering": ordering,
        "claims": claims,
        "limitations": [
            "Support scores are not calibrated probabilities.",
            "No claim identifies a person, intent, guilt, admissibility, or real-world occurrence.",
        ],
    }


def _weight_key(event_type: str) -> str:
    return {
        "door.open": "door_open",
        "presence.motion": "presence",
        "automation.triggered": "light_command",
        "light.on": "light_state",
        "cpe.flow": "cpe_flow",
        "device.tamper": "tamper",
        "device.offline": "offline",
    }.get(event_type, event_type.replace(".", "_"))
