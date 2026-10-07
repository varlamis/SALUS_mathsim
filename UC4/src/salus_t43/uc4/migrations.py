"""Explicit, deterministic migration boundary for versioned UC4 configurations."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .models import SCHEMA_VERSION, SimulationConfig


@dataclass(frozen=True, slots=True)
class MigrationReport:
    source_version: str
    target_version: str
    applied_steps: tuple[str, ...]


def migrate_simulation_config(document: dict[str, Any]) -> tuple[dict[str, Any], MigrationReport]:
    """Migrate a configuration to the current schema without mutating its input."""

    migrated = deepcopy(document)
    source = str(migrated.get("schema_version", "missing"))
    if source == SCHEMA_VERSION:
        SimulationConfig.model_validate(migrated)
        return migrated, MigrationReport(source, SCHEMA_VERSION, ())
    if source != "0.9.0":
        raise ValueError(f"unsupported UC4 configuration schema_version: {source}")

    migrated.setdefault("network", {}).setdefault("background_load_fraction", 0.0)
    migrated.setdefault("collection", {}).setdefault("start_delay_seconds", 0.0)
    migrated["schema_version"] = SCHEMA_VERSION
    SimulationConfig.model_validate(migrated)
    return migrated, MigrationReport(
        source, SCHEMA_VERSION,
        ("add_network_background_load_fraction", "add_collection_start_delay_seconds"),
    )
