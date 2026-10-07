"""Stable priority queue for UC4 discrete-event execution."""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
from typing import Any


@dataclass(order=True, frozen=True, slots=True)
class ScheduledEvent:
    simulation_time: float
    sequence: int
    kind: str = field(compare=False)
    source: str = field(compare=False)
    target: str | None = field(default=None, compare=False)
    payload: dict[str, Any] = field(default_factory=dict, compare=False)
    correlation_ids: tuple[str, ...] = field(default_factory=tuple, compare=False)


class EventQueue:
    def __init__(self) -> None:
        self._heap: list[ScheduledEvent] = []
        self._next_sequence = 0
        self._last_key: tuple[float, int] | None = None

    def schedule(
        self,
        simulation_time: float,
        kind: str,
        source: str,
        target: str | None = None,
        payload: dict[str, Any] | None = None,
        correlation_ids: tuple[str, ...] = (),
    ) -> ScheduledEvent:
        if simulation_time < 0:
            raise ValueError("simulation time must be non-negative")
        event = ScheduledEvent(
            float(simulation_time), self._next_sequence, kind, source, target,
            dict(payload or {}), tuple(correlation_ids),
        )
        self._next_sequence += 1
        heapq.heappush(self._heap, event)
        return event

    def pop(self) -> ScheduledEvent:
        event = heapq.heappop(self._heap)
        key = (event.simulation_time, event.sequence)
        if self._last_key is not None and key < self._last_key:
            raise RuntimeError("event queue monotonicity invariant violated")
        self._last_key = key
        return event

    def __bool__(self) -> bool:
        return bool(self._heap)

    def __len__(self) -> int:
        return len(self._heap)
