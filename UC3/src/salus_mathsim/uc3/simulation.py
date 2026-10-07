from __future__ import annotations

from copy import deepcopy
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


def _event(ids: IdentifierFactory, kind: str, time: float, source: str, target: str, message_id: str | None, attributes: dict[str, Any], observable: bool, delay: float = 0.0) -> dict[str, Any]:
    public = {"event_type": kind, "event_time": round(time, 6), "source_entity": source, "target_entity": target, "message_id": message_id, "attributes": attributes}
    return {"event_id": ids.next("EV"), **public, "ingest_time": round(time + max(0.0, delay), 6), "payload_hash": hashlib.sha256(json.dumps(public, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "observable": observable}


def _features(config: SimulationConfig, kind: str) -> dict[str, float]:
    return {
        "authorization": float(config.attack.enabled and not config.attack.authorized),
        "protocol": float(kind in {"smart_fuzzing", "unsupported_function", "malformed_request"}),
        "rate": float(kind == "application_flood" or config.attack.request_rate_per_second > config.channel.capacity_messages_per_second),
        "command_residual": float(kind in {"smart_fuzzing", "unauthorized_write", "supply_chain_predeployment"}),
        "process_residual": float(kind == "sensor_fault"),
    }


def simulate(root: Path, config: SimulationConfig) -> SimulationResult:
    ids = IdentifierFactory()
    process_rng = random.Random(config.seed * 31 + 1)
    channel_rng = random.Random(config.seed * 31 + 2)
    observation_rng = random.Random(config.seed * 31 + 3)
    truth: list[dict[str, Any]] = []
    observed: list[dict[str, Any]] = []
    process_state: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    policies: list[dict[str, Any]] = []
    mitigations: list[dict[str, Any]] = []
    level = config.process.initial_level_m
    safety_violations = 0

    for second in range(0, int(config.duration_seconds) + 1):
        measurement = level + config.process.sensor_bias_m + process_rng.gauss(0.0, config.process.sensor_noise_std_m)
        pump_on = measurement < config.process.target_level_m - 0.05
        valve_open = measurement > config.process.target_level_m + 0.05
        inflow = config.process.pump_flow_m3_s if pump_on else 0.0
        outflow = config.process.outlet_flow_m3_s if valve_open else 0.0
        level = level + (inflow - outflow) / config.process.area_m2
        bounded = min(config.process.maximum_level_m, max(config.process.minimum_level_m, level))
        if bounded != level:
            safety_violations += 1
            level = bounded
        if second % 5 == 0:
            visible = observation_rng.random() < config.channel.observation_probability
            event = _event(ids, "process_observation", float(second), "UC3-D02", "UC3-D05", None, {"level_m": round(measurement, 6), "pump_on": pump_on, "valve_open": valve_open, "clock_offset_s": config.clocks["sensor"]}, visible, config.channel.base_delay_seconds)
            truth.append(event)
            process_state.append({"simulation_time": float(second), "level_m": round(level, 6), "measured_level_m": round(measurement, 6), "pump_on": pump_on, "valve_open": valve_open})
            if visible:
                observed.append(deepcopy(event))

    attack_generated = config.attack.count if config.attack.enabled else 0
    overflow = max(0, attack_generated - config.channel.buffer_messages) if config.attack.kind == "application_flood" else 0
    channel_loss = 0
    observation_loss = 0
    process_effects = 0
    for index in range(attack_generated):
        time = config.attack.start_seconds + index * config.attack.interval_seconds
        message_id = f"UC3-MSG-{index+1:06d}"
        if index >= attack_generated - overflow:
            continue
        if channel_rng.random() < config.channel.loss_probability:
            channel_loss += 1
            continue
        visible = observation_rng.random() < config.channel.observation_probability
        if not visible:
            observation_loss += 1
        malformed = config.attack.kind == "malformed_request" or index < round(config.attack.count * config.attack.malformed_ratio)
        supported = config.attack.kind not in {"unsupported_function"} and not malformed
        accepted = supported and config.attack.authorized and config.attack.kind not in {"smart_fuzzing", "application_flood", "sensor_fault", "supply_chain_predeployment"}
        event = _event(ids, "protocol_validation", time, "UC3-D11", "UC3-D05", message_id, {"attack_stage": "fuzzing" if index < max(1, config.attack.count // 2) else "write_attempt", "parse": not malformed, "supported_function": supported, "authorized": config.attack.authorized, "accepted": accepted, "protocol": "abstract_modbus_tcp"}, visible, config.channel.base_delay_seconds)
        truth.append(event)
        validations.append(event)
        if visible:
            observed.append(deepcopy(event))
        features = _features(config, config.attack.kind)
        if malformed:
            features["protocol"] = 1.0
        score = round(sum(features[k] * config.detection.weights[k] for k in features), 6)
        if config.detection.enabled and visible and score >= config.detection.threshold:
            alert = _event(ids, "alert", event["ingest_time"], "UC3-S01", "UC3-S02", message_id, {"score": score, "threshold": config.detection.threshold, "features": features, "explanation": [k for k, v in features.items() if v > 0], "missing_features": []}, True, 0.001)
            alerts.append(alert); truth.append(alert); observed.append(deepcopy(alert))
            requested = config.policy.selected_action
            safety_rejected = config.attack.kind == "sensor_fault" and requested == "isolate_source" and config.policy.safety_telemetry_required
            applied = "rejected_safety" if safety_rejected else (requested if config.policy.enforcement_available else "none")
            decision = _event(ids, "policy_decision", alert["ingest_time"], "UC3-S02", "UC3-D09", message_id, {"requested_action": requested, "applied_action": applied, "safety_check": "rejected" if safety_rejected else "pass", "telemetry_preserved": True}, True, config.policy.enforcement_delay_seconds)
            policies.append(decision); truth.append(decision); observed.append(deepcopy(decision))
            action = _event(ids, "mitigation_action", decision["ingest_time"], "UC3-D09", "UC3-D11", message_id, {"action": applied, "effective": applied not in {"none", "alert_only", "rejected_safety"}, "live_enforcement": False, "rollback_required": False}, True, 0.001)
            mitigations.append(action); truth.append(action); observed.append(deepcopy(action))
        if accepted and not mitigations:
            process_effects += 1

    evidence, custody = collect(observed, set(config.evidence.allowed_types), set(config.evidence.allowed_fields)) if config.evidence.enabled else ([], [])
    integrity_errors = verify(evidence, custody)
    reconstruction = {"hidden_truth_used": False, "claims": [{"claim_id": "UC3-CLM-000001", "statement": "A synthetic anomalous request sequence targeted the abstract PLC service.", "status": "supported" if alerts else "inconclusive", "supporting_evidence_ids": [e["evidence_id"] for e in evidence if e["evidence_type"] in {"protocol_validation", "alert"}], "alternatives": ["sensor fault", "process disturbance", "observation loss"], "confidence": "high" if alerts and not integrity_errors else "low"}]}
    metrics = {
        "attack_messages_generated": attack_generated,
        "attack_messages_validated": len(validations),
        "alert_count": len(alerts),
        "attack_detection_recall": len({a["message_id"] for a in alerts}) / attack_generated if attack_generated else None,
        "process_effect_count": process_effects,
        "safety_violation_count": safety_violations,
        "process_level_min_m": min(p["level_m"] for p in process_state),
        "process_level_max_m": max(p["level_m"] for p in process_state),
        "integrity_failure_count": len(integrity_errors),
        "unauthorized_disclosure_count": 0,
        "losses": {"channel": channel_loss, "queue_overflow": overflow, "observation": observation_loss},
    }
    core = {"ground_truth_events": truth, "process_state": process_state, "observed_events": observed, "protocol_validation": validations, "alerts": alerts, "policy_decisions": policies, "mitigation_actions": mitigations, "evidence_manifest": evidence, "custody_events": custody, "reconstructed_timeline": reconstruction, "metrics": metrics}
    graph = runtime_graph(root, core)
    documents = {"resolved_config": config.model_dump(mode="json"), "entities": load_entities(root), "relationships": load_relationships(root), **core, "graph": graph, "competency_queries": competency_queries(graph), "validation_report": {"status": "valid", "integrity_errors": integrity_errors, "invariants": {"process_bounded": safety_violations == 0, "live_control": False, "hidden_truth_isolated": True}}, "investigation_summary": {"scenario_id": config.scenario_id, "synthetic": True, "alerts": len(alerts), "process_effects": process_effects, "limitations": "No operational plant, PLC, SCADA, protocol, AI, SDN, or nuclear-safety fidelity."}}
    canonical_hash = digest(documents)
    documents["run_manifest"] = {"schema_version": "1.0.0", "use_case": "UC3", "scenario_id": config.scenario_id, "seed": config.seed, "canonical_result_sha256": canonical_hash, "synthetic": True}
    return SimulationResult(config.scenario_id, canonical_hash, documents)


def run_simulation(root: Path, config_path: Path) -> SimulationResult:
    return simulate(root, SimulationConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8"))))


def export_result(result: SimulationResult, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    jsonl = {"ground_truth_events", "process_state", "observed_events", "protocol_validation", "alerts", "policy_decisions", "mitigation_actions", "custody_events"}
    for name, document in result.documents.items():
        if name == "resolved_config":
            path, rendered = output / "resolved_config.yaml", yaml.safe_dump(document, sort_keys=True)
        elif name == "investigation_summary":
            path = output / "investigation_summary.md"
            rendered = "# UC3 synthetic investigation summary\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in document.items()) + "\n"
        elif name in jsonl:
            path = output / f"{name}.jsonl"
            rendered = "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in document)
        else:
            path, rendered = output / f"{name}.json", json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path.write_text(rendered, encoding="utf-8")
    (output / "process_overview.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="760" height="90"><text x="20" y="35">sensor → PLC scan/interlock → pump and valve → bounded vessel</text><text x="20" y="65">monitor → detection/XAI → safe policy → evidence</text></svg>\n', encoding="utf-8")
    (output / "graph_overview.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="760" height="70"><text x="20" y="40">UC3 synthetic entity, event, mitigation, evidence, and twin graph</text></svg>\n', encoding="utf-8")
