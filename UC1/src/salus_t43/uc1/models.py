from __future__ import annotations

from pathlib import PurePath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AttackConfig(StrictModel):
    enabled: bool
    kind: Literal["forged_request", "replay", "flood", "malformed", "sequence_anomaly"]
    start_seconds: float = Field(ge=0)
    count: int = Field(ge=1)
    interval_seconds: float = Field(gt=0)
    credential_state: Literal["valid", "untrusted", "expired", "revoked"]
    replay_age_seconds: float = Field(ge=0)


class ChannelConfig(StrictModel):
    capacity_messages_per_second: float = Field(gt=0)
    buffer_messages: int = Field(ge=1)
    base_delay_seconds: float = Field(ge=0)
    jitter_seconds: float = Field(ge=0)
    loss_probability: float = Field(ge=0, le=1)
    observation_probability: float = Field(ge=0, le=1)


class TrustConfig(StrictModel):
    service_available: bool
    freshness_window_seconds: float = Field(ge=0)
    valid_sender: str


class DetectionConfig(StrictModel):
    threshold: float = Field(ge=0, le=1)
    weights: dict[str, float]

    @model_validator(mode="after")
    def validate_weights(self) -> "DetectionConfig":
        required = {"auth", "freshness", "sequence", "rate", "plausibility"}
        if set(self.weights) != required:
            raise ValueError(f"weights must be exactly {sorted(required)}")
        if any(value < 0 or value > 1 for value in self.weights.values()):
            raise ValueError("detection weights must be in [0,1]")
        if abs(sum(self.weights.values()) - 1.0) > 1e-9:
            raise ValueError("detection weights must sum to 1")
        return self


class PolicyConfig(StrictModel):
    supported_actions: list[Literal["drop", "rate_limit", "isolate", "alert_only"]]
    selected_action: Literal["drop", "rate_limit", "isolate", "alert_only"]
    enforcement_available: bool
    enforcement_delay_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def action_supported(self) -> "PolicyConfig":
        if self.selected_action not in self.supported_actions:
            raise ValueError("selected_action must be listed in supported_actions")
        return self


class ControllerConfig(StrictModel):
    initial_phase: Literal["safe_all_red", "north_south", "east_west"]
    minimum_phase_seconds: float = Field(gt=0)
    allow_control_requests: bool


class EvidenceConfig(StrictModel):
    enabled: bool
    allowed_types: list[str]
    allowed_fields: list[str]
    retention_seconds: float = Field(ge=0)


class OutputConfig(StrictModel):
    directory: str

    @model_validator(mode="after")
    def safe_directory(self) -> "OutputConfig":
        path = PurePath(self.directory)
        if path.is_absolute() or ".." in path.parts or path.parts[:3] != ("reports", "generated", "uc1"):
            raise ValueError("output directory must remain under reports/generated/uc1")
        return self


class SimulationConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    scenario_id: str
    description: str
    seed: int = Field(ge=0)
    duration_seconds: float = Field(gt=0)
    attack: AttackConfig
    channel: ChannelConfig
    trust: TrustConfig
    detection: DetectionConfig
    policy: PolicyConfig
    controller: ControllerConfig
    evidence: EvidenceConfig
    clocks: dict[str, float]
    outputs: OutputConfig

    @model_validator(mode="after")
    def cross_fields(self) -> "SimulationConfig":
        if not self.scenario_id.startswith("UC1-"):
            raise ValueError("scenario_id must start with UC1-")
        final_attack = self.attack.start_seconds + (self.attack.count - 1) * self.attack.interval_seconds
        if final_attack > self.duration_seconds:
            raise ValueError("attack schedule exceeds duration_seconds")
        return self

