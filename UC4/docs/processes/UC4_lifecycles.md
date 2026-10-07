# UC4 entity lifecycle specification

## 1. Authority and representation

The authoritative editable diagram is `diagrams/state_machines/UC4_entity_lifecycles.bpmn`. It contains six event-driven BPMN processes for the lifecycles required by Stage 5:

1. investigation alert/case trigger `UC4-DO06`;
2. authorization object `UC4-DO01`;
3. CPE lawful-acquisition module `UC4-S02`, hosted at the `UC4-D01` boundary;
4. door sensor `UC4-D03`;
5. Home Assistant connectivity `UC4-D02`;
6. evidence item `UC4-DO05`.

Tasks prefixed `[STATE]` encode persistent lifecycle states. Events between them encode transition triggers. Gateways encode mutually exclusive guards or competing events. BPMN is the visual/exchange representation; the state sets, equations, and invariants in `models/formal/uc4_mathematical_model.md` remain normative.

For data objects and services whose first listed state means “not instantiated” (`absent`, `inactive`, or `not_collected`), the waiting message-start event represents that state. Receipt of the message instantiates the process and performs the first transition. No hidden transition is implied.

## 2. Cross-lifecycle coupling

| Source lifecycle | Message/signal | Target lifecycle | Constraint |
|---|---|---|---|
| External detector | `Msg_Alert` | `DO06: absent → created` | Alert uses observable events only. |
| Investigator | `Msg_Acknowledge` | `DO06: created → acknowledged` | Assigns a case ID but grants no collection right. |
| `DO06` | `Msg_AuthRequest` | `DO01: absent → submitted` | Authorization is independent from case acknowledgement. |
| `DO06` | `Msg_CasePreparation` | `S02: inactive → request_received` | `S02` remains non-collecting while awaiting the decision. |
| `DO01` | `Msg_AuthDecision` | `S02: request_received → authorized/denied` | The active branch still requires `ScopeOK`; default is deny. |
| `DO01` | `Msg_AuthTerminal` | `S02: collecting → expired/revoked` | Interrupts collection and suppresses uncommitted payload. |
| `S02` | `Msg_Candidates` | `DO05: not_collected → collected` | Sent only from `completed`; all failure states send metadata only. |
| `S02` | `Msg_Denial` | `DO06: acknowledged → closed` | Closure records reason and zero disclosed evidence. |
| `DO05` | `Msg_EvidenceReady` | `DO06` | Only a verified evidence manifest is accepted. |
| Reconstruction service | `Msg_Reconstruction` | `DO06: acknowledged → closed` | Closure records qualified/inconclusive technical outcome. |

## 3. Investigation case trigger (`UC4-DO06`)

The canonical entity combines alert and case-trigger behavior; no separate case entity is invented. `UC4-DO08` remains the custody-action entity.

| Current state | Trigger | Guard | Next state | Mandatory effect |
|---|---|---|---|---|
| `absent` | Explainable alert received | Supporting event IDs and rule trace present | `created` | Freeze alert provenance and correlation ID. |
| `created` | Investigator acknowledgement | Investigator authenticated for case management | `acknowledged` | Assign case ID; record reviewer and decision time. |
| `acknowledged` | Acquisition denied/failed/expired/revoked | Terminal policy/acquisition result | `closed` | Record reason; evidence payload count must be zero. |
| `acknowledged` | Verified evidence then reconstruction | Manifest integrity valid; reconstruction references manifest | `closed` | Store technical outcome, uncertainty, and report ID. |

`created → closed` without acknowledgement is not modeled in the selected vertical slice; a future cancellation adapter may add it as a versioned transition.

## 4. Authorization (`UC4-DO01`)

| Current state | Trigger | Guard | Next state | Mandatory effect |
|---|---|---|---|---|
| `absent` | Authorization submission | Case/request identifiers present | `submitted` | Preserve submitted object/version. |
| `submitted` | Verification completes | Issuer/signature valid and required fields complete | `verified` | Record verification proof and policy version. |
| `submitted` | Verification fails or is ambiguous | Default branch | `denied` | Terminal for this version; grant no actions. |
| `verified` | Activation | `valid_from ≤ now < valid_to` | `active` | Notify `S02` of active status. |
| `active` | Validity timer fires | `now ≥ valid_to` | `expired` | Notify `S02`; terminal for this version. |
| `active` | Issuer revocation signal | Revocation identifies this authorization version | `revoked` | Notify `S02`; terminal for this version. |

`denied`, `expired`, and `revoked` have no outgoing state transition. A revised authorization receives a new version/ID and a new lifecycle instance.

## 5. CPE lawful-acquisition module (`UC4-S02`)

