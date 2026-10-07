# UC3 entity lifecycles

- Sensor: healthy → noisy/biased/stuck/unavailable → restored.
- PLC: initializing → operational → degraded/safe/unavailable → recovered.
- Gateway: available → rate-limited/isolated/unavailable → rolled back.
- Alert: created → reviewed/correlated → closed or escalated.
- Mitigation: requested → acknowledged → applied/effective or failed/rejected → expired/rolled back.
- Evidence: identified → minimized → hashed → collected → verified/quarantined → retained/disposed.
- Twin: synchronized → stale/unknown → resynchronized.

Transitions are symbolic and must not actuate external systems.
