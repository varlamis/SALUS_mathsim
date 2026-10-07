# UC4 Stage 10 Monte Carlo analysis

This report contains synthetic, uncalibrated model results. It is not pilot performance, legal validation, or evidence of real-device fidelity.

## Reproducibility and inference

- Samples: **100** independently parameterized, deterministically seeded runs.
- Master seed: **20260908**; every simulation seed is retained in `monte_carlo_summary.json` and every row in `monte_carlo_samples.jsonl`.
- Continuous outcomes: two-sided 95% normal-approximation interval for the mean using the sample standard deviation.
- Binary outcomes: two-sided 95% Wilson score interval.
- Undefined outcomes are never coerced to zero; the table records both usable and undefined counts.
- Sensitivity is Pearson correlation and is descriptive, not causal.

## Deterministic nominal reference

Seed: **43004**  
Canonical result SHA-256: `497b2a1c226c72798a22f977354fd5614b28ea2430c2eae1032165cd312fac81`

| Outcome | Nominal value |
|---|---:|
| `capture_recall` | 1.0000 |
| `evidence_precision` | 1.0000 |
| `evidence_items` | 17 |
| `unauthorized_disclosure_bytes` | 0 |
| `collection_latency_p95_seconds` | 0.0160 |
| `investigation_latency_seconds` | 20.0170 |
| `reconstruction_recall` | 1.0000 |
| `reconstruction_precision` | 0.5000 |
| `timestamp_mae_seconds` | 0.0424 |
| `custody_failures` | 0 |
| `twin_mean_lag_seconds` | 0.4883 |
| `twin_stale_state_fraction` | 0.7462 |
| `queue_loss_rate` | 0.0000 |
| `maximum_queue_occupancy_bytes` | 0.0000 |
| `acquisition_utilization` | 0.1901 |
| `acquisition_queue_occupancy_bytes` | 4040 |
| `acquisition_loss_rate` | 0.0000 |
| `strong_claim_count` | 3 |

## Outcome intervals

| Outcome | n | Undefined | Mean | 95% CI |
|---|---:|---:|---:|---:|
| `capture_recall` | 99 | 1 | 0.8990 | [0.8393, 0.9587] |
| `evidence_precision` | 89 | 11 | 1.0000 | [1.0000, 1.0000] |
| `evidence_items` | 100 | 0 | 10.7800 | [9.7016, 11.8584] |
| `unauthorized_disclosure_bytes` | 100 | 0 | 0.0000 | [0.0000, 0.0000] |
| `collection_latency_p95_seconds` | 89 | 11 | 270.1117 | [234.0530, 306.1704] |
| `investigation_latency_seconds` | 100 | 0 | 327.6993 | [289.3063, 366.0924] |
| `reconstruction_recall` | 100 | 0 | 0.6647 | [0.6048, 0.7246] |
| `reconstruction_precision` | 89 | 11 | 0.5000 | [0.5000, 0.5000] |
| `timestamp_mae_seconds` | 89 | 11 | 0.0390 | [0.0351, 0.0429] |
| `custody_failures` | 100 | 0 | 0.0000 | [0.0000, 0.0000] |
| `twin_mean_lag_seconds` | 100 | 0 | 4.8723 | [4.2352, 5.5093] |
| `twin_stale_state_fraction` | 100 | 0 | 0.6143 | [0.5886, 0.6399] |
| `queue_loss_rate` | 100 | 0 | 0.0000 | [0.0000, 0.0000] |
| `maximum_queue_occupancy_bytes` | 100 | 0 | 0.0000 | [0.0000, 0.0000] |
| `acquisition_utilization` | 100 | 0 | 0.4009 | [0.3402, 0.4615] |
| `acquisition_queue_occupancy_bytes` | 100 | 0 | 2566.6100 | [2310.3979, 2822.8221] |
| `acquisition_loss_rate` | 89 | 11 | 0.0000 | [0.0000, 0.0000] |
| `strong_claim_count` | 100 | 0 | 2.0300 | [1.8282, 2.2318] |

## Largest absolute input/output correlations

| Uncertain input | Outcome | Pearson r | Paired n |
|---|---|---:|---:|
| `collection_start_delay_seconds` | `collection_latency_p95_seconds` | 1.0000 | 89 |
| `collection_start_delay_seconds` | `investigation_latency_seconds` | 1.0000 | 100 |
| `clock_offset_bound_seconds` | `twin_mean_lag_seconds` | 0.8831 | 100 |
| `network_background_load_fraction` | `acquisition_utilization` | 0.7318 | 100 |
| `collection_start_delay_seconds` | `capture_recall` | -0.5369 | 99 |
| `collection_start_delay_seconds` | `reconstruction_recall` | -0.3645 | 100 |
| `collection_start_delay_seconds` | `acquisition_queue_occupancy_bytes` | -0.3321 | 100 |
| `collection_start_delay_seconds` | `strong_claim_count` | -0.3319 | 100 |
| `collection_start_delay_seconds` | `evidence_items` | -0.3316 | 100 |
| `observation_loss_probability` | `twin_stale_state_fraction` | -0.3283 | 100 |
| `collection_start_delay_seconds` | `acquisition_utilization` | -0.2619 | 100 |
| `network_background_load_fraction` | `twin_stale_state_fraction` | -0.2338 | 100 |
| `clock_offset_bound_seconds` | `timestamp_mae_seconds` | -0.1950 | 89 |
| `observation_loss_probability` | `collection_latency_p95_seconds` | -0.1838 | 89 |
| `network_background_load_fraction` | `timestamp_mae_seconds` | -0.1812 | 89 |

## Technical boundary

Zero unauthorized disclosure in these tested paths means that no denied synthetic policy decision released bytes. It does not prove statutory compliance. Custody results verify the implemented hash-chain abstraction, not legal admissibility. Values must be recalibrated against lab or pilot measurements before operational claims are made.

## Relationship to proposal targets

The zero-disclosure, complete modeled-custody, deterministic replay, and bounded reconstruction results are technical evidence relevant to the proposal's privacy-preserving investigation, trustworthy evidence handling, Digital Twin, and reproducibility aims. They are not direct measurements of proposal KPIs and do not demonstrate performance on pilot infrastructure.
