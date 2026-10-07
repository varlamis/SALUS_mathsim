# UC1 validation matrix

| Requirement | Status | Evidence | Remaining work |
|---|---|---|---|
| Scenario and sources | Complete | `docs/use_cases/UC1.md` | Partner confirmation remains a calibration activity. |
| Entities and stable IDs | Complete | `models/instances/uc1_entities.json`; schema tests | Exact pilot inventory remains TBD. |
| Relationships and graph | Complete | 60 relations; graph tests and `models/graph/uc1_graph.json` | Deployment topology remains assumed. |
| Formal mathematical model | Complete | `models/formal/uc1_mathematical_model.md` | Parameters are synthetic. |
| Normal and attack process models | Complete | process docs and seven BPMN files | Partner workflow review pending. |
| Deterministic simulation | Complete | simulation and reproducibility tests | No live adapters by design. |
| Trust and message validation | Complete | validation events and negative branches | Cryptography is abstract. |
| Explainable detection | Complete | feature/score/explanation tests | Baseline rules are not trained AI. |
| Policy and mitigation | Complete | requested/applied decision records | T4.2 API TBD. |
| Controller safety | Complete | zero violations across tests/experiments | Not safety certification. |
| Evidence and custody | Complete | hash/minimization/tamper tests | Production storage TBD. |
| Runtime graph queries | Complete | graph/query tests | Persistent graph technology TBD. |
| Experiment matrix | Complete | nine passing branches | Further branches may be added after partner input. |
| Monte Carlo analysis | Complete | 100 predeclared synthetic samples | No pilot calibration. |
| Integration contracts | Complete | eight versioned contracts | Several transports remain proposed/TBD. |
| Clean-environment validation | Partial | locked environment and passing tests | Independent CI/platform run pending. |

