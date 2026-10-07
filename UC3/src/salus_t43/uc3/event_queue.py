from dataclasses import dataclass, field
import heapq
from typing import Any


@dataclass(order=True)
class ScheduledEvent:
    time: float
    sequence: int
    kind: str = field(compare=False)
    payload: dict[str, Any] = field(compare=False)


class EventQueue:
    def __init__(self) -> None:
        self._heap: list[ScheduledEvent] = []
        self._sequence = 0

    def push(self, time: float, kind: str, payload: dict[str, Any]) -> None:
        if time < 0:
            raise ValueError("event time cannot be negative")
        self._sequence += 1
        heapq.heappush(self._heap, ScheduledEvent(time, self._sequence, kind, payload))

    def pop(self) -> ScheduledEvent:
        return heapq.heappop(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)
