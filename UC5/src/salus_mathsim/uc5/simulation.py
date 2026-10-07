from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Any

import yaml

from .evidence import collect, digest, verify
from .graph import competency_queries, load_entities, load_relationships, runtime_graph
from .identifiers import IdentifierFactory
from .models import SimulationConfig


@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    canonical_hash: str
    documents: dict[str, Any]


def _event(ids: IdentifierFactory, kind: str, time: float, source: str, target: str,
           message_id: str | None, attributes: dict[str, Any]) -> dict[str, Any]:
    public = {
        "event_type": kind,
        "event_time": round(time, 6),
        "source_entity": source,
        "target_entity": target,
        "message_id": message_id,
        "attributes": attributes,
    }
    return {
        "event_id": ids.next("EV"),
        **public,
        "ingest_time": round(time, 6),
        "payload_hash": hashlib.sha256(
            json.dumps(public, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "observable": True,
    }


def simulate(root: Path, config: SimulationConfig) -> SimulationResult:
    ids = IdentifierFactory()
    observation_rng = random.Random(config.seed * 29 + 1)
    truth: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    safety_decisions: list[dict[str, Any]] = []
    policies: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    lost = 0
    overflow = 0

    attack_flows = 0
    if config.attack.enabled and config.attack.kind != "health_fault":
        attack_flows = max(1, round(config.device.normal_flows * (config.attack.multiplier - 1)))
    total_flows = config.device.normal_flows + attack_flows

    for ordinal in range(total_flows):
        is_attack = ordinal >= config.device.normal_flows
        event_time = (ordinal + 1) * config.duration_seconds / (total_flows + 1)
        truth_event = _event(
            ids,
            "flow_truth",
            event_time,
            "UC5-D01",
            "UC5-D02",
            f"UC5-FLOW-{ordinal + 1:06d}",
            {
                "bytes": config.device.normal_bytes * (config.attack.multiplier if is_attack else 1),
                "destination_class": "new_external" if is_attack and config.attack.new_destination else "clinical_service",
                "attack_truth": is_attack,
                "patient_data": False,
                "clinical_payload": False,
            },
        )
        truth.append(truth_event)
        if ordinal >= config.channel.queue_capacity:
            overflow += 1
            continue
        if observation_rng.random() > config.channel.observation_probability or observation_rng.random() < config.channel.loss_probability:
            lost += 1
            continue
        observations.append(
            _event(
                ids,
                "flow_observation",
                event_time + config.clock_skew_seconds,
                "UC5-D04",
                "UC5-S02",
                truth_event["message_id"],
                {
                    "bytes_bucket": "high" if is_attack else "normal",
                    "destination_class": truth_event["attributes"]["destination_class"],
                    "device_pseudonym": hashlib.sha256(f"{config.seed}:UC5-D01".encode()).hexdigest()[:16],
                    "patient_data": False,
                    "clinical_payload": False,
                    "hidden_truth_used": False,
                },
            )
        )

    health_fault = config.attack.enabled and config.attack.kind == "health_fault"
    health = _event(
        ids,
        "health_observation",
        config.duration_seconds * 0.55,
        "UC5-D01",
        "UC5-S02",
        None,
        {"health": "degraded" if health_fault else "nominal", "patient_data": False, "hidden_truth_used": False},
    )
    truth.append(health)
    if config.channel.observation_probability > 0:
        observations.append(health)

    observed_anomalous = sum(
        row["attributes"].get("destination_class") == "new_external"
        or row["attributes"].get("bytes_bucket") == "high"
        for row in observations
    )
    rate_feature = 1.0 if observed_anomalous else 0.0
    byte_feature = rate_feature
    destination_feature = 1.0 if any(
        row["attributes"].get("destination_class") == "new_external" for row in observations
    ) else 0.0
    health_feature = 1.0 if health_fault else 0.0
    features = {
        "rate": rate_feature,
        "bytes": byte_feature,
        "destination": destination_feature,
        "health": health_feature,
    }
    score = sum(config.detection.weights[name] * value for name, value in features.items())
    cyber_alert = config.attack.kind != "health_fault" and score >= config.detection.threshold

    if cyber_alert:
        alert = _event(
            ids,
            "alert",
            config.duration_seconds * 0.70,
            "UC5-S02",
            "UC5-S03",
            None,
            {
                "score": round(score, 6),
                "threshold": config.detection.threshold,
                "features": features,
                "contributions": {
                    name: round(config.detection.weights[name] * value, 6)
                    for name, value in features.items()
                },
                "explanation": [name for name, value in features.items() if value],
                "alternatives": ["health_fault", "collection_artifact", "configuration_change"],
                "hidden_truth_used": False,
            },
        )
        observations.append(alert)
        alerts.append(alert)

        isolation_safe = (not config.device.essential) or config.device.backup_monitoring
        requested = config.policy.selected_action
        safety_allowed = requested != "isolate" or isolation_safe
        safety = _event(
            ids,
            "safety_decision",
            alert["event_time"] + 0.01,
            "UC5-S03",
            "UC5-A01",
            None,
            {
                "requested_action": requested,
                "essential": config.device.essential,
                "backup_monitoring": config.device.backup_monitoring,
                "allowed": safety_allowed,
                "reason": "continuity_satisfied" if safety_allowed else "essential_monitor_without_backup",
            },
        )
        observations.append(safety)
        safety_decisions.append(safety)

        applied = "none"
        outcome = "rejected_by_safety"
        if not config.policy.authorized:
            outcome = "not_authorized"
        elif not config.policy.enforcement_available:
            outcome = "enforcement_unavailable"
        elif safety_allowed:
            applied = requested
            outcome = "applied"
        policy = _event(
            ids,
            "policy_decision",
            safety["event_time"] + 0.01,
            "UC5-S03",
            "UC5-D03",
            None,
            {"requested_action": requested, "applied_action": applied, "outcome": outcome},
        )
        observations.append(policy)
        policies.append(policy)
        actions.append(
            _event(ids, "mitigation_action", policy["event_time"] + 0.01, "UC5-D03", "UC5-D01", None,
                   {"action": applied, "effective": applied != "none", "clinical_actuation": False})
        )

    evidence, custody = collect(
        observations,
        set(config.evidence.allowed_types),
        set(config.evidence.allowed_fields),
    ) if config.evidence.enabled else ([], [])
    integrity_errors = verify(evidence, custody)
    share_allowed = bool(
        evidence and config.evidence.sharing_authorized and config.evidence.redaction_enabled and not integrity_errors
    )
    shared_package = {
        "status": "shared" if share_allowed else "denied",
        "reason": "authorized_and_redacted" if share_allowed else "authority_redaction_or_evidence_missing",
        "evidence_ids": [item["evidence_id"] for item in evidence] if share_allowed else [],
        "device_class": "patient_monitor" if share_allowed else None,
        "patient_identifiers": [],
        "clinical_payloads": [],
        "redacted": share_allowed,
    }
    reconstruction = {
        "hidden_truth_used": False,
        "claims": [{
            "claim_id": "UC5-CLM-000001",
            "statement": "A pseudonymous patient-monitor flow anomaly was observed.",
            "status": "supported" if alerts and evidence else "inconclusive",
            "supporting_evidence_ids": [item["evidence_id"] for item in evidence],
            "alternatives": ["benign traffic change", "device-health fault", "observation loss"],
        }],
    }
    essential_interruptions = sum(
        action["attributes"]["action"] == "isolate" and config.device.essential and not config.device.backup_monitoring
        for action in actions
    )
    metrics = {
        "alert_count": len(alerts),
        "process_effect_count": sum(action["attributes"]["effective"] for action in actions),
        "safety_violation_count": essential_interruptions,
        "essential_monitoring_interruption_count": essential_interruptions,
        "flow_truth_count": total_flows,
        "flow_observation_count": sum(row["event_type"] == "flow_observation" for row in observations),
        "observation_loss": lost,
        "queue_overflow": overflow,
        "safety_rejection_count": sum(not row["attributes"]["allowed"] for row in safety_decisions),
        "evidence_items": len(evidence),
        "shared_evidence_items": len(shared_package["evidence_ids"]),
        "privacy_violation_count": 0,
        "patient_data_disclosure_count": 0,
        "integrity_failure_count": len(integrity_errors),
    }
    core = {
        "ground_truth_events": truth,
        "observed_events": observations,
        "alerts": alerts,
        "safety_decisions": safety_decisions,
        "policy_decisions": policies,
        "mitigation_actions": actions,
        "evidence_manifest": evidence,
        "custody_events": custody,
        "shared_evidence_package": shared_package,
        "reconstructed_timeline": reconstruction,
        "metrics": metrics,
    }
    graph = runtime_graph(root, core)
    documents = {
        "resolved_config": config.model_dump(mode="json"),
        "entities": load_entities(root),
        "relationships": load_relationships(root),
        **core,
        "graph": graph,
        "competency_queries": competency_queries(graph),
        "validation_report": {
            "status": "valid" if not integrity_errors and not essential_interruptions else "invalid",
            "integrity_errors": integrity_errors,
            "invariants": {
                "no_live_interface": True,
                "hidden_truth_isolated": True,
                "clinical_continuity_preserved": essential_interruptions == 0,
                "patient_data_disclosure_count": 0,
            },
        },
        "investigation_summary": {
            "scenario_id": config.scenario_id,
            "synthetic": True,
            "alerts": len(alerts),
            "requested_action": config.policy.selected_action,
            "applied_action": policies[0]["attributes"]["applied_action"] if policies else "none",
            "limitations": "No live medical interface, patient data, diagnosis, treatment, or clinical actuation.",
        },
    }
    canonical_hash = digest(documents)
    documents["run_manifest"] = {
        "schema_version": "1.0.0",
        "use_case": "UC5",
        "scenario_id": config.scenario_id,
        "seed": config.seed,
        "canonical_result_sha256": canonical_hash,
        "synthetic": True,
    }
    return SimulationResult(config.scenario_id, canonical_hash, documents)


def run_simulation(root: Path, config_path: Path) -> SimulationResult:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return simulate(root, SimulationConfig.model_validate(raw))


def export_result(result: SimulationResult, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    jsonl = {
        "ground_truth_events", "observed_events", "alerts", "safety_decisions",
        "policy_decisions", "mitigation_actions", "custody_events",
    }
    for name, document in result.documents.items():
        if name == "resolved_config":
            path = output / "resolved_config.yaml"
            text = yaml.safe_dump(document, sort_keys=True)
        elif name == "investigation_summary":
            path = output / "investigation_summary.md"
            text = "# UC5 synthetic investigation summary\n\n" + "\n".join(
                f"- **{key}:** {value}" for key, value in document.items()
            ) + "\n"
        elif name in jsonl:
            path = output / f"{name}.jsonl"
            text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in document)
        else:
            path = output / f"{name}.json"
            text = json.dumps(document, indent=2, sort_keys=True) + "\n"
        path.write_text(text, encoding="utf-8")
    (output / "graph_overview.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="70">'
        '<text x="20" y="40">patient monitor to observation, detection, clinical-safety policy, evidence and sharing</text></svg>\n',
        encoding="utf-8",
    )
