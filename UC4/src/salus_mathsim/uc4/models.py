"""Strict Pydantic mirrors of the UC4 interchange contracts."""

from __future__ import annotations

from pathlib import PurePath
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0.0"
UC4_ID = r"^UC4(?:-[A-Z]{1,3}[0-9]{2})?$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Lifecycle(StrictModel):
    initial_state: str = Field(min_length=1)
    allowed_states: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def initial_is_allowed(self) -> "Lifecycle":
        if len(self.allowed_states) != len(set(self.allowed_states)):
            raise ValueError("allowed_states must be unique")
        if self.initial_state not in self.allowed_states:
            raise ValueError("initial_state must occur in allowed_states")
        return self


class Interface(StrictModel):
    name: str = Field(min_length=1)
    kind: Literal["physical", "network", "application", "policy", "storage", "simulation", "human"]
    direction: Literal["in", "out", "bidirectional"]
    protocol: str = Field(min_length=1)
    status: Literal["confirmed", "abstract", "proposed", "TBD", "disabled"]


class EntityData(StrictModel):
    generates: list[str]
    consumes: list[str]


class Provenance(StrictModel):
    source_references: list[str] = Field(min_length=1)
    record_status: Literal["proposal", "roadmap", "agreed_decision", "assumed", "proposed", "TBD"]
    confidence: Literal["low", "medium", "high"]
    assumption_ids: list[str]


class Entity(StrictModel):
    schema_version: Literal["1.0.0"]
    entity_id: str = Field(pattern=UC4_ID)
    use_case: Literal["UC4"]
    name: str = Field(min_length=1, max_length=160)
    entity_class: Literal[
        "UseCase", "PhysicalEnvironment", "NetworkZone", "Gateway", "GatewayServer",
        "Sensor", "SensorActuator", "Actuator", "TwinEntity", "CloudService",
        "ForensicsService", "DigitalTwinService", "HumanActor", "LEAUser",
        "HumanOrganisationActor", "OrganisationSystemActor", "SystemActor",
        "PolicyDataObject", "NetworkFlowLogEntry", "EventLogEntry", "EventTelemetry",
        "EvidenceItem", "Alert", "PolicyDecision", "CustodyEvent", "AnalysisResult",
    ]
    parent_class: str = Field(min_length=1)
    designation: Literal["physical", "digital", "logical"]
    owner_operator: str = Field(min_length=1)
    location: str = Field(min_length=1)
    network_zones: list[str]
    role: str = Field(min_length=1)
    lifecycle: Lifecycle
    capabilities: list[str]
    interfaces: list[Interface]
    data: EntityData
    twin_id: str | None = Field(default=None, pattern=r"^UC4-DT[0-9]{2}$")
    physical_entity_id: str | None = Field(default=None, pattern=r"^UC4-D[0-9]{2}$")
    clock_domain: str | None = None
    provenance: Provenance
    sensitivity: Literal["Low", "Medium", "High", "Critical"]
    retention_class: Literal["none", "configuration", "scenario", "bounded_source", "run_retention", "case_retention", "restricted_truth", "external_TBD"]
    observability: Literal["observable", "partially_observable", "latent", "derived_observable", "fully_audited", "audited_interface", "read_only_audited", "policy_visible", "collector_if_authorized", "authorized_access_only", "investigator_visible", "evidence_only", "not_observable_when_disabled"]
    notes: str | None = None

    @model_validator(mode="after")
    def entity_invariants(self) -> "Entity":
        if self.entity_class == "TwinEntity" and (not self.physical_entity_id or not self.clock_domain):
            raise ValueError("TwinEntity requires physical_entity_id and clock_domain")
        if re.fullmatch(r"UC4-D[0-9]{2}", self.entity_id):
            if not self.twin_id or not self.clock_domain:
                raise ValueError("physical UC4 device requires twin_id and clock_domain")
        return self


class EventProvenance(StrictModel):
    source_record_id: str | None
    sequence: int = Field(ge=0)
    clock_domain: str = Field(min_length=1)
    quality: Literal["exact", "estimated", "delayed", "partial", "missing_marker"]


