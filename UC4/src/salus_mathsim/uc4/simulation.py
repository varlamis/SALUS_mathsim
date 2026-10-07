"""Deterministic end-to-end UC4 discrete-event simulator."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from salus_mathsim.graph_builder import build_graph, graph_document, load_relationships
from salus_mathsim.validation import validate_repository

from .authorization import PolicyDecision, SourceRecord, denial_for_request, evaluate_record
from .collection import CollectedEvidence, canonical_json_bytes, collect_evidence
from .custody import CustodyChain
from .dynamics import ObservationModel
from .entities import DigitalTwin, HomeAssistantState, PhysicalDevice
from .event_queue import EventQueue, ScheduledEvent
from .identifiers import IdentifierFactory
from .metrics import build_metrics
from .models import DeviceConfig, SimulationConfig, UC4Event
from .reconstruction import reconstruct
from .queries import CompetencyQueryEngine
from .runtime_graph import build_runtime_graph, render_graph_overview
from .traffic import CPEQueue


@dataclass(frozen=True, slots=True)
class SimulationResult:
    run_id: str
    canonical_result_hash: str
    documents: dict[str, Any]


class UC4Simulation:
    def __init__(self, root: Path, config: SimulationConfig, validation_report: dict[str, Any]) -> None:
        self.root = root
        self.config = config
        self.validation_report = validation_report
        self.run_id = f"UC4-RUN-{config.random_seed:010d}"
        self.ids = IdentifierFactory()
        self.queue = EventQueue()
        self.observation = ObservationModel(config.random_seed, config.observation, config.network)
        self.cpe_queue = CPEQueue(
            config.network.service_capacity_bits_per_second,
            config.network.buffer_bytes,
            config.network.background_load_fraction,
        )
        self.home_assistant = HomeAssistantState()
        self.truth: list[UC4Event] = []
        self.observed: list[UC4Event] = []
        self.records: list[SourceRecord] = []
        self.policy_decisions: list[PolicyDecision] = []
        self.evidence: list[CollectedEvidence] = []
        self.twin_lags: list[float] = []
        self.losses: dict[str, int] = {"observation": 0, "presence_missed": 0, "queue_overflow": 0, "retention": 0}
        self.losses_by_source: dict[str, int] = {}
        self.processed_keys: list[tuple[float, int]] = []
        self.acquisition_state = "inactive"
        self.reconstruction: dict[str, Any] = {"schema_version": "1.0.0", "observations": [], "claims": []}
        self.custody = CustodyChain(self.run_id, config.authorization.case_id, config.schema_version)
        self.integrity_failures = 0
        self._last_network_time = 0.0
        self._relevant_records = 0
        self._report_time: float | None = None
        self._collection_start_time: float | None = None
        self._collection_bytes = 0

        collection = json.loads((root / "models" / "instances" / "uc4_entities.json").read_text(encoding="utf-8"))
        self.entity_collection = collection
        self.home_assistant.online = not config.faults.home_assistant_unavailable
        by_id = {item["entity_id"]: item for item in collection["entities"]}
        self.devices: dict[str, PhysicalDevice] = {}
        self.twins: dict[str, DigitalTwin] = {}
        for device_id, profile in sorted(config.devices.items()):
            entity = by_id[device_id]
            initial = str(profile.transition_parameters.get("initial_state", entity["lifecycle"]["initial_state"]))
            self.devices[device_id] = PhysicalDevice(
                device_id, initial, frozenset(entity["lifecycle"]["allowed_states"]), initial != "offline",
            )
            twin_id = entity["twin_id"]
            self.twins[twin_id] = DigitalTwin(twin_id, device_id)

    def run(self) -> SimulationResult:
        self._schedule_initial_events()
        while self.queue:
            scheduled = self.queue.pop()
            if scheduled.simulation_time > self.config.time.horizon:
                break
            self.processed_keys.append((scheduled.simulation_time, scheduled.sequence))
            self._dispatch(scheduled)
        self._assert_invariants()
        return self._build_result()

    def _schedule_initial_events(self) -> None:
        correlation = (self.ids.next("correlation"),)
        for index, device_id in enumerate(sorted(self.devices)):
            if self.config.devices[device_id].enabled:
                self.queue.schedule(
                    self.config.time.warmup + index * 0.01, "device_snapshot", device_id,
                    payload={"event_type": "device.heartbeat"}, correlation_ids=correlation,
                )
        if self.config.incident.enabled:
            incident_correlation = (self.ids.next("correlation"),)
            self.queue.schedule(self.config.time.entry, "entry", "UC4-A05", "UC4-D03", correlation_ids=incident_correlation)
            self.queue.schedule(self.config.time.tamper, "tamper", "UC4-A05", "UC4-D03", correlation_ids=incident_correlation)
            self.queue.schedule(self.config.time.case_trigger, "case_trigger", "UC4-A02", "UC4-DO06", correlation_ids=incident_correlation)
            self.queue.schedule(self.config.time.request, "acquisition_request", "UC4-A02", "UC4-S02", correlation_ids=incident_correlation)

    def _dispatch(self, event: ScheduledEvent) -> None:
        handlers = {
            "device_snapshot": self._handle_snapshot,
            "entry": self._handle_entry,
            "tamper": self._handle_tamper,
            "disconnect": self._handle_disconnect,
            "observation": self._handle_observation,
            "ha_ingest": self._handle_ha_ingest,
            "automation": self._handle_automation,
            "light_ack": self._handle_light_ack,
            "twin_sync": self._handle_twin_sync,
            "case_trigger": self._handle_case_trigger,
            "acquisition_request": self._handle_acquisition_request,
            "acquisition_execute": self._handle_acquisition_execute,
        }
        try:
            handler = handlers[event.kind]
        except KeyError as exc:
            raise RuntimeError(f"unknown scheduled event kind: {event.kind}") from exc
        handler(event)

    def _handle_snapshot(self, scheduled: ScheduledEvent) -> None:
        device = self.devices[scheduled.source]
        self._emit_device_candidate(scheduled, "device.heartbeat", device.state, device.version)

    def _handle_entry(self, scheduled: ScheduledEvent) -> None:
        door = self.devices["UC4-D03"]
        if door.transition("open_online", scheduled.simulation_time):
            self._emit_truth("UC4-D03", "door.open", scheduled.simulation_time, {
                "state": door.state, "version": door.version, "context": "armed_unoccupied",
            }, scheduled.correlation_ids, observe=True)
        self._emit_truth("UC4-ENV01", "presence.true_movement", scheduled.simulation_time, {
            "occupancy": "intruder_present", "restricted": True,
        }, scheduled.correlation_ids, observe=False)
        if not self.config.faults.force_presence_miss and self.observation.detected("UC4-D04", self.config.observation.presence_detection_probability):
            presence = self.devices["UC4-D04"]
            if presence.transition("motion_online", scheduled.simulation_time):
                self._emit_truth("UC4-D04", "presence.motion", scheduled.simulation_time, {
                    "state": presence.state, "version": presence.version,
                }, scheduled.correlation_ids, observe=True, extra_delay=self.config.observation.presence_reporting_delay_seconds)
        else:
            self._record_loss("presence_missed", "UC4-D04")

    def _handle_tamper(self, scheduled: ScheduledEvent) -> None:
        door = self.devices["UC4-D03"]
        if self.config.incident.tamper_strategy == "tampered_then_offline" and door.transition("tampered", scheduled.simulation_time):
            self._emit_truth("UC4-D03", "device.tamper", scheduled.simulation_time, {
                "state": door.state, "version": door.version,
            }, scheduled.correlation_ids, observe=True)
        delay = self.config.devices["UC4-D03"].processing_delay_seconds
        self.queue.schedule(scheduled.simulation_time + delay, "disconnect", "UC4-D03", payload={}, correlation_ids=scheduled.correlation_ids)

    def _handle_disconnect(self, scheduled: ScheduledEvent) -> None:
        door = self.devices["UC4-D03"]
        previous = door.state
        if door.transition("offline", scheduled.simulation_time):
            self._emit_truth("UC4-D03", "device.offline", scheduled.simulation_time, {
                "state": door.state, "last_logical_state": previous, "version": door.version,
            }, scheduled.correlation_ids, observe=True)

    def _emit_device_candidate(self, scheduled: ScheduledEvent, event_type: str, state: str, version: int) -> None:
        self._emit_truth(scheduled.source, event_type, scheduled.simulation_time, {
            "state": state, "version": version,
        }, scheduled.correlation_ids, observe=True)

    def _emit_truth(
        self, source: str, event_type: str, true_time: float, payload: dict[str, Any],
        correlation_ids: tuple[str, ...], observe: bool, extra_delay: float = 0.0,
    ) -> None:
        truth = self._event(source, event_type, true_time, true_time, payload, correlation_ids, "ground_truth_only", "exact")
        self.truth.append(truth)
        if not observe:
            return
        if source == "UC4-D03" and event_type == "door.open" and self.config.faults.force_door_observation_loss:
            self._record_loss("observation", source)
            return
        profile = self.config.devices.get(source)
        if profile is None or not profile.enabled or not self.observation.delivered(source, profile):
            self._record_loss("observation", source)
            return
        local_time = self.observation.local_time(source, true_time, profile)
        ingest = true_time + profile.processing_delay_seconds + extra_delay + self.observation.network_delay(source)
        self.queue.schedule(ingest, "observation", source, "UC4-D02", payload={
            "event_type": event_type,
            "event_time": local_time,
            "true_time": true_time,
            "state_payload": payload,
        }, correlation_ids=correlation_ids)

    def _handle_observation(self, scheduled: ScheduledEvent) -> None:
        event_type = scheduled.payload["event_type"]
        payload = dict(scheduled.payload["state_payload"])
        event = self._event(
            scheduled.source, event_type, scheduled.payload["event_time"], scheduled.simulation_time,
            payload, scheduled.correlation_ids, "observable", "estimated",
        )
        self.observed.append(event)
        record = self._record_from_event(event, scheduled.source, "device_state_event", "export_state")
        self._retain(record, scheduled.simulation_time)
        self._record_cpe_flow(event, scheduled.simulation_time)
        if scheduled.source in {"UC4-D03", "UC4-D04", "UC4-D05", "UC4-D06"}:
            self.queue.schedule(scheduled.simulation_time, "ha_ingest", "UC4-D02", payload={
                "device_id": scheduled.source, "event_type": event_type,
                "event_time": event.event_time, "state_payload": payload,
            }, correlation_ids=scheduled.correlation_ids)
        device = self.devices.get(scheduled.source)
        if device:
            self.queue.schedule(scheduled.simulation_time, "twin_sync", "UC4-S06", payload={
                "device_id": scheduled.source, "state": payload.get("state", device.state),
                "version": payload.get("version", device.version), "event_time": event.event_time,
            }, correlation_ids=scheduled.correlation_ids)

    def _handle_ha_ingest(self, scheduled: ScheduledEvent) -> None:
        payload = scheduled.payload
        state_payload = payload["state_payload"]
        ha_record = self._new_record(
            "UC4-D02", payload["device_id"], "home_assistant_event", "read_historical",
            payload["event_time"], payload["event_type"], state_payload.get("state"),
            scheduled.simulation_time, scheduled.correlation_ids, "estimated",
        )
        ha_record.content["source"] = payload["device_id"]
        accepted = self.home_assistant.ingest(
            payload["device_id"], int(state_payload.get("version", 0)),
            str(state_payload.get("state", "unknown")), ha_record.content,
            self.config.retention.home_assistant_max_events,
        )
        if not accepted:
            return
        self._retain(ha_record, scheduled.simulation_time)
        if payload["event_type"] == "door.open" and self.config.incident.light_automation_enabled:
            self.queue.schedule(
                scheduled.simulation_time + self.config.incident.home_assistant_automation_delay_seconds,
                "automation", "UC4-D02", "UC4-D06", correlation_ids=scheduled.correlation_ids,
            )

    def _handle_automation(self, scheduled: ScheduledEvent) -> None:
        event = self._event("UC4-D02", "automation.triggered", scheduled.simulation_time, scheduled.simulation_time, {
            "rule": "entry_light", "command": "light.on", "target": "UC4-D06",
        }, scheduled.correlation_ids, "observable", "exact")
        self.observed.append(event)
        self._retain(self._record_from_event(event, "UC4-D06", "home_assistant_event", "read_historical"), scheduled.simulation_time)
        self._record_cpe_flow(event, scheduled.simulation_time)
        self.queue.schedule(
            scheduled.simulation_time + self.config.incident.light_acknowledgement_delay_seconds,
            "light_ack", "UC4-D06", payload={}, correlation_ids=scheduled.correlation_ids,
        )

    def _handle_light_ack(self, scheduled: ScheduledEvent) -> None:
        light = self.devices["UC4-D06"]
        if light.online and light.transition("on_online", scheduled.simulation_time):
            self._emit_truth("UC4-D06", "light.on", scheduled.simulation_time, {
                "state": light.state, "version": light.version,
            }, scheduled.correlation_ids, observe=True)

    def _handle_twin_sync(self, scheduled: ScheduledEvent) -> None:
        device_id = scheduled.payload["device_id"]
        twin_id = f"UC4-DT{device_id[-2:]}"
        accepted = self.twins[twin_id].synchronize(
            int(scheduled.payload["version"]), str(scheduled.payload["state"]),
            float(scheduled.payload["event_time"]), scheduled.simulation_time,
        )
        if accepted and self.twins[twin_id].lag is not None:
            self.twin_lags.append(float(self.twins[twin_id].lag))

    def _handle_case_trigger(self, scheduled: ScheduledEvent) -> None:
        self.acquisition_state = "request_received"
        self.observed.append(self._event(
            "UC4-DO06", "case.triggered", scheduled.simulation_time, scheduled.simulation_time,
            {"case_id": self.config.authorization.case_id, "collection_active": False},
            scheduled.correlation_ids, "observable", "exact",
        ))

    def _handle_acquisition_request(self, scheduled: ScheduledEvent) -> None:
        self.queue.schedule(
            scheduled.simulation_time + self.config.collection.start_delay_seconds,
            "acquisition_execute", scheduled.source, scheduled.target,
            payload=scheduled.payload, correlation_ids=scheduled.correlation_ids,
        )

    def _handle_acquisition_execute(self, scheduled: ScheduledEvent) -> None:
        self._collection_start_time = scheduled.simulation_time
        authorization = self.config.authorization
        if authorization.decision_path != "allow":
            self.acquisition_state = "denied"
            self.policy_decisions.append(denial_for_request(authorization, scheduled.simulation_time, self.ids.next("policy")))
            self.reconstruction = self._reconstruct([])
            self._report_time = scheduled.simulation_time
            return
        self.acquisition_state = "collecting"
        retained = self._retained_at(scheduled.simulation_time)
        if not retained:
            self.policy_decisions.append(PolicyDecision(
                self.ids.next("policy"), authorization.authorization_id, None, "deny",
                "source_window_empty", scheduled.simulation_time, (), 0,
            ))
            self.acquisition_state = "denied"
            self.reconstruction = self._reconstruct([])
            self._report_time = scheduled.simulation_time
            return
        for record in retained:
            decision, projection = evaluate_record(
                authorization, record, scheduled.simulation_time, self.ids.next("policy"), authorization.purpose,
            )
            if (
                authorization.evidence_window_start <= record.event_time < authorization.evidence_window_end
                and record.subject_entity in authorization.allowed_entities
                and record.data_type in authorization.allowed_data_types
            ):
                self._relevant_records += 1
            if projection is None:
                self.policy_decisions.append(decision)
                continue
            acquisition_time = scheduled.simulation_time + (len(self.evidence) + 1) * 0.001
            released_bytes = len(canonical_json_bytes(projection))
            self._collection_bytes += released_bytes
            decision = replace(decision, bytes_released=released_bytes)
            collected = collect_evidence(
                self.ids.next("evidence"), record, projection, decision, acquisition_time,
            )
            self.policy_decisions.append(decision)
            self.custody.append(
                self.ids.next("custody"), collected.item.evidence_id, collected.item.content_hash,
                "registered", acquisition_time, "UC4-S03",
            )
            verified = collected.verify_content() and self.custody.verify()
            self.custody.append(
                self.ids.next("custody"), collected.item.evidence_id, collected.item.content_hash,
                "verified" if verified else "verification_failed", acquisition_time + 0.0001, "UC4-S04",
            )
            status = "verified" if verified and self.custody.verify() else "verification_failed"
            self.evidence.append(CollectedEvidence(collected.item.model_copy(update={"custody_status": status}), collected.content))
        self._apply_integrity_faults()
        self.acquisition_state = "completed"
        self.reconstruction = self._reconstruct(self.evidence)
        self._report_time = max(
            scheduled.simulation_time,
            max((item.item.acquisition_time for item in self.evidence), default=scheduled.simulation_time),
        )

    def _reconstruct(self, evidence: list[CollectedEvidence]) -> dict[str, Any]:
        return reconstruct(
            evidence,
            self.config.reconstruction,
            uncertainty_seconds=self._timestamp_uncertainty(),
            clock_offsets={device_id: profile.clock_offset_seconds for device_id, profile in self.config.devices.items()},
        )

    def _timestamp_uncertainty(self) -> float:
        return (
            self.config.observation.clock_offset_bound_seconds
            + self.config.observation.timestamp_jitter_bound_seconds
            + self.config.network.base_delay_seconds
            + self.config.network.jitter_bound_seconds
        )

    def _apply_integrity_faults(self) -> None:
        if self.config.faults.evidence_tamper_after_collection and self.evidence:
            first = self.evidence[0]
            corrupted_content = {**first.content, "fault_injected": "post_collection_tamper"}
            failed_item = first.item.model_copy(update={"custody_status": "verification_failed"})
            self.evidence[0] = CollectedEvidence(failed_item, corrupted_content)
            self.integrity_failures += 1
        if self.config.faults.custody_tamper_after_append and self.custody.records:
            self.custody.records[0] = replace(self.custody.records[0], action="tampered_action")
            self.evidence = [
                CollectedEvidence(item.item.model_copy(update={"custody_status": "verification_failed"}), item.content)
                for item in self.evidence
            ]
            self.integrity_failures += 1

    def _event(
        self, source: str, event_type: str, event_time: float, ingest_time: float,
        payload: dict[str, Any], correlation_ids: tuple[str, ...], visibility: str, quality: str,
    ) -> UC4Event:
        return UC4Event.model_validate({
            "schema_version": "1.0.0", "event_id": self.ids.next("event"), "use_case": "UC4",
            "event_time": event_time, "ingest_time": ingest_time, "source_entity": source,
            "target_entity": None, "event_type": event_type, "payload": payload,
            "correlation_ids": list(correlation_ids),
            "provenance": {"source_record_id": None, "sequence": len(self.truth) + len(self.observed), "clock_domain": f"{source}-clock", "quality": quality},
            "visibility": visibility,
        })

    def _record_from_event(self, event: UC4Event, subject: str, data_type: str, action: str) -> SourceRecord:
        return self._new_record(
            event.source_entity, subject, data_type, action, event.event_time, event.event_type,
            event.payload.get("state"), event.ingest_time, tuple(event.correlation_ids), event.provenance.quality,
        )

    def _new_record(
        self, source: str, subject: str, data_type: str, action: str, event_time: float,
        event_type: str, state: Any, ingest_time: float, correlation_ids: tuple[str, ...], quality: str,
    ) -> SourceRecord:
        record_id = self.ids.next("record")
        content = {
            "record_id": record_id, "entity_id": subject, "event_type": event_type,
            "event_time": event_time, "ingest_time": ingest_time, "state": state,
            "source": source, "correlation_ids": list(correlation_ids), "quality": quality,
            "internal_sequence": len(self.records),
        }
        return SourceRecord(record_id, source, subject, data_type, action, event_time, content)

    def _record_cpe_flow(self, event: UC4Event, simulation_time: float) -> None:
        if not self.config.network.logging_enabled or self.config.faults.cpe_unavailable:
            if self.config.faults.cpe_unavailable:
                self._record_loss("cpe_unavailable", "UC4-D01")
            return
        encoded_size = len(canonical_json_bytes(event.model_dump(mode="json", exclude_none=True)))
        elapsed = max(0.0, simulation_time - self._last_network_time)
        update = self.cpe_queue.update(encoded_size, elapsed)
        self._last_network_time = simulation_time
        if update.dropped_bytes > 0:
            self._record_loss("queue_overflow", "UC4-D01")
            return
        cpe_record = self._new_record(
            "UC4-D01", "UC4-D01", "cpe_flow_metadata", "export_metadata", event.event_time,
            "cpe.flow", None, simulation_time, tuple(event.correlation_ids), "estimated",
        )
        cpe_record.content["source"] = event.source_entity
        self._retain(cpe_record, simulation_time)

    def _retain(self, record: SourceRecord, simulation_time: float) -> None:
        self.records.append(record)
        cutoff = simulation_time - self.config.retention.nominal_seconds
        expired = [item for item in self.records if item.event_time < cutoff]
        self.records = [item for item in self.records if item.event_time >= cutoff]
        for item in expired:
            self._record_loss("retention", item.source_entity)
        cpe_records = [item for item in self.records if item.source_entity == "UC4-D01"]
        size = sum(len(canonical_json_bytes(item.content)) for item in cpe_records)
        while size > self.config.retention.cpe_max_bytes and cpe_records:
            victim = cpe_records.pop(0)
            self.records.remove(victim)
            size -= len(canonical_json_bytes(victim.content))
            self._record_loss("retention", victim.source_entity)

    def _record_loss(self, cause: str, source: str, count: int = 1) -> None:
        self.losses[cause] = self.losses.get(cause, 0) + count
        key = f"{source}:{cause}"
        self.losses_by_source[key] = self.losses_by_source.get(key, 0) + count

    def _retained_at(self, simulation_time: float) -> list[SourceRecord]:
        cutoff = simulation_time - self.config.retention.nominal_seconds
        return [record for record in self.records if record.event_time >= cutoff]

    def _assert_invariants(self) -> None:
        if self.processed_keys != sorted(self.processed_keys):
            raise RuntimeError("processed event keys are not monotonic")
        all_ids = [event.event_id for event in self.truth + self.observed]
        if len(all_ids) != len(set(all_ids)):
            raise RuntimeError("duplicate event identifier")
        for device in self.devices.values():
            if device.state not in device.allowed_states or device.version < 0:
                raise RuntimeError(f"invalid final state for {device.entity_id}")
        clock_bound = (
            self.config.observation.clock_offset_bound_seconds
            + self.config.observation.timestamp_jitter_bound_seconds
        )
        if any(event.ingest_time < event.event_time - clock_bound for event in self.observed):
            raise RuntimeError("event-time causality bound violated")
        if self.cpe_queue.occupancy_bytes < 0 or self.cpe_queue.occupancy_bytes > self.cpe_queue.buffer_bytes:
            raise RuntimeError("CPE queue outside bounds")
        custody_valid = self.custody.verify()
        if not custody_valid and not self.config.faults.custody_tamper_after_append:
            raise RuntimeError("custody chain verification failed")
        if self.config.faults.custody_tamper_after_append and custody_valid:
            raise RuntimeError("configured custody corruption was not detected")
        if any(item.item.custody_status == "verified" and not item.verify_content() for item in self.evidence):
            raise RuntimeError("corrupt evidence retained verified status")
        denied_bytes = sum(item.bytes_released for item in self.policy_decisions if item.decision == "deny")
        if denied_bytes:
            raise RuntimeError("deny decision released protected bytes")
        if not self.config.network.payload_capture_enabled is False:
            raise RuntimeError("payload capture invariant violated")

    def _build_result(self) -> SimulationResult:
        latencies = [item.item.acquisition_time - self.config.time.request for item in self.evidence]
        denied_bytes = sum(item.bytes_released for item in self.policy_decisions if item.decision == "deny")
        metrics = build_metrics(
            self._relevant_records, len(self.evidence), denied_bytes, latencies,
            self.twin_lags, self.cpe_queue.total_arrivals,
            self.cpe_queue.total_dropped, self.cpe_queue.maximum_occupancy_bytes, self.losses,
        )
        metrics["integrity"] = {
            "content_and_custody_verified": self.integrity_failures == 0 and self.custody.verify(),
            "detected_failures": self.integrity_failures,
            "quarantined_evidence_items": sum(item.item.custody_status == "verification_failed" for item in self.evidence),
        }
        metrics["losses_by_source_and_cause"] = dict(sorted(self.losses_by_source.items()))
        metrics["investigation_latency_seconds"] = (
            self._report_time - self.config.time.case_trigger
            if self._report_time is not None and self.config.incident.enabled else None
        )
        metrics["reconstruction"] = self._evaluate_reconstruction()
        last_updates = [twin.update_time for twin in self.twins.values() if twin.update_time is not None]
        stale_time = sum(
            max(0.0, self.config.time.horizon - (update_time + self.config.digital_twin.stale_threshold_seconds))
            for update_time in last_updates
        )
        metrics["twins"]["stale_state_fraction"] = (
            stale_time / (self.config.time.horizon * len(self.twins)) if self.twins else None
        )
        metrics["network"]["modeled_utilization"] = (
            self.cpe_queue.total_served / self.cpe_queue.total_service_capacity
            if self.cpe_queue.total_service_capacity else None
        )
        metrics["network"]["background_load_fraction"] = self.config.network.background_load_fraction
        acquisition_duration = max(0.001, len(self.evidence) * 0.001)
        acquisition_capacity = self.cpe_queue.service_bytes_per_second * acquisition_duration
        metrics["network"]["acquisition"] = {
            "transferred_bytes": self._collection_bytes,
            "modeled_duration_seconds": acquisition_duration if self._collection_start_time is not None else None,
            "utilization": min(1.0, self._collection_bytes / acquisition_capacity) if self._collection_start_time is not None and acquisition_capacity else None,
            "maximum_queue_occupancy_bytes": min(self._collection_bytes, self.config.network.buffer_bytes) if self._collection_start_time is not None else None,
            "dropped_bytes": max(0, self._collection_bytes - self.config.network.buffer_bytes) if self._collection_start_time is not None else None,
            "loss_rate": (
                max(0, self._collection_bytes - self.config.network.buffer_bytes) / self._collection_bytes
                if self._collection_start_time is not None and self._collection_bytes else None
            ),
        }
        enabled = set(self.config.topology.enabled_entities)
        entities = {
            **{key: value for key, value in self.entity_collection.items() if key != "entities"},
            "entities": [item for item in self.entity_collection["entities"] if item["entity_id"] in enabled],
        }
        relationships_path = self.root / "models" / "relationships" / "uc4_relationships.csv"
        relationships = [
            item for item in load_relationships(relationships_path)
            if item["source_entity"] in enabled and item["target_entity"] in enabled
        ]
        metrics["assumption_coverage"] = self._assumption_coverage(entities["entities"], relationships)
        graph = build_graph(entities, relationships)
        static_graph = graph_document(graph, sources=[self.root / "models" / "instances" / "uc4_entities.json", relationships_path])
        static_graph["metadata"].pop("generated_at", None)
        event_documents = [item.model_dump(mode="json") for item in self.observed]
        policy_documents = [item.as_dict() for item in self.policy_decisions]
        evidence_document = {
            "schema_version": "1.0.0",
            "evidence": [{"item": item.item.model_dump(mode="json"), "content": item.content} for item in self.evidence],
        }
        custody_documents = [item.as_dict() for item in self.custody.records]
        graph_json = build_runtime_graph(
            self.run_id, static_graph, event_documents, policy_documents,
            evidence_document, custody_documents, self.reconstruction,
        )
        graph_schema = json.loads((self.root / "models" / "schemas" / "runtime_graph.schema.json").read_text(encoding="utf-8"))
        graph_errors = list(Draft202012Validator(graph_schema).iter_errors(graph_json))
        if graph_errors:
            raise RuntimeError("runtime graph schema violation: " + "; ".join(error.message for error in graph_errors[:5]))
        competency_queries = CompetencyQueryEngine(graph_json).run()
        graph_overview_svg = render_graph_overview(graph_json)
        deterministic_documents: dict[str, Any] = {
            "resolved_config": self.config.model_dump(mode="json"),
            "entities": entities,
            "relationships": relationships,
            "ground_truth_events": [item.model_dump(mode="json") for item in self.truth],
            "observed_events": event_documents,
            "policy_decisions": policy_documents,
            "evidence_manifest": evidence_document,
            "custody_events": custody_documents,
            "reconstructed_timeline": self.reconstruction,
            "graph": graph_json,
            "competency_queries": competency_queries,
            "graph_overview_svg": graph_overview_svg,
            "metrics": metrics,
            "validation_report": {**self.validation_report, "dynamic_invariants": "valid"},
        }
        canonical_hash = hashlib.sha256(canonical_json_bytes(deterministic_documents)).hexdigest()
        manifest = {
            "schema_version": "1.0.0", "run_id": self.run_id,
            "scenario_id": self.config.scenario_id, "random_seed": self.config.random_seed,
            "deterministic": self.config.deterministic, "canonical_result_sha256": canonical_hash,
            "generation_time_utc": datetime.now(timezone.utc).isoformat(),
            "generation_time_excluded_from_canonical_hash": True,
        }
        summary = _investigation_summary(self.config, self.evidence, self.reconstruction, metrics, canonical_hash)
        return SimulationResult(self.run_id, canonical_hash, {"run_manifest": manifest, **deterministic_documents, "investigation_summary": summary})

    def _evaluate_reconstruction(self) -> dict[str, Any]:
        relevant_types = {"door.open", "presence.motion", "light.on", "device.tamper", "device.offline"}
        truth = [event for event in self.truth if event.event_type in relevant_types]
        reconstructed = [
            item for item in self.reconstruction.get("observations", [])
            if item.get("event_type") in relevant_types and isinstance(item.get("estimated_time"), (int, float))
        ]
        unused = set(range(len(reconstructed)))
        errors: list[float] = []
        for event in truth:
            candidates = [index for index in unused if reconstructed[index]["event_type"] == event.event_type]
            if not candidates:
                continue
            selected = min(candidates, key=lambda index: abs(reconstructed[index]["estimated_time"] - event.event_time))
            unused.remove(selected)
            errors.append(abs(reconstructed[selected]["estimated_time"] - event.event_time))
        matched = len(errors)
        return {
            "ground_truth_relevant_events": len(truth),
            "reconstructed_relevant_events": len(reconstructed),
            "matched_events": matched,
            "recall": matched / len(truth) if truth else None,
            "precision": matched / len(reconstructed) if reconstructed else None,
            "timestamp_mean_absolute_error_seconds": sum(errors) / matched if matched else None,
            "evaluation_only_ground_truth_access": True,
        }

    @staticmethod
    def _assumption_coverage(entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, Any]:
        statuses = [item["provenance"]["record_status"] for item in entities]
        statuses.extend(item["record_status"] for item in relationships)
        counts = {status: statuses.count(status) for status in ("proposal", "roadmap", "agreed_decision", "assumed", "proposed", "TBD")}
        total = len(statuses)
        return {
            "model_records": total,
            "counts": counts,
            "fractions": {status: count / total if total else None for status, count in counts.items()},
            "assumed_or_tbd_fraction": (counts["assumed"] + counts["TBD"]) / total if total else None,
        }


def run_simulation(root: Path, config_path: Path) -> SimulationResult:
    report, _ = validate_repository(root, config_path)
    try:
        report["config"] = config_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        report["config"] = config_path.name
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8-sig"))
    config = SimulationConfig.model_validate(raw)
    return UC4Simulation(root, config, report).run()


def export_result(result: SimulationResult, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    json_files = {
        "run_manifest.json": "run_manifest", "entities.json": "entities",
        "relationships.json": "relationships", "evidence_manifest.json": "evidence_manifest",
        "reconstructed_timeline.json": "reconstructed_timeline", "graph.json": "graph",
        "competency_queries.json": "competency_queries",
        "metrics.json": "metrics", "validation_report.json": "validation_report",
    }
    for filename, key in json_files.items():
        (output_directory / filename).write_bytes(canonical_json_bytes(result.documents[key]) + b"\n")
    for filename, key in {
        "ground_truth_events.jsonl": "ground_truth_events", "observed_events.jsonl": "observed_events",
        "policy_decisions.jsonl": "policy_decisions", "custody_events.jsonl": "custody_events",
    }.items():
        content = b"".join(canonical_json_bytes(item) + b"\n" for item in result.documents[key])
        (output_directory / filename).write_bytes(content)
    (output_directory / "resolved_config.yaml").write_text(
        yaml.safe_dump(result.documents["resolved_config"], sort_keys=False), encoding="utf-8",
    )
    (output_directory / "investigation_summary.md").write_text(
        result.documents["investigation_summary"], encoding="utf-8",
    )
    (output_directory / "graph_overview.svg").write_text(
        result.documents["graph_overview_svg"], encoding="utf-8",
    )


def _investigation_summary(
    config: SimulationConfig, evidence: list[CollectedEvidence], reconstruction: dict[str, Any],
    metrics: dict[str, Any], canonical_hash: str,
) -> str:
    claims = "\n".join(
        f"- {claim['claim_type']}: {claim['qualification']} (support {claim['support_score']})"
        for claim in reconstruction.get("claims", [])
    ) or "- No evidence-supported claims were produced."
    return f"""# UC4 synthetic investigation summary

Scenario: `{config.scenario_id}`  
Seed: `{config.random_seed}`  
Authorization path: `{config.authorization.decision_path}`  
Verified evidence items: `{len(evidence)}`  
Canonical result SHA-256: `{canonical_hash}`

## Qualified technical findings

{claims}

## Privacy and integrity

- Unauthorized disclosure bytes: `{metrics['privacy']['unauthorized_disclosure_bytes']}`.
- Payload capture: disabled.
- Reconstruction input: verified collected evidence only; hidden ground truth is excluded.

## Limitations

This is a synthetic, uncalibrated technical simulation. It does not establish identity, intent, guilt, legal admissibility, GDPR compliance, real-device fidelity, production readiness, or pilot KPI attainment.
"""
