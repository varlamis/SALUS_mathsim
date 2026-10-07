from salus_mathsim.uc4.dynamics import ObservationModel
from salus_mathsim.uc4.entities import DigitalTwin, PhysicalDevice
from salus_mathsim.uc4.models import SimulationConfig
from salus_mathsim.uc4.traffic import CPEQueue

import pytest
import yaml


def _config(repo_root):
    raw = yaml.safe_load((repo_root / "configs" / "uc4" / "incident_lawful_access.yaml").read_text(encoding="utf-8"))
    return SimulationConfig.model_validate(raw)


def test_device_transition_and_twin_monotonicity():
    device = PhysicalDevice("UC4-D03", "closed_online", frozenset({"closed_online", "open_online", "tampered", "offline"}))
    assert device.transition("open_online", 10.0)
    assert device.version == 1
    assert not device.transition("open_online", 10.1)
    assert device.version == 1
    with pytest.raises(ValueError):
        device.transition("invented", 11.0)

    twin = DigitalTwin("UC4-DT03", "UC4-D03")
    assert twin.synchronize(1, "open_online", 10.0, 10.2)
    assert not twin.synchronize(1, "closed_online", 9.0, 10.3)
    assert twin.state == "open_online"


def test_seeded_observation_streams_repeat(repo_root):
    config = _config(repo_root)
    left = ObservationModel(config.random_seed, config.observation, config.network)
    right = ObservationModel(config.random_seed, config.observation, config.network)
    profile = config.devices["UC4-D03"]
    assert [left.delivered("UC4-D03", profile) for _ in range(10)] == [right.delivered("UC4-D03", profile) for _ in range(10)]
    times_left = [left.local_time("UC4-D03", 600.0, profile) for _ in range(5)]
    times_right = [right.local_time("UC4-D03", 600.0, profile) for _ in range(5)]
    assert times_left == times_right
    assert all(abs(value - 600.0 - profile.clock_offset_seconds) <= config.observation.timestamp_jitter_bound_seconds for value in times_left)


def test_cpe_queue_conservation_and_overflow():
    queue = CPEQueue(capacity_bits_per_second=80.0, buffer_bytes=20)
    update = queue.update(arriving_bytes=50, elapsed_seconds=1.0)
    update.assert_conservation()
    assert update.served_bytes == 10
    assert update.dropped_bytes == 20
    assert update.final_bytes == 20
    assert 0 <= queue.occupancy_bytes <= queue.buffer_bytes