| Current state | Trigger | Guard | Next state | Mandatory effect |
|---|---|---|---|---|
| `inactive` | Case-preparation message | Case ID resolvable | `request_received` | Audit pending request; do not query sources. |
| `request_received` | Authorization decision | Active, verified, case-bound and `ScopeOK` | `authorized` | Record allow decision and permitted projection. |
| `request_received` | Any failed/unknown predicate | Default branch | `denied` | Return reason metadata with zero evidence bytes. |
| `authorized` | Start evaluation | Sources available and authorization remains active | `collecting` | Query only authorized adapters and minimize fields. |
| `authorized` | Source unavailable/guard false | Default branch | `failed` | Audit failure; return zero uncommitted payload. |
| `collecting` | Eligible reads complete | All committed records remain eligible | `completed` | Package and send authorized candidates. |
| `collecting` | Authorization expires | Matching authorization becomes `expired` | `expired` | Stop reads; discard uncommitted records. |
| `collecting` | Authorization revoked | Matching authorization becomes `revoked` | `revoked` | Stop reads; discard uncommitted records. |
| `collecting` | Source/audit timeout | Configured timeout reached | `failed` | Fail closed and audit source failure. |

The states `completed`, `denied`, `expired`, `revoked`, and `failed` are terminal for one acquisition transaction. A later request starts a new transaction in `inactive`.

## 6. Door sensor (`UC4-D03`)

| Current state | Trigger | Guard | Next state | Emission/effect |
|---|---|---|---|---|
| `closed_online` | `door.open` | Physical contact is open | `open_online` | Increment `v_D`; emit open event if observed. |
| `open_online` | `door.close` | Physical contact is closed | `closed_online` | Increment `v_D`; emit close event if observed. |
| `closed_online` or `open_online` | `device.tamper` | `gamma_D = 1` | `tampered` | Increment `v_D`; emit tamper event if observed. |
| Any online state | `device.disconnect` | Always true | `offline` | Preserve last logical state; increment `v_D`; emit offline event if observable. |
| `tampered` | `device.disconnect` | Always true | `offline` | Preserve `last_logical_state=tampered`. |
| `offline` | `device.restore` | Authorized maintenance | Configured `closed_online` or `open_online` | Increment `v_D`; emit recovery event. |

The formal tuple keeps logical state `z_D` and connectivity `c_D` independently, while the canonical inventory exposes the coarser states `closed_online`, `open_online`, `tampered`, and `offline`. Therefore the BPMN `offline` state must retain `last_logical_state`; it does not erase whether the preceding logical state was tampered. Duplicate/debounced events do not transition or increment `v_D`.

## 7. Home Assistant connectivity (`UC4-D02`)

| Current state | Trigger | Guard | Next state | Mandatory effect |
|---|---|---|---|---|
| `online` | Error/overload threshold | Health policy reports degradation | `degraded` | Continue bounded operation with quality/degradation flags. |
| `online` | Host/service outage | Health is offline | `offline` | Reject ingestion; no normal automation/event emission. |
| `degraded` | Health checks recover | Health is online | `online` | Resume normal processing without replaying stale versions. |
| `degraded` | Service failure | Health is offline | `offline` | Stop ingestion and automation. |
| `offline` | Authorized restoration | Service restored and registry integrity checks pass | `online` | Resume with prior accepted versions; reject stale updates. |

At the simulation horizon, the process ends without changing the current lifecycle state.

## 8. Evidence item (`UC4-DO05`)

| Current state | Trigger | Guard | Next state | Mandatory effect |
|---|---|---|---|---|
| `not_collected` | Authorized candidate received | Originating acquisition state is `completed` | `collected` | Fix source bytes, provenance, authorization, and policy-decision IDs. |
| `collected` | Registration succeeds | Canonicalization/hash/storage/custody append all succeed | `registered` | Persist content-addressed object and initial custody actions. |
| `registered` | Verification succeeds | Content hash and complete custody chain recompute | `verified` | Emit verified manifest for reconstruction. |
| `registered` | Verification fails | Default branch | `verification_failed` | Quarantine; do not expose to reconstruction. |
| `verified` | Retention expiry or authorized disposal | Disposal policy and custody action valid | `disposed` | Remove/dispose content as configured; retain permitted disposal proof. |

`verification_failed` is terminal in this version. Remediation creates a separately identified evidence item or custody correction; it cannot overwrite the failed item.

## 9. Validation invariants

1. Every transition endpoint belongs to the entity's canonical `allowed_states` set.
2. The case acknowledgement and authorization activation remain distinct transitions.
3. `S02.collecting` is reachable only through `request_received → authorized` with an active authorization and `ScopeOK=true`.
4. `S02.denied|expired|revoked|failed` can never send `Msg_Candidates`.
5. Door state version increases exactly once per accepted transition and never on duplicate input.
6. Home Assistant in `offline` emits no ordinary device/automation records.
7. Only `DO05.verified` emits `Msg_EvidenceReady`; `verification_failed` is quarantined.
8. All terminal transitions and rejected guards produce an audit event with entity/version/case/correlation/reason identifiers.
