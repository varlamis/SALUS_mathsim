# UC3 process specifications

| Process | Trigger | Responsible entities | Inputs | Outputs/failure paths |
|---|---|---|---|---|
| Normal control | scan tick | sensor, PLC, actuators | level observation | bounded command; stale/invalid input uses safe logic |
| Smart fuzzing | configured attack time | synthetic adversary, gateway, PLC | symbolic request metadata | validation decision; overflow/loss accounted |
| Detection/XAI | observed event | monitor, detection service | protocol/process features | scored alert plus contributions/missingness |
| Mitigation | explained alert | policy, gateway, analyst | alert/capabilities/safety | requested/applied/effective action or explicit failure |
| Evidence | scoped event | evidence service | allowlisted observable metadata | hash, custody record, or collection failure |
| Reconstruction | evidence ready | reconstruction service, investigator | verified evidence | qualified claim with alternatives/uncertainty |

Every step emits an auditable event and preserves distinct source, receive, detect, decide, apply, and collect times.
