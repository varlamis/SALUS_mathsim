"""Seeded clock, observation, and device-transition dynamics."""

from __future__ import annotations

import hashlib
import random

from .models import DeviceConfig, NetworkConfig, ObservationConfig


class RandomStreams:
    """Independent deterministic streams avoid coupling outcomes to iteration order."""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self._streams: dict[str, random.Random] = {}

    def stream(self, name: str) -> random.Random:
        if name not in self._streams:
            material = f"{self.seed}:{name}".encode("utf-8")
            stream_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
            self._streams[name] = random.Random(stream_seed)
        return self._streams[name]


class ObservationModel:
    def __init__(self, seed: int, observation: ObservationConfig, network: NetworkConfig) -> None:
        self.config = observation
        self.network = network
        self.random = RandomStreams(seed)

    def detected(self, source: str, probability: float) -> bool:
        return self.random.stream(f"detection:{source}").random() < probability

    def delivered(self, source: str, device: DeviceConfig) -> bool:
        p = 1.0 - (
            (1.0 - self.config.base_loss_probability)
            * (1.0 - self.network.loss_probability)
            * (1.0 - device.error_probability)
        )
        return self.random.stream(f"loss:{source}").random() >= p

    def local_time(self, source: str, simulation_time: float, device: DeviceConfig) -> float:
        jitter = self.random.stream(f"clock:{source}").gauss(0.0, self.config.timestamp_jitter_std_seconds)
        bound = self.config.timestamp_jitter_bound_seconds
        jitter = min(bound, max(-bound, jitter))
        return max(0.0, simulation_time + device.clock_offset_seconds + jitter)

    def network_delay(self, source: str) -> float:
        jitter = self.random.stream(f"network:{source}").uniform(-self.network.jitter_bound_seconds, self.network.jitter_bound_seconds)
        return max(0.0, self.network.base_delay_seconds + jitter)
