# UC4 assumption and engineering-decision register

## 1. Purpose

This register controls every non-source-confirmed detail required to build the UC4 end-to-end mathematical model and simulator. It implements the provenance rules in `docs/use_cases/UC4.md` and prevents plausible engineering choices from being presented as proposal facts.

The simulator must proceed using the defaults below. A later real-world value must replace a default through configuration, instance data, or an adapter; it must not require changes to the core event, evidence, authorization, or reconstruction semantics.

## 2. Status and change rules

- `accepted`: approved project modelling decision and safe to implement.
- `synthetic_default`: an executable value chosen for reproducibility, not calibrated to a real deployment.
- `TBD_real_value`: the simulator has a working fallback, but a deployment-specific value remains unknown.
- `retired`: no longer used; the record remains for traceability and points to its replacement.

Every revision must update the affected inventory/configuration artefacts, tests, and `CHANGELOG.md`. Never delete an assumption that has appeared in a generated run manifest.

## 3. Register

| ID | Status | Assumption or decision | Rationale/source | Chosen executable default | Affected model elements | Replacement mechanism | Impact if wrong |
|---|---|---|---|---|---|---|---|
| `ASSUMPTION-UC4-001` | accepted | The implemented incident is unauthorized door entry followed by deliberate door-sensor disconnection/disablement. | `AGREED-UC4-001`; consistent with threats in `PROPOSAL-PDF-p169-p170`. | Door opens, then `tampered -> offline`; devices without a tamper signal transition directly to `offline`. | Incident, door sensor, reconstruction. | Incident strategy in YAML. | Changes the evidence pattern and causal claims. |
| `ASSUMPTION-UC4-002` | accepted | The smart home is initially unoccupied and armed. | Needed to make entry abnormal; not stated by proposal. | `occupancy=unoccupied`, `security_context=armed`. | Environment, incident detector. | Scenario initial-state configuration. | Changes anomaly interpretation, not raw observations. |
| `ASSUMPTION-UC4-003` | accepted | CPE router and Home Assistant are separate logical entities even if co-hosted later. | Proposal names an open-source WAN/LAN router and an IoT residential gateway. | `UC4-D01` and `UC4-D02` are distinct. | Inventory, topology, graph, processes. | Deployment mapping may set common host ID while retaining logical IDs. | Conflating them would lose provenance and responsibility boundaries. |
| `ASSUMPTION-UC4-004` | TBD_real_value | Exact device manufacturers/models are unknown. | Roadmap prohibits invention. | Generic typed device instances only. | `UC4-D01`–`UC4-D06`. | Entity-instance fields or hardware adapter. | Vendor-specific behavior and available artefacts may differ. |
| `ASSUMPTION-UC4-005` | TBD_real_value | Exact device/application protocols are unknown. | Proposal lists representative devices but not UC4 protocol assignments. | Typed abstract message/flow interface; protocol value `TBD/abstract`. | Devices, traffic, relations. | Protocol adapter plus configuration. | Message timing, observability, and evidence fields may differ. |
| `ASSUMPTION-UC4-006` | accepted | CPE records flow metadata and a device-presence/lease history in bounded buffers. | Required for CPE-based reconstruction; legacy inventory proposes these sources. | Payload disabled; flow endpoints, times, counters, decision and observation state retained. | CPE, data sources `UC4-DS07/08`. | CPE adapter/capability profile. | Evidence capture and correlation may improve or degrade. |
| `ASSUMPTION-UC4-007` | accepted | Home Assistant retains registry, last-known states, automation context, and bounded event history. | Consistent with proposed Home Assistant validation environment. | In-memory/store-backed canonical events, maximum `10,000` events. | Home Assistant, evidence collection. | Home Assistant API/log adapter and retention config. | Missing context reduces causal reconstruction. |
| `ASSUMPTION-UC4-008` | accepted | Door sensor supports `closed`, `open`, `tampered`, and `offline`; tamper capability may be disabled. | Required by agreed scenario; hardware support is unknown. | Tamper capability enabled in primary synthetic run. | Door sensor dynamics. | Device capability configuration. | Without tamper signal, intent is less observable and inference confidence falls. |
| `ASSUMPTION-UC4-009` | synthetic_default | Presence sensing is imperfect. | Required to model evidential uncertainty. | Detection probability `0.95`, false-positive probability `0.01` per `1 s` evaluation window, reporting delay `0.20 s`, refractory period `2 s`. | Presence sensor, metrics. | Calibrated device/dataset profile. | Strongly affects corroboration and reconstruction recall. |
| `ASSUMPTION-UC4-010` | accepted | Door opening in armed context triggers a Home Assistant rule that turns on the smart light. | Agreed scenario needs a causal actuator trace. | Rule enabled; processing delay `0.10 s`; light acknowledgment delay `0.15 s`. | Home Assistant, smart light. | Automation-rule configuration. | Removes one corroborating trace if disabled. |
| `ASSUMPTION-UC4-011` | accepted | Smart plug is modelled but is not manipulated in the primary incident. | Proposal lists controlled switches/power plugs; keeps scope representative without inventing an extra attack. | Online/off state, periodic heartbeat; optional watts disabled. | Smart plug. | Incident and capability configuration. | Minimal effect on primary reconstruction. |
| `ASSUMPTION-UC4-012` | accepted | Vendor-cloud interaction is optional and disabled in the primary run. | Proposal notes cloud services, but access/capability is unspecified. | `UC4-S01.enabled=false`. | Cloud adapter, topology, acquisition. | Enable adapter and extend authorization scope. | Cloud evidence may otherwise add or expose contextual data. |
| `ASSUMPTION-UC4-013` | accepted | A case trigger and lawful authorization are independent objects and transitions. | UC4 legal/privacy objective and default-deny design. | Case trigger never activates collection. | Authorization and process models. | Normative; only external interface may change. | Combining them creates unauthorized disclosure risk. |
| `ASSUMPTION-UC4-014` | accepted | Authorization is represented by a synthetic verifiable object. | Needed for executable policy behavior without modelling real judicial procedure. | Fields: issuer, subject, case, purpose, targets, data types, actions, validity interval, evidence window, status, verification result. | `UC4-DO01`, policy engine. | Authorization-provider adapter. | Missing fields must cause denial. |
| `ASSUMPTION-UC4-015` | accepted | Policy evaluation defaults to deny and minimization happens before investigator-visible release. | Security/privacy invariant. | Unknown, invalid, ambiguous, expired, revoked, or out-of-scope request is denied. | Collection, tests, evidence outputs. | Normative; policy versions may extend rules. | Any permissive fallback could disclose protected data. |
| `ASSUMPTION-UC4-016` | synthetic_default | The primary authorization covers the incident sources and a bounded evidence window. | Needed for successful nominal acquisition. | Valid `t=900–1500 s`; evidence window `t=540–780 s`; allowed sources `D01–D06/D02 records`; metadata and state events only. | Config, policy tests. | Authorization fixture/configuration. | Changes which evidence is eligible. |
| `ASSUMPTION-UC4-017` | synthetic_default | The nominal simulation timeline is fixed and reproducible. | Supports deterministic tests. | Horizon `1800 s`; warm-up `300 s`; entry `600 s`; sensor disconnect `610 s`; case trigger `900 s`; request `920 s`. | Event queue, scenario config. | YAML time parameters. | Changes retention pressure and temporal correlations. |
| `ASSUMPTION-UC4-018` | synthetic_default | Entity clocks may differ from simulation time. | Required for realistic correlation uncertainty. | Per-source fixed offset sampled from `Uniform[-2,2] s`; timestamp jitter `Normal(0,0.05 s)` truncated to `±0.20 s`. | Events, reconstruction, metrics. | Clock profile/calibration configuration. | Ordering and claim confidence may change. |
| `ASSUMPTION-UC4-019` | synthetic_default | Communications are flow/event abstractions, not packet-accurate emulation. | Appropriate for T4.3 entity/process modelling. | CPE service capacity `10 Mbit/s`, byte buffer `1 MiB`, base delay `0.01 s`, jitter bound `0.005 s`, configurable loss; payload capture off. | Traffic and CPE queue. | Network profile or packet adapter. | Cannot support packet-level performance/security claims. |
| `ASSUMPTION-UC4-020` | synthetic_default | Nominal observation loss is low but non-zero. | Needed to keep observability distinct from truth. | Independent base loss probability `0.005`; source-specific overrides allowed. | Devices, CPE, Home Assistant, metrics. | Calibrated dataset/deployment profile. | Directly affects evidence recall. |
| `ASSUMPTION-UC4-021` | accepted | Every enabled physical device has exactly one active digital counterpart. | `PROPOSAL-PDF-p162-p164`; T4.3 roadmap. | `UC4-D01..D06` map to `UC4-DT01..DT06`. | Entity inventory, graph, twin service. | Versioned mapping record. | Ambiguous or missing twin state breaks graph and synchronization invariants. |
| `ASSUMPTION-UC4-022` | synthetic_default | Twin updates reject stale versions and expose synchronization lag. | Needed for deterministic state reconciliation. | Strictly increasing per-entity version; equal/older version rejected; stale threshold `5 s`. | Twin dynamics and tests. | DTE synchronization adapter. | Different conflict rules can change digital state. |
| `ASSUMPTION-UC4-023` | accepted | Evidence uses canonical serialization, SHA-256 content hashes, and an append-only custody hash chain. | Proposal custody/integrity context; implementation is not a production blockchain. | Local content-addressed repository and hash chain. | Evidence/custody. | Evidence-store and ledger adapters. | Affects interoperability, not the requirement to detect alteration. |
| `ASSUMPTION-UC4-024` | accepted | Raw source, observed event, evidence, normalized event, and reconstruction claim are distinct immutable/versioned objects. | Required for forensic provenance. | Derivations create new IDs and links; no raw overwrite. | Schemas, repository, reconstruction. | Normative data-contract revisions. | Conflation would invalidate provenance and evaluation. |
| `ASSUMPTION-UC4-025` | accepted | Hidden simulation truth is inaccessible to acquisition and reconstruction. | Required for honest evaluation. | Separate output and dependency boundary. | Simulator, tests, metrics. | Normative architecture invariant. | Leakage makes reconstruction metrics meaningless. |
| `ASSUMPTION-UC4-026` | accepted | Only synthetic/pseudonymous identities are generated. | Avoids use of personal data in the model. | IDs such as `resident-001`, never names or real addresses. | Actors, logs, evidence fixtures. | Synthetic identity provider. | Real identifiers would create unnecessary privacy risk. |
| `ASSUMPTION-UC4-027` | accepted | SDN mitigation is disabled for the first UC4 acquisition path. | No confirmed UC4 mitigation action; acquisition authorization is the relevant policy control. | `sdn_policy_required=No`; adapter inactive. | Inventory, process, integration. | Explicit T4.2 policy/adapter configuration. | Enabling SDN adds flows, policy decisions, and failure modes. |
| `ASSUMPTION-UC4-028` | accepted | Detection uses an explainable rule/case trigger, not a production ML model. | Keeps the vertical slice focused on T4.3 while preserving T3.3 integration. | Rule context: door opens while armed/unoccupied, optionally strengthened by motion/offline transition. | Alert/case trigger. | Detection adapter or trained model output contract. | Detection quality is not a project claim. |
| `ASSUMPTION-UC4-029` | accepted | Proposal-named UC4 datasets are optional calibration inputs, not prerequisites for the first run. | Their local availability, licences, and exact columns are not established. | Synthetic generator drives initial runs. | Data adapters, calibration. | Dataset ingestion after provenance/licence/field mapping. | Synthetic fidelity remains limited until calibration. |
| `ASSUMPTION-UC4-030` | accepted | Legacy CPE fields are hypotheses and require explicit mapping. | Current CSV and JSON disagree in naming/content. | Canonical fields plus `uc4_legacy_cpe_field_mapping.csv`; unsupported fields are not promoted. | Inventory and migration. | Versioned migration script/report. | Silent merging would obscure provenance and contradictions. |
| `ASSUMPTION-UC4-031` | synthetic_default | Source-record retention spans the nominal evidence window. | Required for a successful nominal acquisition while allowing negative retention tests. | Home Assistant `10,000` events; CPE `50 MiB` record capacity; records retained for at least `1,200 s` in nominal config. | CPE/Home Assistant buffers. | Retention configuration or real capability profile. | Shorter retention reduces evidence capture. |
| `ASSUMPTION-UC4-032` | accepted | Sensitivity labels in the canonical inventories are conservative engineering classifications. | Proposal requires privacy preservation but does not classify every field. | `Low/Medium/High/Critical` as recorded per entity/data class. | Inventory, minimization, outputs. | Versioned data-classification policy. | Labels control collection/redaction and storage handling. |
| `ASSUMPTION-UC4-033` | synthetic_default | Reconstruction uses an explainable weighted support score rather than a calibrated probability. | Enables deterministic qualified claims while source likelihoods are uncalibrated. | Missing penalty `0.25`; support weights: door `1.0`, presence `0.6`, light command/state `0.5` each, CPE flow `0.4`, tamper `0.9`, offline `0.8`, heartbeat cessation `0.5`; source reliabilities: D01 `0.80`, D02 `0.90`, D03 `0.95`, D04 `0.80`, D06 `0.90`, S03 `1.00`. | Reconstruction and claim metrics. | Versioned reconstruction configuration or calibrated inference model. | Changes claim strength labels and must not be interpreted as posterior probability. |