class UC4Event(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0.0"]
    event_id: str = Field(pattern=r"^UC4-EVT-[A-Z0-9-]+$")
    use_case: Literal["UC4"]
    event_time: float = Field(ge=0)
    ingest_time: float = Field(ge=0)
    source_entity: str = Field(pattern=UC4_ID)
    target_entity: str | None = Field(default=None, pattern=UC4_ID)
    event_type: str = Field(min_length=1)
    payload: dict[str, Any]
    correlation_ids: list[str]
    provenance: EventProvenance
    visibility: Literal["ground_truth_only", "observable", "collected", "investigator_visible"]


class TimeRange(StrictModel):
    start: float = Field(ge=0)
    end: float = Field(ge=0)

    @model_validator(mode="after")
    def ordered(self) -> "TimeRange":
        if self.start > self.end:
            raise ValueError("source time range start must not exceed end")
        return self


class Transformation(StrictModel):
    transformation_id: str = Field(min_length=1)
    type: Literal["none", "minimize", "redact", "normalize", "derive"]
    input_evidence_ids: list[str]
    time: float = Field(ge=0)
    actor_id: str = Field(pattern=UC4_ID)


class EvidenceItem(StrictModel):
    schema_version: Literal["1.0.0"]
    evidence_id: str = Field(pattern=r"^UC4-EV-[0-9]{6}$")
    use_case: Literal["UC4"]
    source_entity: str = Field(pattern=UC4_ID)
    source_record_ids: list[str] = Field(min_length=1)
    authorization_id: str = Field(pattern=r"^UC4-AUTH-[0-9]{4}$")
    policy_decision_id: str = Field(pattern=r"^UC4-PD-[0-9]{6}$")
    acquisition_method: Literal["cpe_historical", "cpe_live", "home_assistant_export", "device_state_export", "cloud_export"]
    source_time_range: TimeRange
    acquisition_time: float = Field(ge=0)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonicalization: Literal["RFC8785-JCS"]
    collector_id: Literal["UC4-S02"]
    sensitivity: Literal["Low", "Medium", "High", "Critical"]
    transformations: list[Transformation]
    custody_status: Literal["registered", "verified", "verification_failed", "disposed"]
    storage_reference: str = Field(min_length=1)


class TimeConfig(StrictModel):
    unit: Literal["seconds"]
    horizon: float = Field(gt=0)
    warmup: float = Field(ge=0)
    entry: float = Field(ge=0)
    tamper: float = Field(ge=0)
    case_trigger: float = Field(ge=0)
    request: float = Field(ge=0)


class TopologyConfig(StrictModel):
    enabled_entities: list[str] = Field(min_length=1)
    cloud_enabled: bool = False
    sdn_enabled: bool = False


class DeviceConfig(StrictModel):
    enabled: bool
    processing_delay_seconds: float = Field(ge=0)
    error_probability: float = Field(ge=0, le=1)
    clock_offset_seconds: float
    transition_parameters: dict[str, Any]


class IncidentConfig(StrictModel):
    enabled: bool
    entry_entity: Literal["UC4-D03"]
    tamper_target: Literal["UC4-D03"]
    tamper_strategy: Literal["tampered_then_offline", "direct_offline"]
    light_automation_enabled: bool
    home_assistant_automation_delay_seconds: float = Field(ge=0)
    light_acknowledgement_delay_seconds: float = Field(ge=0)


class AuthorizationConfig(StrictModel):
    decision_path: Literal["allow", "absent", "invalid", "expired", "revoked", "out_of_scope"]
    authorization_id: str = Field(pattern=r"^UC4-AUTH-[0-9]{4}$")
    case_id: str = Field(pattern=r"^UC4-CASE-[0-9]{4}$")
    purpose: str = Field(min_length=1)
    valid_from: float = Field(ge=0)
    valid_to: float = Field(gt=0)
    evidence_window_start: float = Field(ge=0)
    evidence_window_end: float = Field(ge=0)
    allowed_entities: list[str]
    allowed_data_types: list[str]
    allowed_actions: list[Literal["read_historical", "observe_live", "export_metadata", "export_state"]]
    permitted_fields: list[str] = Field(min_length=1)
    verification_result: Literal["valid", "invalid", "unknown"]


class ObservationConfig(StrictModel):
    base_loss_probability: float = Field(ge=0, le=1)
    presence_detection_probability: float = Field(ge=0, le=1)
    presence_false_positive_probability: float = Field(ge=0, le=1)
    presence_evaluation_window_seconds: float = Field(gt=0)
    presence_reporting_delay_seconds: float = Field(ge=0)
    presence_refractory_seconds: float = Field(ge=0)
    clock_offset_bound_seconds: float = Field(ge=0)
    timestamp_jitter_std_seconds: float = Field(ge=0)
    timestamp_jitter_bound_seconds: float = Field(ge=0)


class NetworkConfig(StrictModel):
    service_capacity_bits_per_second: float = Field(gt=0)
    buffer_bytes: int = Field(ge=1)
    base_delay_seconds: float = Field(ge=0)
    jitter_bound_seconds: float = Field(ge=0)
    loss_probability: float = Field(ge=0, le=1)
    logging_enabled: bool
    payload_capture_enabled: Literal[False]
    background_load_fraction: float = Field(default=0.0, ge=0, lt=1)


class CollectionConfig(StrictModel):
    minimization_enabled: Literal[True]
    pseudonymization_enabled: Literal[True]
    acquisition_timeout_seconds: float = Field(gt=0)
    allowed_sources_only: Literal[True]
    deny_empty_projection: Literal[True]
    retention_policy: Literal["bounded_case_retention", "dispose_at_run_end"]
    start_delay_seconds: float = Field(default=0.0, ge=0)


class RetentionConfig(StrictModel):
    home_assistant_max_events: int = Field(ge=1)
    cpe_max_bytes: int = Field(ge=1)
    nominal_seconds: float = Field(ge=0)


class DigitalTwinConfig(StrictModel):
    stale_threshold_seconds: float = Field(ge=0)


class ReconstructionConfig(StrictModel):
    missing_evidence_penalty: float = Field(ge=0, le=1)
    support_weights: dict[str, float]
    source_reliability: dict[str, float]


class OutputConfig(StrictModel):
    directory: str = Field(min_length=1)
    canonicalization: Literal["RFC8785-JCS"]
    include_ground_truth: bool

    @model_validator(mode="after")
    def safe_relative_directory(self) -> "OutputConfig":
        path = PurePath(self.directory)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("output directory must be a repository-relative path without '..'")
        return self


class FaultConfig(StrictModel):
    force_presence_miss: bool = False
    force_door_observation_loss: bool = False
    evidence_tamper_after_collection: bool = False
    custody_tamper_after_append: bool = False
    home_assistant_unavailable: bool = False
    cpe_unavailable: bool = False


class SimulationConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    scenario_id: Literal["UC4-unauthorized-entry-sensor-tampering"]
    deterministic: bool
    random_seed: int = Field(ge=0, le=4294967295)
    time: TimeConfig
    topology: TopologyConfig
    devices: dict[str, DeviceConfig]
    incident: IncidentConfig
    authorization: AuthorizationConfig
    observation: ObservationConfig
    network: NetworkConfig
    collection: CollectionConfig
    retention: RetentionConfig
    digital_twin: DigitalTwinConfig
    reconstruction: ReconstructionConfig
    outputs: OutputConfig
    faults: FaultConfig = Field(default_factory=FaultConfig)

    @model_validator(mode="after")
    def cross_constraints(self) -> "SimulationConfig":
        t = self.time
        if not (0 <= t.warmup < t.entry < t.tamper < t.case_trigger <= t.request < t.horizon):
            raise ValueError("times must satisfy warmup < entry < tamper < case_trigger <= request < horizon")
        a = self.authorization
        if not (a.valid_from < a.valid_to and a.evidence_window_start < a.evidence_window_end):
            raise ValueError("authorization validity and evidence windows must be ordered")
        if self.incident.enabled and not (a.evidence_window_start <= t.entry <= t.tamper <= a.evidence_window_end):
            raise ValueError("enabled incident must fall inside the evidence window")
        if a.decision_path == "allow" and a.verification_result != "valid":
            raise ValueError("allow decision_path requires verification_result=valid")
        if a.decision_path == "absent" and a.verification_result != "unknown":
            raise ValueError("absent decision_path requires verification_result=unknown")
        enabled = set(self.topology.enabled_entities)
        if len(enabled) != len(self.topology.enabled_entities):
            raise ValueError("topology.enabled_entities must be unique")
        for device_id, profile in self.devices.items():
            if not re.fullmatch(r"UC4-D0[1-6]", device_id):
                raise ValueError(f"invalid device profile key: {device_id}")
            if profile.enabled and device_id not in enabled:
                raise ValueError(f"enabled device profile {device_id} is absent from topology")
            if abs(profile.clock_offset_seconds) > self.observation.clock_offset_bound_seconds:
                raise ValueError(f"clock offset for {device_id} exceeds configured bound")
        if not set(a.allowed_entities).issubset(enabled):
            raise ValueError("authorization.allowed_entities must be enabled topology entities")
        if len(a.allowed_entities) != len(set(a.allowed_entities)):
            raise ValueError("authorization.allowed_entities must be unique")
        if len(a.allowed_data_types) != len(set(a.allowed_data_types)):
            raise ValueError("authorization.allowed_data_types must be unique")
        if len(a.allowed_actions) != len(set(a.allowed_actions)):
            raise ValueError("authorization.allowed_actions must be unique")
        if len(a.permitted_fields) != len(set(a.permitted_fields)):
            raise ValueError("authorization.permitted_fields must be unique")
        cloud_present = "UC4-S01" in enabled
        if self.topology.cloud_enabled != cloud_present:
            raise ValueError("cloud_enabled must agree with presence of UC4-S01")
        if self.observation.timestamp_jitter_std_seconds > self.observation.timestamp_jitter_bound_seconds:
            raise ValueError("timestamp jitter standard deviation must not exceed its bound")
        if any(v < 0 for v in self.reconstruction.support_weights.values()):
            raise ValueError("support weights must be non-negative")
        if any(v < 0 or v > 1 for v in self.reconstruction.source_reliability.values()):
            raise ValueError("source reliability values must be within [0,1]")
        return self
