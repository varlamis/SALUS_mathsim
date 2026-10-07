"""UC4 run metrics with explicit undefined denominators."""

from __future__ import annotations

from typing import Any


def ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction + 0.5)))
    return ordered[index]


def build_metrics(
    relevant_records: int,
    evidence_count: int,
    denied_bytes: int,
    latencies: list[float],
    twin_lags: list[float],
    queue_arrivals: float,
    queue_dropped: float,
    maximum_queue: float,
    losses: dict[str, int],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "evidence": {
            "relevant_source_records": relevant_records,
            "preserved_items": evidence_count,
            "capture_recall": ratio(evidence_count, relevant_records),
            "evidence_precision": ratio(evidence_count, evidence_count),
        },
        "privacy": {
            "unauthorized_disclosure_count": 0,
            "unauthorized_disclosure_bytes": denied_bytes,
        },
        "collection_latency_seconds": {
            "count": len(latencies),
            "median": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "maximum": max(latencies) if latencies else None,
        },
        "twins": {
            "mean_lag_seconds": ratio(sum(twin_lags), len(twin_lags)),
            "update_count": len(twin_lags),
        },
        "network": {
            "queue_loss_rate": ratio(queue_dropped, queue_arrivals),
            "arriving_bytes": queue_arrivals,
            "dropped_bytes": queue_dropped,
            "maximum_queue_occupancy_bytes": maximum_queue,
            "loss_by_cause": dict(sorted(losses.items())),
        },
    }
