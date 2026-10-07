# UC5 assumptions register

| ID | Assumption used for executable slice | Status / required owner |
|---|---|---|
| UC5-A01 | All entities, identifiers and events are synthetic. | Fixed safety boundary |
| UC5-A02 | Exactly one patient monitor is active; other medical-device classes remain inventory-only. | Confirm with HMU |
| UC5-A03 | Time is integer seconds in UTC and all byte/rate units are explicit. | Confirm integration owners |
| UC5-A04 | Seeded configurable distributions approximate normal rate and bytes. | Replace with licensed DS8 mapping |
| UC5-A05 | `anomalous_egress` is symbolic and contains no exploit, malware or payload. | Fixed safety boundary |
| UC5-A06 | A new external destination plus rate/byte deviation is sufficient for the demonstrator alert. | Calibrate with 5YPE/HMU |
| UC5-A07 | Device-health mismatch is observable metadata, not a clinical measurement. | Confirm clinical-safety owner |
| UC5-A08 | The active monitor is essential unless configuration states otherwise. | Confirm clinical-safety owner |
| UC5-A09 | Isolation requires authorization, enforcement availability and nonessential status or approved backup. | Confirm hospital authority |
| UC5-A10 | Rejected isolation falls back to continued monitoring/review without interrupting service. | Confirm SOC and clinical teams |
| UC5-A11 | Evidence purpose is incident investigation; capture is minimized to synthetic event identifiers, hashes and abstract features. | Confirm controller/legal owner |
| UC5-A12 | Sharing requires evidence integrity, redaction and explicit authorization and contains no patient/clinical fields. | Confirm sharing authority |
| UC5-A13 | Reconstruction may use collected evidence but never hidden attack truth. | Fixed evaluation boundary |
| UC5-A14 | Proposal KPI attainment cannot be inferred from synthetic runs; WP6 baselines and protocol are required. | Open with WP6 |

Assumptions are configuration-visible where executable. A future change to patient-data scope, clinical actuation, or a live endpoint requires a separate safety, ethics, privacy and authorization review and is outside this package.
