import hashlib
import json
from typing import Any


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def collect(events: list[dict[str, Any]], allowed_types: set[str], allowed_fields: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence: list[dict[str, Any]] = []
    custody: list[dict[str, Any]] = []
    previous = "0" * 64
    for event in events:
        if event["event_type"] not in allowed_types:
            continue
        content = {key: event[key] for key in sorted(allowed_fields) if key in event}
        item = {"evidence_id": f"UC5-ED-{len(evidence)+1:06d}", "evidence_type": event["event_type"], "source_event_id": event["event_id"], "content": content, "content_sha256": digest(content)}
        evidence.append(item)
        record = {"custody_id": f"UC5-CL-{len(custody)+1:06d}", "evidence_id": item["evidence_id"], "action": "collected", "previous_hash": previous}
        record["record_hash"] = digest(record)
        previous = record["record_hash"]
        custody.append(record)
    return evidence, custody


def verify(evidence: list[dict[str, Any]], custody: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_id = {item["evidence_id"]: item for item in evidence}
    previous = "0" * 64
    for item in evidence:
        if digest(item["content"]) != item["content_sha256"]:
            errors.append(f"content hash mismatch: {item['evidence_id']}")
    for record in custody:
        expected = record["record_hash"]
        unsigned = {k: v for k, v in record.items() if k != "record_hash"}
        if record["evidence_id"] not in by_id or record["previous_hash"] != previous or digest(unsigned) != expected:
            errors.append(f"custody verification failed: {record['custody_id']}")
        previous = expected
    return errors

