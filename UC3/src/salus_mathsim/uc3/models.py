from __future__ import annotations

from pathlib import PurePath
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProcessConfig(StrictModel):
    area_m2: float = Field(gt=0)
    initial_level_m: float = Field(ge=0)
    minimum_level_m: float = Field(ge=0)
    maximum_level_m: float = Field(gt=0)
    target_level_m: float = Field(ge=0)
    pump_flow_m3_s: float = Field(ge=0)
    outlet_flow_m3_s: float = Field(ge=0)
    sensor_noise_std_m: float = Field(ge=0)
    sensor_bias_m: float
    scan_period_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def bounds(self) -> "ProcessConfig":
        if not self.minimum_level_m < self.target_level_m < self.maximum_level_m:
            raise ValueError("minimum_level_m < target_level_m < maximum_level_m is required")
        if not self.minimum_level_m <= self.initial_level_m <= self.maximum_level_m:
            raise ValueError("initial level must be inside process bounds")
        return self


class AttackConfig(StrictModel):
    enabled: bool
    kind: Literal["smart_fuzzing", "unauthorized_write", "application_flood", "sensor_fault", "unsupported_function", "malformed_request", "supply_chain_predeployment"]
    start_seconds: float = Field(ge=0)
    count: int = Field(ge=1)
    interval_seconds: float = Field(gt=0)
    request_rate_per_second: float = Field(gt=0)
    authorized: bool
    malformed_ratio: float = Field(ge=0, le=1)


class ChannelConfig(StrictModel):
    capacity_messages_per_second: float = Field(gt=0)
    buffer_messages: int = Field(ge=1)
    base_delay_seconds: float = Field(ge=0)
    jitter_seconds: float = Field(ge=0)
    loss_probability: float = Field(ge=0, le=1)
    observation_probability: float = Field(ge=0, le=1)


class DetectionConfig(StrictModel):
    enabled: bool
    threshold: float = Field(ge=0, le=1)
    weights: dict[str, float]

    @model_validator(mode="after")
    def weights_valid(self) -> "DetectionConfig":
        required = {"authorization", "protocol", "rate", "command_residual", "process_residual"}
        if set(self.weights) != required or abs(sum(self.weights.values()) - 1.0) > 1e-9:
            raise ValueError("detector weights must use the five required keys and sum to 1")
        if any(value < 0 or value > 1 for value in self.weights.values()):
            raise ValueError("detector weights must be in [0,1]")
        return self


class PolicyConfig(StrictModel):
    supported_actions: list[Literal["drop", "rate_limit", "isolate_source", "alert_only"]]
    selected_action: Literal["drop", "rate_limit", "isolate_source", "alert_only"]
    enforcement_available: bool
    safety_telemetry_required: bool
    enforcement_delay_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def supported(self) -> "PolicyConfig":
        if self.selected_action not in self.supported_actions:
            raise ValueError("selected action is not supported")
        return self


class EvidenceConfig(StrictModel):
    enabled: bool
    allowed_types: list[str]
    allowed_fields: list[str]
    retention_seconds: float = Field(ge=0)


class OutputConfig(StrictModel):
    directory: str

    @model_validator(mode="after")
    def safe(self) -> "OutputConfig":
        path = PurePath(self.directory)
        if path.is_absolute() or ".." in path.parts or path.parts[:3] != ("reports", "generated", "uc3"):
            raise ValueError("output directory must remain under reports/generated/uc3")
        return self


class SimulationConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    scenario_id: str
    description: str
    seed: int = Field(ge=0)
    duration_seconds: float = Field(gt=0)
    process: ProcessConfig
    attack: AttackConfig
    channel: ChannelConfig
    detection: DetectionConfig
    policy: PolicyConfig
    evidence: EvidenceConfig
    clocks: dict[str, float]
    outputs: OutputConfig

    @model_validator(mode="after")
    def cross_fields(self) -> "SimulationConfig":
        if not self.scenario_id.startswith("UC3-"):
            raise ValueError("scenario_id must start with UC3-")
        end = self.attack.start_seconds + (self.attack.count - 1) * self.attack.interval_seconds
        if end > self.duration_seconds:
            raise ValueError("attack schedule exceeds duration")
        if set(self.clocks) != {"sensor", "plc", "monitor"}:
            raise ValueError("clocks must define sensor, plc, and monitor")
        return self
