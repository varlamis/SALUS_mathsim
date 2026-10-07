"""Runtime physical-device and digital-twin state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PhysicalDevice:
    entity_id: str
    state: str
    allowed_states: frozenset[str]
    online: bool = True
    version: int = 0
    last_event_time: float = 0.0

    def transition(self, next_state: str, event_time: float) -> bool:
        if next_state not in self.allowed_states:
            raise ValueError(f"{self.entity_id}: state {next_state!r} is not declared")
        if next_state == self.state:
            return False
        self.state = next_state
        self.online = next_state != "offline"
        self.version += 1
        self.last_event_time = event_time
        return True


@dataclass(slots=True)
class DigitalTwin:
    entity_id: str
    physical_entity_id: str
    accepted_version: int = -1
    state: str | None = None
    update_time: float | None = None
    source_event_time: float | None = None
    rejected_updates: int = 0

    def synchronize(self, version: int, state: str, event_time: float, ingest_time: float) -> bool:
        if version <= self.accepted_version:
            self.rejected_updates += 1
            return False
        self.accepted_version = version
        self.state = state
        self.source_event_time = event_time
        self.update_time = ingest_time
        return True

    @property
    def lag(self) -> float | None:
        if self.update_time is None or self.source_event_time is None:
            return None
        return max(0.0, self.update_time - self.source_event_time)


@dataclass(slots=True)
class HomeAssistantState:
    online: bool = True
    accepted_versions: dict[str, int] = field(default_factory=dict)
    last_known_states: dict[str, str] = field(default_factory=dict)
    records: list[dict[str, Any]] = field(default_factory=list)

    def ingest(self, entity_id: str, version: int, state: str, record: dict[str, Any], maximum: int) -> bool:
        if not self.online or version <= self.accepted_versions.get(entity_id, -1):
            return False
        self.accepted_versions[entity_id] = version
        self.last_known_states[entity_id] = state
        self.records.append(record)
        if len(self.records) > maximum:
            del self.records[: len(self.records) - maximum]
        return True
