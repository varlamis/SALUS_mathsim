# UC3 validation matrix

| Capability | Status | Evidence | Limitation |
|---|---|---|---|
| Scenario/provenance | Complete | `docs/use_cases/UC3.md`; assumptions | Partner details remain TBD. |
| Entities and relationships | Complete | 36 entities; 60 typed relations | Synthetic/abstract inventory. |
| Strict schemas | Complete | nine Draft 2020-12 schemas | Production schema governance not assessed. |
| Formal model | Complete | `models/formal/uc3_mathematical_model.md` | One-vessel surrogate only. |
| BPMN and lifecycles | Complete | eight parseable BPMN files | No operational workflow claim. |
| Deterministic simulation | Complete | source/tests/generated run | No live interfaces. |
| Detection/XAI | Complete | weighted rules and explanations | Transparent baseline, not validated AI. |
| Safety-constrained policy | Complete | requested/applied/rejected records | Abstract enforcement only. |
| Evidence/custody/reconstruction | Complete | hashes, chain, tamper tests | Not an admissibility assessment. |
| Experiments | Complete | nine declared branches | Synthetic assertions. |
| Monte Carlo | Complete | 100 seeded samples | Not pilot calibration. |
| Runtime graph | Complete | static/runtime graph and queries | In-memory JSON projection. |
| Integration contracts | Complete | eight versioned boundaries | Transport/authentication TBD. |
| DS4/DS5 replay | TBD | raw-data boundary and mapping | Datasets not supplied/committed. |
| Nuclear plant fidelity | Not Applicable | explicit scope boundary | Deliberately prohibited. |
