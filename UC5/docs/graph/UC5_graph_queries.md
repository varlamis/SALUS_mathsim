# UC5 graph competency queries

The generated graph combines validated static entities/relations with runtime observations, alerts, safety decisions, evidence and claims. Queries are deterministic and derive from graph content.

| Query | Expected answer |
|---|---|
| Which device and zone produced the anomalous flow? | Active monitor and medical-device zone through deployment/communication edges. |
| What baseline was expected? | Registered device profile and configuration-linked flow model. |
| Why did the alert fire? | Alert-to-observation lineage and exported feature contributions. |
| Is the twin stale? | Latest observation time versus configured staleness threshold. |
| What care dependency constrained response? | `supports_care` and `depends_on` paths to essential monitoring. |
| Why was isolation rejected/applied? | Safety decision gates: essentiality, backup, authorization and enforcement. |
| What was requested versus applied? | Policy and mitigation nodes linked to the alert/device. |
| What evidence supports the claim? | Evidence `derived_from` observable events and `supports_claim` edges. |
| Was sharing permitted and redacted? | Authorization/redaction/share nodes and package integrity status. |
| Which assumptions remain open? | Assumption entities and owner/status metadata. |

The exported `competency_queries.json` is part of the required run bundle and is checked by tests for non-empty, data-derived results.
