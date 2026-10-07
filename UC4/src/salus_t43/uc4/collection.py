"""Canonical evidence construction and integrity verification."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

from .authorization import PolicyDecision, SourceRecord
from .models import EvidenceItem


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize the JSON-compatible value using RFC 8785/JCS rules."""
    return _canonical(value).encode("utf-8")


def _canonical(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return _ecmascript_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_canonical(item) for item in value) + "]"
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("JCS object keys must be strings")
        keys = sorted(value, key=lambda key: key.encode("utf-16-be", errors="surrogatepass"))
        return "{" + ",".join(f"{_canonical(key)}:{_canonical(value[key])}" for key in keys) + "}"
    raise TypeError(f"value of type {type(value).__name__} is not JSON-compatible")


def _ecmascript_number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("RFC 8785 forbids NaN and infinity")
    if value == 0:
        return "0"
    text = repr(value).lower()
    absolute = abs(value)
    if 1e-6 <= absolute < 1e21:
        if "e" in text:
            mantissa, exponent_text = text.split("e")
            exponent = int(exponent_text)
            sign = "-" if mantissa.startswith("-") else ""
            digits = mantissa.lstrip("-").replace(".", "")
            decimal_position = (mantissa.lstrip("-").find(".") if "." in mantissa else len(mantissa.lstrip("-"))) + exponent
            if decimal_position <= 0:
                text = sign + "0." + "0" * (-decimal_position) + digits
            elif decimal_position >= len(digits):
                text = sign + digits + "0" * (decimal_position - len(digits))
            else:
                text = sign + digits[:decimal_position] + "." + digits[decimal_position:]
        if text.endswith(".0"):
            text = text[:-2]
        return text
    if "e" not in text:
        text = format(value, ".15e")
    mantissa, exponent_text = text.split("e")
    mantissa = mantissa.rstrip("0").rstrip(".")
    exponent = int(exponent_text)
    return f"{mantissa}e{'+' if exponent >= 0 else ''}{exponent}"


@dataclass(frozen=True, slots=True)
class CollectedEvidence:
    item: EvidenceItem
    content: dict[str, Any]

    def verify_content(self) -> bool:
        return hashlib.sha256(canonical_json_bytes(self.content)).hexdigest() == self.item.content_hash


def collect_evidence(
    evidence_id: str,
    record: SourceRecord,
    projection: dict[str, Any],
    decision: PolicyDecision,
    acquisition_time: float,
) -> CollectedEvidence:
    content_hash = hashlib.sha256(canonical_json_bytes(projection)).hexdigest()
    method = {
        "cpe_flow_metadata": "cpe_historical",
        "home_assistant_event": "home_assistant_export",
        "device_state_event": "device_state_export",
    }.get(record.data_type, "device_state_export")
    item = EvidenceItem.model_validate({
        "schema_version": "1.0.0",
        "evidence_id": evidence_id,
        "use_case": "UC4",
        "source_entity": record.source_entity,
        "source_record_ids": [record.record_id],
        "authorization_id": decision.authorization_id,
        "policy_decision_id": decision.policy_decision_id,
        "acquisition_method": method,
        "source_time_range": {"start": record.event_time, "end": record.event_time},
        "acquisition_time": acquisition_time,
        "content_hash": content_hash,
        "canonicalization": "RFC8785-JCS",
        "collector_id": "UC4-S02",
        "sensitivity": "High",
        "transformations": [{
            "transformation_id": f"UC4-TRANSFORM-{evidence_id.rsplit('-', 1)[-1]}",
            "type": "minimize" if decision.decision == "minimize" else "none",
            "input_evidence_ids": [],
            "time": acquisition_time,
            "actor_id": "UC4-S02",
        }],
        "custody_status": "registered",
        "storage_reference": f"evidence://sha256/{content_hash}",
    })
    return CollectedEvidence(item, dict(projection))
