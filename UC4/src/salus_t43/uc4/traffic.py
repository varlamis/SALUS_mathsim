"""Abstract CPE queue with explicit conservation accounting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueUpdate:
    initial_bytes: float
    arriving_bytes: float
    served_bytes: float
    dropped_bytes: float
    final_bytes: float

    def assert_conservation(self, tolerance: float = 1e-9) -> None:
        expected = self.initial_bytes + self.arriving_bytes - self.served_bytes - self.dropped_bytes
        if abs(self.final_bytes - expected) > tolerance:
            raise RuntimeError("CPE queue conservation invariant violated")


class CPEQueue:
    def __init__(self, capacity_bits_per_second: float, buffer_bytes: int, background_load_fraction: float = 0.0) -> None:
        if not 0 <= background_load_fraction < 1:
            raise ValueError("background load fraction must be within [0,1)")
        self.service_bytes_per_second = capacity_bits_per_second / 8.0 * (1.0 - background_load_fraction)
        self.background_load_fraction = background_load_fraction
        self.buffer_bytes = float(buffer_bytes)
        self.occupancy_bytes = 0.0
        self.maximum_occupancy_bytes = 0.0
        self.total_arrivals = 0.0
        self.total_served = 0.0
        self.total_dropped = 0.0
        self.total_service_capacity = 0.0

    def update(self, arriving_bytes: float, elapsed_seconds: float) -> QueueUpdate:
        if arriving_bytes < 0 or elapsed_seconds < 0:
            raise ValueError("queue arrival and elapsed time must be non-negative")
        initial = self.occupancy_bytes
        available = initial + arriving_bytes
        service_capacity = self.service_bytes_per_second * elapsed_seconds
        served = min(available, service_capacity)
        after_service = available - served
        dropped = max(0.0, after_service - self.buffer_bytes)
        final = after_service - dropped
        self.occupancy_bytes = final
        self.maximum_occupancy_bytes = max(self.maximum_occupancy_bytes, final)
        self.total_arrivals += arriving_bytes
        self.total_served += served
        self.total_dropped += dropped
        self.total_service_capacity += service_capacity
        update = QueueUpdate(initial, arriving_bytes, served, dropped, final)
        update.assert_conservation()
        return update
