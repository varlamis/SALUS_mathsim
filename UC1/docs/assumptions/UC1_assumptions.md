# UC1 assumption and calibration register

All assumptions below are accepted synthetic fallbacks for implementation. They must be replaced, not silently edited, when partner evidence becomes available.

| ID | Assumption/fallback | Status | Impact and replacement |
|---|---|---|---|
| `ASSUMPTION-UC1-001` | Nominal attack is a symbolic forged/replayed control-affecting request. | Agreed synthetic fallback | Replace attack class and preconditions after NRW scenario confirmation. |
| `ASSUMPTION-UC1-002` | One abstract controlled road/lab environment is sufficient. | Synthetic fallback | Split into lab, road, and municipal environments if topology is supplied. |
| `ASSUMPTION-UC1-003` | Vehicle gateway and in-vehicle zone are logical boundaries. | Open | Replace with confirmed gateway/bus topology; never infer ECUs. |
| `ASSUMPTION-UC1-004` | Car2X is one abstract bounded message channel. | Synthetic fallback | Select an ITS-G5/C-V2X profile only with confirmed interface data. |
| `ASSUMPTION-UC1-005` | One roadside/control backhaul and optional management service exist logically. | Open | Replace with pilot topology and ownership. |
| `ASSUMPTION-UC1-006` | SALUS services share one logical protected zone. | Synthetic fallback | Map to deployment zones from T4.2/T4.4. |
| `ASSUMPTION-UC1-007` | Vehicle motion is not needed for the first message-security slice. | Synthetic fallback | Add bounded kinematics only if needed for plausibility. |
| `ASSUMPTION-UC1-008` | OBU exposes abstract message and health events. | Open | Replace with confirmed telemetry and API. |
| `ASSUMPTION-UC1-009` | An in-vehicle controller is only a bounded downstream cyber target. | Synthetic fallback | Calibrate separately from DS1; never infer actuation. |
| `ASSUMPTION-UC1-010` | RSU combines receive and abstract validation handoff. | Open | Split roles when hardware/software architecture is known. |
| `ASSUMPTION-UC1-011` | Controller has three safe abstract phases and a 3 s minimum. | Synthetic fallback | Replace from approved test controller model; safety gate remains mandatory. |
| `ASSUMPTION-UC1-012` | Metadata observation probability is configurable; payload capture is disabled. | Synthetic fallback | Replace with monitoring coverage measurements. |
| `ASSUMPTION-UC1-013` | Trust checking returns available/credential/sender/freshness predicates. | Synthetic fallback | Bind to confirmed PKI semantics without storing secrets. |
| `ASSUMPTION-UC1-014` | Weighted deterministic rules stand in for T3.3 detection. | Synthetic fallback | Replace through the versioned AI contract and retain explanations. |
| `ASSUMPTION-UC1-015` | Policy supports drop, rate-limit, isolate, or alert-only actions. | Synthetic fallback | Capability discovery must remove unsupported actions. |
| `ASSUMPTION-UC1-016` | Four stateful entities have one-to-one observable twins. | Synthetic fallback | Align object and synchronization semantics with T4.4. |
| `ASSUMPTION-UC1-017` | Evidence is allowlisted, minimized, hashed, and custody chained. | Synthetic fallback | Replace authorization, retention, and storage with approved contracts. |
| `ASSUMPTION-UC1-018` | Reconstruction correlates trust, alert, policy, and controller records. | Synthetic fallback | Add calibrated reliability and causal rules when data exists. |
| `ASSUMPTION-UC1-019` | Vehicle operator is pseudonymous and not behaviourally modelled. | Synthetic fallback | Add only required, lawful pilot role attributes. |
| `ASSUMPTION-UC1-020` | A generic traffic-infrastructure operator owns the RSU/controller roles. | Open | Replace with confirmed organisation and responsibilities. |

Default rates, delays, probabilities, weights, and retention are stored in YAML with units. Their Monte Carlo ranges are declared before results are viewed.

