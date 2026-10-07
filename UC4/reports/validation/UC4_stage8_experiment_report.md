# UC4 Stage 8 experiment and negative-path report

## Result

The complete Stage 8 matrix executed successfully on the synthetic UC4 model. All 16 experiment-specific assertions passed, and unauthorized disclosure was zero in every branch. Machine-readable results, including canonical run hashes, are stored in `reports/validation/UC4_stage8_experiment_report.json`.

| Experiment | Evidence | Verified | Denies | Integrity | Disclosure bytes | Main observable effect |
|---|---:|---:|---:|---|---:|---|
| `baseline` | 0 | 0 | 0 | pass | 0 | Normal heartbeats only; no incident or acquisition. |
| `nominal_lawful_incident` | 17 | 17 | 16 | pass | 0 | Entry, automation, and tamper claims are strongly supported. |
| `authorization_absent` | 0 | 0 | 1 | pass | 0 | Request denied before source acquisition. |
| `authorization_invalid` | 0 | 0 | 1 | pass | 0 | Verification failure releases no records. |
| `authorization_expired` | 0 | 0 | 1 | pass | 0 | Expired validity interval releases no records. |
| `authorization_revoked` | 0 | 0 | 1 | pass | 0 | Revoked authorization releases no records. |
| `out_of_scope_device` | 0 | 0 | 1 | pass | 0 | Out-of-scope target causes fail-closed denial. |
| `presence_event_missed` | 14 | 14 | 16 | pass | 0 | True movement remains hidden; no presence observation is invented. |
| `door_event_lost` | 9 | 9 | 16 | pass | 0 | Door truth remains hidden; automation becomes unsupported. |
| `source_records_evicted` | 0 | 0 | 1 | pass | 0 | Sixteen retained records expire before acquisition. |
| `cpe_queue_overflow` | 11 | 11 | 10 | pass | 0 | Queue loss rate is 0.868747; non-CPE evidence remains available. |
| `maximum_clock_skew` | 17 | 17 | 16 | pass | 0 | Maximum uncertainty width expands from 4.43 s to 60.43 s. |
| `evidence_content_tampered` | 17 | 16 | 16 | fault detected | 0 | One hash-mismatched item is quarantined. |
| `custody_link_tampered` | 17 | 0 | 16 | fault detected | 0 | The broken chain quarantines all 17 items. |
| `home_assistant_unavailable` | 8 | 8 | 12 | pass | 0 | No automation trace; entry/tamper retain partial support. |
| `cpe_unavailable` | 11 | 11 | 10 | pass | 0 | Device and Home Assistant evidence remains without CPE flows. |

The nominal run has 16 deny decisions in addition to 17 minimized releases because retained warm-up records are outside the authorized evidence-time window. These are expected per-record denials and demonstrate that a valid authorization does not widen collection beyond its window.

## Analytical findings

### Authorization isolation

Absent, invalid, expired, revoked, and out-of-scope authorization paths all terminate with one deny outcome, zero evidence objects, and zero released bytes. The identical incident ground truth across these branches confirms that acquisition is controlled by authorization state rather than by whether an incident or case exists.

### Observation and automation causality

Forcing the presence miss removes `presence.motion` while preserving `presence.true_movement` only in hidden truth. Losing `door.open` before Home Assistant ingestion also prevents `automation.triggered` and `light.on`; consequently, the automation claim becomes unsupported. This demonstrates that the implementation does not reconstruct or trigger downstream behavior from inaccessible ground truth.

### Retention, congestion, and availability

Reducing retention to 100 seconds removes all incident-window source records before the request and yields an explicit `source_window_empty` denial. Severe CPE congestion drops approximately 86.9% of arriving bytes at the abstract queue while leaving independently retained device/Home Assistant evidence available. CPE unavailability removes the network evidence path without crashing the acquisition pipeline. Home Assistant unavailability suppresses its event and automation paths while preserving direct device and CPE observations.

### Time uncertainty

Clock normalization subtracts configured source offsets before ordering. The maximum-skew profile increases the declared offset uncertainty bound to 30 seconds, expanding evidence intervals to 60.43 seconds and making all adjacent ordering comparisons ambiguous. The model therefore preserves a partial/uncertain order rather than using local timestamps as a false total order.

### Integrity containment

Post-collection content modification is detected by hash recomputation and quarantines the affected item while allowing the remaining 16 verified items to support qualified claims. Modifying the first custody action invalidates the complete downstream chain, leaves zero verified items, and makes all reconstruction claims unsupported. Neither corruption path is mistaken for absence or silently repaired.

## Reproduction

```powershell
python -m pip install -e ".[test]"
salus-mathsim experiment --matrix configs/uc4/experiments.yaml --output reports/generated/uc4/experiments
python -m pytest -q
```

At Stage 8 completion, each experiment directory contained the 14-file core package defined in `docs/use_cases/UC4.md`. Stage 9 adds `competency_queries.json` and `graph_overview.svg` when those packages are regenerated. The two comparison files are written alongside the experiment directories. Individual run generation times are excluded from canonical result hashes.

## Interpretation boundary

These results validate internal behavior under explicit synthetic assumptions. They do not establish legal admissibility, GDPR compliance, real-device fidelity, production integration readiness, or pilot KPI attainment. No partner validation is required for this implementation gate; later real-system calibration must replace documented synthetic defaults without changing the tested privacy and integrity invariants.