## 4. Verification requirements

| Assumption group | Verification method |
|---|---|
| `001–003`, `010–017`, `021–028` | Scenario, state-machine, policy, provenance, twin, and end-to-end tests derived from the formal model. |
| `004–008`, `011–012`, `029–032` | Schema/provenance checks plus adapter and configuration substitution tests; unsupported legacy fields must remain excluded. |
| `009`, `018–020`, `022`, `031` | Boundary, seeded reproducibility, statistical sanity, timing, conservation, overflow, retention, and stale-update tests. |
| `023–025` | Canonical hash, deliberate corruption, custody-chain, immutable derivation, and ground-truth isolation tests. |
| `026`, `032` | Fixture scanning, sensitivity-policy, minimization, and zero-disclosure checks. |
| `033` | Hand-calculated support-score fixtures covering support, contradiction, missing evidence, bounds, and undefined denominators. |

## 5. Invariants derived from the register

1. No unknown value may silently become “confirmed.”
2. A missing configuration value either receives the documented default or causes an actionable validation error.
3. Authentication without an active in-scope authorization cannot release evidence.
4. Denied requests may emit decision metadata but never protected source payload.
5. Reconstruction cannot read hidden ground truth.
6. Every enabled physical device has exactly one active twin mapping.
7. Every collected item has source, authorization, decision, hash, and custody references.
8. Same schema/code/configuration/seed yields identical canonical results.

## 6. Resolution workflow

When a real value becomes available:

1. Preserve the existing assumption ID and mark the prior value superseded in its revision history.
2. Add the new source reference and confidence.
3. Change configuration or adapter data, not core semantics, whenever possible.
4. Re-run schema, invariant, negative-policy, reproducibility, and end-to-end tests.
5. Compare metrics with the prior synthetic profile and document material changes.
