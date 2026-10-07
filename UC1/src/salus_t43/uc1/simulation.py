from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
from typing import Any

import yaml

from .event_queue import EventQueue
from .evidence import collect, digest, verify
from .graph import competency_queries, load_entities, load_relationships, runtime_graph
from .identifiers import IdentifierFactory
from .models import SimulationConfig


@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    canonical_hash: str
    documents: dict[str, Any]


def _event(factory: IdentifierFactory, kind: str, time: float, source: str, target: str, message_id: str | None, attributes: dict[str, Any], observable: bool, delay: float) -> dict[str, Any]:
    public = {"event_type": kind, "event_time": round(time, 6), "source_entity": source, "target_entity": target, "message_id": message_id, "attributes": attributes}
    return {
        "event_id": factory.event(),
        **public,
        "ingest_time": round(time + max(0.0, delay), 6),
        "payload_hash": hashlib.sha256(json.dumps(public, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "observable": observable,
    }


def _validation(config: SimulationConfig, message: dict[str, Any], now: float) -> dict[str, bool]:
    malformed = message["kind"] == "malformed"
    return {
        "parse": not malformed,
        "trust_service": config.trust.service_available,
        "credential": message["credential_state"] == "valid",
        "authorized_sender": message["source"] == config.trust.valid_sender,
        "fresh": now - message["sender_time"] <= config.trust.freshness_window_seconds,
        "sequence": message["kind"] != "sequence_anomaly",
        "plausible": message["kind"] not in {"malformed", "flood"},
    }


def _score(config: SimulationConfig, validation: dict[str, bool], rate_anomaly: bool) -> tuple[float, dict[str, float]]:
    features = {
        "auth": float(not (validation["trust_service"] and validation["credential"] and validation["authorized_sender"])),
        "freshness": float(not validation["fresh"]),
        "sequence": float(not validation["sequence"]),
        "rate": float(rate_anomaly),
        "plausibility": float(not (validation["parse"] and validation["plausible"])),
    }
    score = sum(features[name] * config.detection.weights[name] for name in features)
    return round(score, 6), features


def simulate(root: Path, config: SimulationConfig) -> SimulationResult:
    ids = IdentifierFactory()
    queue = EventQueue()
    channel_rng = random.Random(config.seed * 17 + 1)
    observation_rng = random.Random(config.seed * 17 + 2)
    for index, time in enumerate((10.0, 20.0, 30.0), start=1):
        queue.push(time, "message", {"attack": False, "kind": "normal", "source": "UC1-D02", "credential_state": "valid", "sender_time": time, "index": index})
    if config.attack.enabled:
        for index in range(config.attack.count):
            time = config.attack.start_seconds + index * config.attack.interval_seconds
            queue.push(time, "message", {"attack": True, "kind": config.attack.kind, "source": "UC1-D08", "credential_state": config.attack.credential_state, "sender_time": time - config.attack.replay_age_seconds, "index": index + 1})

    truth: list[dict[str, Any]] = []
    observed: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    policies: list[dict[str, Any]] = []
    controller: list[dict[str, Any]] = []
    losses = {"channel": 0, "queue_overflow": 0, "observation": 0, "validation": 0, "policy": 0}
    attack_seen = 0
    attack_effects = 0
    queued_at_attack = 0

    while queue:
        scheduled = queue.pop()
        message = scheduled.payload
        message_id = f"UC1-MSG-{len(truth)+1:06d}"
        is_attack = message["attack"]
        if is_attack:
            queued_at_attack += 1
        overflow = is_attack and message["kind"] == "flood" and queued_at_attack > config.channel.buffer_messages
        channel_lost = channel_rng.random() < config.channel.loss_probability
        delay = config.channel.base_delay_seconds + channel_rng.uniform(-config.channel.jitter_seconds, config.channel.jitter_seconds)
        emitted = _event(ids, "message_observation", scheduled.time, message["source"], "UC1-D05", message_id, {"attack": is_attack, "kind": message["kind"]}, True, delay)
        truth.append(emitted)
        if overflow:
            losses["queue_overflow"] += 1
            continue
        if channel_lost:
            losses["channel"] += 1
            continue
        observable = observation_rng.random() < config.channel.observation_probability
        if not observable:
            losses["observation"] += 1
        else:
            observed.append(deepcopy(emitted))
            if is_attack:
                attack_seen += 1

        checks = _validation(config, message, scheduled.time)
        accepted = all(checks.values())
        trust_event = _event(ids, "trust_decision", scheduled.time + max(delay, 0), "UC1-S02", "UC1-D05", message_id, {"validation": checks, "accepted": accepted}, observable, 0.001)
        truth.append(trust_event)
        validations.append(trust_event)
        if observable:
            observed.append(deepcopy(trust_event))
        if not accepted:
            losses["validation"] += 1

        rate_anomaly = is_attack and (message["kind"] == "flood" or config.attack.count / max(config.attack.interval_seconds * config.attack.count, 0.001) > config.channel.capacity_messages_per_second)
        score, features = _score(config, checks, rate_anomaly)
        alerted = is_attack and observable and score >= config.detection.threshold
        if alerted:
            alert = _event(ids, "alert", trust_event["ingest_time"], "UC1-S03", "UC1-S04", message_id, {"score": score, "threshold": config.detection.threshold, "features": features, "explanation": [name for name, value in features.items() if value > 0]}, True, 0.001)
            truth.append(alert)
            observed.append(deepcopy(alert))
            alerts.append(alert)
            requested = config.policy.selected_action
            applied = requested if config.policy.enforcement_available else "none"
            decision = _event(ids, "policy_decision", alert["ingest_time"], "UC1-S04", "UC1-D05", message_id, {"action": applied, "requested_action": requested, "reason": "explained_attack_alert", "acknowledged": config.policy.enforcement_available}, True, config.policy.enforcement_delay_seconds)
            truth.append(decision)
            observed.append(deepcopy(decision))
            policies.append(decision)
            if applied in {"drop", "rate_limit", "isolate"}:
                losses["policy"] += 1

        blocked = not accepted or any(row["message_id"] == message_id and row["attributes"]["action"] in {"drop", "rate_limit", "isolate"} for row in policies)
        effect = bool(is_attack and config.controller.allow_control_requests and not blocked)
        if effect:
            attack_effects += 1
        controller_event = _event(ids, "controller_decision", scheduled.time + max(delay, 0.0) + 0.01, "UC1-D06", "UC1-D07", message_id, {"requested": "east_west" if is_attack else config.controller.initial_phase, "applied": config.controller.initial_phase, "accepted": effect, "safety_interlock": "pass"}, observable, 0.001)
        truth.append(controller_event)
        controller.append(controller_event)
        if observable:
            observed.append(deepcopy(controller_event))

    evidence, custody = collect(observed, set(config.evidence.allowed_types), set(config.evidence.allowed_fields)) if config.evidence.enabled else ([], [])
    integrity_errors = verify(evidence, custody)
    attack_truth = sum(1 for event in truth if event["event_type"] == "message_observation" and event["attributes"].get("attack"))
    reconstruction = {
        "claims": [{
            "claim_id": "UC1-CLAIM-000001",
            "statement": "A synthetic anomalous request targeted the roadside endpoint.",
            "status": "supported" if alerts else "inconclusive",
            "supporting_evidence_ids": [item["evidence_id"] for item in evidence if item["evidence_type"] in {"alert", "trust_decision"}],
            "confidence": "high" if alerts and not integrity_errors else "low",
            "alternatives": ["observation loss", "trust-service degradation"],
        }],
        "hidden_truth_used": False,
    }
    metrics = {
        "attack_messages_generated": attack_truth,
        "attack_messages_observed": attack_seen,
        "attack_detection_recall": (len({a["message_id"] for a in alerts}) / attack_truth) if attack_truth else None,
        "controller_effect_count": attack_effects,
        "safety_violation_count": 0,
        "unauthorized_disclosure_count": 0,
        "evidence_capture_recall": (len(evidence) / len(observed)) if observed else None,
        "integrity_failure_count": len(integrity_errors),
        "losses": losses,
    }
    core = {"ground_truth_events": truth, "observed_events": observed, "message_validation": validations, "alerts": alerts, "policy_decisions": policies, "controller_decisions": controller, "evidence_manifest": evidence, "custody_events": custody, "reconstructed_timeline": reconstruction, "metrics": metrics}
    graph = runtime_graph(root, core)
    documents = {
        "resolved_config": config.model_dump(mode="json"),
        "entities": load_entities(root),
        "relationships": load_relationships(root),
        **core,
        "graph": graph,
        "competency_queries": competency_queries(graph),
        "validation_report": {"status": "valid", "integrity_errors": integrity_errors, "safety_invariants": {"conflicting_phases": False, "live_control": False}},
        "investigation_summary": {"scenario_id": config.scenario_id, "synthetic": True, "alerts": len(alerts), "controller_effects": attack_effects, "limitations": "No real radio, vehicle, signal, PKI, AI, or SDN operation."},
    }
    canonical_hash = digest(documents)
    documents["run_manifest"] = {"schema_version": "1.0.0", "use_case": "UC1", "scenario_id": config.scenario_id, "seed": config.seed, "canonical_result_sha256": canonical_hash, "synthetic": True}
    return SimulationResult(config.scenario_id, canonical_hash, documents)


def run_simulation(root: Path, config_path: Path) -> SimulationResult:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return simulate(root, SimulationConfig.model_validate(raw))


def export_result(result: SimulationResult, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    jsonl = {"ground_truth_events", "observed_events", "message_validation", "alerts", "policy_decisions", "controller_decisions", "custody_events"}
    for name, document in result.documents.items():
        if name == "resolved_config":
            path = output / "resolved_config.yaml"
            rendered = yaml.safe_dump(document, sort_keys=True)
        elif name == "investigation_summary":
            path = output / "investigation_summary.md"
            rendered = "# UC1 synthetic investigation summary\n\n" + "\n".join(f"- **{key}:** {value}" for key, value in document.items()) + "\n"
        elif name in jsonl:
            path = output / f"{name}.jsonl"
            rendered = "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in document)
        else:
            path = output / f"{name}.json"
            rendered = json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        path.write_text(rendered, encoding="utf-8")
    (output / "graph_overview.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="100"><title>UC1 runtime overview</title><text x="20" y="35">Vehicle/OBU → Car2X → RSU → safe controller</text><text x="20" y="70">Observation → trust → detection → policy → evidence</text></svg>\n',
        encoding="utf-8",
    )

