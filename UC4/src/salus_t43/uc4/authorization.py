"""Fail-closed UC4 authorization, scope, and minimization policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from .models import AuthorizationConfig


@dataclass(frozen=True, slots=True)
class SourceRecord:
    record_id: str
    source_entity: str
    subject_entity: str
    data_type: str
    required_action: str
    event_time: float
    content: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    policy_decision_id: str
    authorization_id: str
    record_id: str | None
    decision: Literal["allow", "minimize", "deny"]
    reason_code: str
    evaluation_time: float
    released_fields: tuple[str, ...]
    bytes_released: int

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["released_fields"] = list(self.released_fields)
        return value


def evaluate_record(
    authorization: AuthorizationConfig,
    record: SourceRecord,
    request_time: float,
    policy_decision_id: str,
    requested_purpose: str,
) -> tuple[PolicyDecision, dict[str, Any] | None]:
    """Evaluate every eligibility term; any missing or failed term denies."""

    checks = (
        (authorization.decision_path == "allow", f"authorization_{authorization.decision_path}"),
        (authorization.verification_result == "valid", "verification_not_valid"),
        (requested_purpose == authorization.purpose, "purpose_mismatch"),
        (authorization.valid_from <= request_time < authorization.valid_to, "authorization_not_active"),
        (authorization.evidence_window_start <= record.event_time < authorization.evidence_window_end, "event_outside_evidence_window"),
        (record.subject_entity in authorization.allowed_entities, "entity_out_of_scope"),
        (record.data_type in authorization.allowed_data_types, "data_type_out_of_scope"),
        (record.required_action in authorization.allowed_actions, "action_out_of_scope"),
    )
    for passed, reason in checks:
        if not passed:
            return PolicyDecision(
                policy_decision_id, authorization.authorization_id, record.record_id,
                "deny", reason, request_time, (), 0,
            ), None

    permitted = set(authorization.permitted_fields)
    projected = {key: value for key, value in record.content.items() if key in permitted}
    if not projected:
        return PolicyDecision(
            policy_decision_id, authorization.authorization_id, record.record_id,
            "deny", "empty_permitted_projection", request_time, (), 0,
        ), None
    decision = "allow" if set(record.content).issubset(permitted) else "minimize"
    return PolicyDecision(
        policy_decision_id, authorization.authorization_id, record.record_id,
        decision, "eligible", request_time, tuple(sorted(projected)), 0,
    ), projected


def denial_for_request(
    authorization: AuthorizationConfig, request_time: float, policy_decision_id: str,
) -> PolicyDecision:
    return PolicyDecision(
        policy_decision_id, authorization.authorization_id, None, "deny",
        f"authorization_{authorization.decision_path}", request_time, (), 0,
    )
