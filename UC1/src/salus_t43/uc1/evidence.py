from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def collect(events: list[dict[str, Any]], allowed_types: set[str], allowed_fields: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence: list[dict[str, Any]] = []
    custody: list[dict[str, Any]] = []
    previous = "0" * 64
    for event in events:
        if event["event_type"] not in allowed_types:
            continue
        fields = {key: event[key] for key in sorted(allowed_fields) if key in event}
        item = {
            "evidence_id": f"UC1-EV-{len(evidence)+1:06d}",
            "source_event_id": event["event_id"],
            "evidence_type": event["event_type"],
            "content_hash": digest(fields),
            "collected_at": event["ingest_time"],
            "fields": fields,
            "custody_status": "verified",
        }
        evidence.append(item)
        chain_hash = digest([previous, item["content_hash"], "collect", item["collected_at"], "UC1-S06"])
        custody.append({
            "custody_id": f"UC1-CUS-{len(custody)+1:06d}",
            "evidence_id": item["evidence_id"],
            "action": "collect",
            "actor": "UC1-S06",
            "time": item["collected_at"],
            "previous_hash": previous,
            "chain_hash": chain_hash,
        })
        previous = chain_hash
    return evidence, custody


def verify(evidence: list[dict[str, Any]], custody: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_id = {item["evidence_id"]: item for item in evidence}
    previous = "0" * 64
    for row in custody:
        item = by_id.get(row["evidence_id"])
        if item is None:
            errors.append(f"missing evidence {row['evidence_id']}")
            continue
        if digest(item["fields"]) != item["content_hash"]:
            errors.append(f"content hash mismatch {item['evidence_id']}")
        expected = digest([previous, item["content_hash"], row["action"], row["time"], row["actor"]])
        if row["previous_hash"] != previous or row["chain_hash"] != expected:
            errors.append(f"custody chain mismatch {row['custody_id']}")
        previous = row["chain_hash"]
    return errors

