# UC4 detailed process catalogue

## 1. Purpose and authority

This catalogue specifies the five UC4 process families required by the scenario contract. The editable BPMN 2.0 XML files under `diagrams/process_flows/` are the authoritative graphical process definitions; this document supplies the implementation contract behind their tasks, decisions, inputs, outputs, failures, audits, and formal-model links.

The models use BPMN sequence flows only within a participant, message flows only across participants, exclusive gateways for guarded decisions, timer/error boundary events for interrupting failures, lanes where one system contains materially different responsibilities, and data stores for retained artefacts. A case trigger never acts as legal authorization, latent ground truth never enters an evidence payload, and every deny path is fail-closed.

| Process ID | Family | Authoritative BPMN | Formal-model focus |
|---|---|---|---|
| `UC4-PR01` | Normal operation | `diagrams/process_flows/UC4_normal_operation.bpmn` | Sections 4–9 |
| `UC4-PR02` | Incident/abnormal behavior | `diagrams/process_flows/UC4_incident.bpmn` | Sections 5, 7, 8, 10 |
| `UC4-PR03` | Detection and case trigger | `diagrams/process_flows/UC4_detection_case_trigger.bpmn` | Sections 5, 10, 13 |
| `UC4-PR04` | Lawful policy enforcement/acquisition | `diagrams/process_flows/UC4_lawful_acquisition.bpmn` | Section 11 and invariants 16.3 |
| `UC4-PR05` | Evidence collection/investigation | `diagrams/process_flows/UC4_evidence_investigation.bpmn` | Sections 12–13 and invariants 16.4 |

## 2. Cross-process rules

1. `UC4-DO06` is the combined alert/case-trigger object. It may move from `created` to `acknowledged` and receive a case ID, but collection stays inactive until `UC4-DO01` is independently issued and validated. `UC4-DO08` remains the custody-action object.
2. An acquisition request is allowed only if authentication succeeds and every authorization dimension—status/signature, case binding, subject/target, entity, data type, action, purpose, and time window—is satisfied.
3. Authorization expiry or revocation interrupts collection. Uncommitted records are discarded, the result contains denial metadata only, and the reason is audited.
4. Only observable source artefacts may become `UC4-DO05`; latent simulation truth is inaccessible to acquisition and reconstruction components.
5. Source bytes are immutable. Normalization produces derived metadata or derived evidence linked by `DERIVED_FROM` and cannot overwrite the source item.
6. A reconstruction is a qualified technical result with uncertainty and alternatives; it is not a legal finding or proof of admissibility.

Audit labels below are normative event types for the simulator. Each audit event must carry `event_id`, `event_type`, simulation and source timestamps, actor/system ID, case ID when applicable, correlation ID, input/output entity IDs, outcome, reason code, and schema version.

## 3. `UC4-PR01` — Normal operation

Participants are physical devices `UC4-D03`–`UC4-D06`, Home Assistant `UC4-D02`, and the CPE/twin services `UC4-D01`/`UC4-S06`. The process establishes versioned device state, observable automation traces, bounded CPE records, and monotonic twin updates before any incident or collection.

| BPMN node(s) | Responsible entity | Input → output | Preconditions / guard | Failure or alternate path | Audit event | Formal reference |
|---|---|---|---|---|---|---|
| `Task_ReadPhysicalState` | `UC4-D03`–`D06` | bounded physical state → candidate state transition | Device lifecycle permits sampling | Offline device yields no accepted transition | `DEVICE_SAMPLE_ATTEMPTED` | §§6.4–6.7 |
| `Task_IncrementVersion` | `UC4-D03`–`D06` | accepted transition → monotonic version | State transition is valid | Invalid state is rejected | `DEVICE_STATE_VERSIONED` | §§4.2, 6 |
| `Send_DeviceEvent` | device adapter | state/version/correlation → `UC4-DO04` | Event schema and observability rules pass | Delivery/loss sampled by observation model | `DEVICE_EVENT_EMITTED` | §§4.2, 5.2 |
| `GW_CommandValid` | target device | command → allow/reject decision | `device.online ∧ command.permitted` | Default is reject | `COMMAND_DECIDED` | §§6, 7.2 |
| `Task_ApplyCommand` / `Task_RejectCommand` | target device | command → bounded new state or rejection | Gateway result | Rejection changes no protected state | `COMMAND_APPLIED` / `COMMAND_REJECTED` | §§6.6–6.7 |
| `Send_Ack` | target device | result → correlated acknowledgement | Command decision exists | Lost acknowledgement remains explicit missingness | `COMMAND_RESULT_EMITTED` | §§4.2, 5.2 |
| `GW_EventFresh` | `UC4-D02` | incoming version → fresh/stale | Incoming entity ID is registered | Default stale branch | `HA_EVENT_FRESHNESS_DECIDED` | §7.1 |
| `Task_UpdateRegistry` | `UC4-D02` | fresh event → HA state/history | `incoming.version > accepted.version` | `Boundary_HAIngestion` interrupts to audit path | `HA_EVENT_ACCEPTED` | §§7.1, 7.3 |
| `Task_AuditStale` | `UC4-D02` | stale/failed event → rejection record | Freshness or ingestion failed | Ends cycle without automation | `HA_EVENT_REJECTED` | §7.1 |
| `Task_EvaluateAutomation`, `GW_Automation` | `UC4-D02` | accepted event/rules → command/no command | Configured rule enabled | Default produces no command | `AUTOMATION_EVALUATED` | §7.2 |
| `Send_Command`, `Task_RecordResult` | `UC4-D02` | rule match → command/result history | Target known and rule matched | Rejection or missing ack is retained | `AUTOMATION_COMMAND_RECORDED` | §§7.2–7.3 |
| `Send_TwinUpdate`, `GW_TwinFresh` | `UC4-D02`, `UC4-S06` | versioned update → accept/reject | Twin mapping exists | Default rejects stale version | `TWIN_UPDATE_DECIDED` | §9 |
| `Task_ObserveFlow`, `Task_UpdateQueue`, `GW_Overflow` | `UC4-D01` | abstract flow → retained/drop decision | Monitoring enabled | Default records overflow/loss | `CPE_QUEUE_DECIDED` | §8 |
| `Task_RetainRecord` / `Task_RecordLoss` | `UC4-D01` | flow metadata → `UC4-DO02` or loss counter | Capacity and retention permit record | No fabricated record on loss | `CPE_RECORD_RETAINED` / `CPE_RECORD_DROPPED` | §§8.2–8.4 |
| `Task_AcceptTwin` / `Task_RejectTwin` | `UC4-S06` | twin update → new mirror state or rejection | Monotonic version guard | Stale update leaves state unchanged | `TWIN_STATE_UPDATED` / `TWIN_UPDATE_REJECTED` | §9 |

Completion: at least one normal event chain has stable entity IDs and correlation IDs; versions never decrease; retained histories obey configured bounds; no evidence collection is active.

## 4. `UC4-PR02` — Incident and abnormal behavior

This process keeps the simulated physical incident separate from the observations available to later investigators. Door and presence detections are probabilistic, tamper telemetry depends on device capability, and CPE retention is capacity-limited.

| BPMN node(s) | Responsible entity | Input → output | Preconditions / guard | Failure or alternate path | Audit event | Formal reference |
|---|---|---|---|---|---|---|
| `Task_Enter`, `Send_Entry` | `UC4-A05`, `UC4-ENV01` | incident schedule → latent entry/door transition | Premises armed; actor synthetic | Scenario cancellation yields no incident | `GROUND_TRUTH_ENTRY_SCHEDULED` (simulation-only) | §10 |
| `Task_SelectTamper`, `Send_Tamper` | `UC4-A05` | configured target/action → latent tamper transition | Target is one of configured device IDs | Unsupported action is configuration error | `GROUND_TRUTH_TAMPER_SCHEDULED` (simulation-only) | §10 |
| `Task_SetDoorTruth` | `UC4-ENV01`, `UC4-D03` | physical entry → true door state `OPEN` | Valid door-state transition | Truth remains inaccessible outside simulator oracle | `GROUND_TRUTH_DOOR_CHANGED` | §§5.3, 6.4 |
| `GW_DoorObserved` | `UC4-D03` | true door change → detected/missed | Device online; Bernoulli draw fixed by seed | Default records missed observation | `DOOR_OBSERVATION_DECIDED` | §§5.2, 6.4 |
| `Task_EmitDoor` / `Task_RecordDoorMiss` | `UC4-D03` | decision → `UC4-DO04` or explicit loss | Gateway result | Miss produces no source event | `DOOR_EVENT_EMITTED` / `DOOR_EVENT_MISSED` | §§5.2, 10 |
| `GW_PresenceDetect` | `UC4-D04` | occupancy over 1 s → detected/missed | Sensor online; evaluation window closed | Default false-negative branch | `PRESENCE_OBSERVATION_DECIDED` | §§6.5, 10; A009 |
| `Task_EmitPresence` / `Task_RecordPresenceMiss` | `UC4-D04` | decision → presence event or loss | Gateway result | Missing event is not evidence of absence | `PRESENCE_EVENT_EMITTED` / `PRESENCE_EVENT_MISSED` | §§5.2, 6.5 |
| `GW_AutomationFire` | `UC4-D02` | observed door event/rule → command/no command | Door event arrived and `R_light=1` | Default preserves absence of trace | `INCIDENT_AUTOMATION_DECIDED` | §7.2 |
| `Task_LightCommand` / `Task_NoAutomation` | `UC4-D02`, `UC4-D06` | decision → light trace or explicit absence | Gateway result | Command reject/loss remains observable missingness | `INCIDENT_LIGHT_TRACE_RECORDED` / `INCIDENT_AUTOMATION_ABSENT` | §§5.2, 7.2 |
| `GW_TamperVisible` | tamper target | action/capabilities → visible/hidden | Target exists | Default when no tamper capability | `TAMPER_VISIBILITY_DECIDED` | §§6, 10 |
| `Task_EmitTamper` / `Task_OnlyOffline` | target device | tamper → event+offline or offline-only | Capability guard | Offline-only path must not invent tamper event | `TAMPER_EVENT_EMITTED` / `DEVICE_OFFLINE_OBSERVED` | §10 |
| `Send_SourceRecord` | `UC4-D02` | observable events → source records | Only observable partition selected | `Boundary_HAUnavailable` records service failure | `HA_INCIDENT_RECORD_PUBLISHED` | §§5.3, 7.3 |
| `Task_ObserveMetadata`, `GW_RecordRetained` | `UC4-D01` | traffic/log signal → retain/drop | Monitoring active | Default is explicit drop | `INCIDENT_CPE_RECORD_DECIDED` | §8 |
| `Task_RetainIncident` / `Task_RecordIncidentLoss` | `UC4-D01`, `UC4-S06` | decision → retained record/twin update or loss count | Queue/retention guard | Dropped data never reappears downstream | `INCIDENT_CPE_RECORD_RETAINED` / `INCIDENT_CPE_RECORD_DROPPED` | §§8–9 |

Completion: the oracle timeline and observable timeline are separate; all observation losses and device/source failures are reproducible from the seed and visible in metrics.

## 5. `UC4-PR03` — Detection and case trigger

The detector emits an explainable candidate, a human investigator decides whether to open a case, and `UC4-S02` records only a pending request-preparation state. This process cannot activate acquisition.

| BPMN node(s) | Responsible entity | Input → output | Preconditions / guard | Failure or alternate path | Audit event | Formal reference |
|---|---|---|---|---|---|---|
| `Task_SelectObservable` | `UC4-D01`, `UC4-D02` | closed 1 s window → observable records | Window watermark reached | Latent truth excluded | `DETECTION_WINDOW_SELECTED` | §§4–5 |
| `Send_Observations` | source adapters | records → versioned window | Schema/provenance present | Missing delivery closes without trigger | `DETECTION_WINDOW_PUBLISHED` | §§4.2, 5.2 |
| `Task_ValidateWindow` | `UC4-S05` | window → validated features | IDs, schema, provenance and clock bounds valid | Invalid window is detector error | `DETECTION_INPUT_VALIDATED` | §§5, 13.1 |
| `Task_EvaluateDetector`, `GW_IncidentPredicate` | `UC4-S05` | features → trigger/no-trigger | `armed ∧ ¬expected_occupied ∧ score ≥ θ_alert` | Default no-trigger; boundary error degrades safely | `INCIDENT_PREDICATE_EVALUATED` | §§10, 13.3 |
| `Task_ConstructAlert`, `Send_Alert` | `UC4-S05` | matched rule + event IDs → `UC4-DO06` | Predicate true | Alert contains no unreferenced assertion | `ALERT_CREATED` | §§4.2, 13 |
| `Task_CloseWindow` | `UC4-S05` | non-match → no-trigger record | Predicate false | No case and no collection | `NO_ALERT_DECISION` | §13.3 |
| `Task_DegradedAudit` | `UC4-S05` | detector exception → degraded record | `Boundary_DetectorError` fired | Must not trigger on error | `DETECTOR_DEGRADED` | Invariant §16.2 |
| `Task_ReviewAlert`, `GW_OpenCase` | `UC4-A02` | alert summary/provenance → open/close decision | Investigator authenticated for case management | Default closes candidate | `CASE_CANDIDATE_REVIEWED` | UC4 scenario §11 |
| `Task_CreateCase` | `UC4-A02` | approved `UC4-DO06` → acknowledged `UC4-DO06` plus case ID | Human decision is `OPEN_CASE` | Collection remains inactive | `CASE_OPENED` | Authorization separation §11.1 |
| `Send_CaseTrigger` | `UC4-A02` | case ID/alert ID → preparation notice | Case exists | Message carries no collection permission | `CASE_TRIGGER_SENT` | §11.1 |
| `Task_CloseFalsePositive` | `UC4-A02` | rejected candidate → closure reason | Default/close decision | Preserve source alert for audit retention only | `CASE_CANDIDATE_CLOSED` | §13.4 |
| `Task_RegisterPending`, `Task_AuditSeparation` | `UC4-S02` | case trigger → pending state | Case ID resolvable | No authorization means no source query | `CASE_PENDING_AUTHORIZATION` | §§11.1, 16.3 |

Completion: every alert lists supporting event IDs and the rule trace; false-positive, detector-error, and open-case paths terminate explicitly; no path from this diagram reaches evidence acquisition.

## 6. `UC4-PR04` — Lawful policy enforcement and acquisition

This collaboration separates the investigator, independent authority, acquisition module, and evidence sources. Inside `UC4-S02`, lanes separate policy evaluation, acquisition/minimization, and audit/response.

| BPMN node(s) | Responsible entity | Input → output | Preconditions / guard | Failure or alternate path | Audit event | Formal reference |
|---|---|---|---|---|---|---|
| `Task_DraftScope` | `UC4-A02` | case → proposed purpose/targets/types/actions/window | Open case; no active collection | Incomplete scope cannot be submitted | `AUTHORIZATION_SCOPE_DRAFTED` | §11.2 |
| `Send_AuthRequest` | `UC4-A02` | draft → authority request | Case ID and requester identity present | Await/timeout handled by caller configuration | `AUTHORIZATION_REQUESTED` | §11.1 |
| `Task_ReviewLegalBasis`, `GW_IssueAuth` | `UC4-A03` | request → approve/refuse | Independent authority workflow | Default is refusal | `AUTHORIZATION_REVIEWED` | §§11.1–11.2 |
| `Task_CreateAuthorization` / `Task_CreateRefusal` | `UC4-A03` | decision → signed `UC4-DO01` | Decision complete | Refusal grants no actions and no scope | `AUTHORIZATION_ISSUED` / `AUTHORIZATION_REFUSED` | §11.2 |
| `Task_BindRequest` | `UC4-A02` | authorization/session/case → acquisition request | All IDs agree | Mismatch must be rejected by policy gate | `ACQUISITION_REQUEST_BOUND` | §11.3 |
| `Task_Authenticate`, `GW_Authenticated` | `UC4-S02` | session → authenticated role decision | Identity provider response available | Default deny; no source query | `REQUESTER_AUTHENTICATED` / `AUTHENTICATION_DENIED` | §11.3 |
| `Task_VerifyAuthorization`, `GW_AuthValid` | `UC4-S02` | `UC4-DO01` → validity decision | Signature, status, case and time available | Default deny for invalid/expired/revoked/unknown | `AUTHORIZATION_VALIDATED` / `AUTHORIZATION_DENIED` | §§11.1–11.3 |
| `Task_CheckScope`, `GW_InScope` | `UC4-S02` | request/auth → Boolean `ScopeOK` | Authorization valid | Any dimension outside scope denies entire request | `AUTHORIZATION_SCOPE_EVALUATED` | §11.3 |
| `Send_SourceQuery` | `UC4-S02` | allowed request → least-privilege query | All policy predicates true | Never sent on deny branch | `SOURCE_QUERY_ISSUED` | §§11.3–11.4 |
| `Task_ResolveSources`, `Task_ReadWindow` | `UC4-D01/D02` adapters | scoped query → immutable candidate records | Adapter/entity/type/time are authorized | Unavailable source leads to timeout; no widening | `SOURCE_WINDOW_READ` | §§8.4, 11.3 |
| `Catch_SourceRecords` + `Boundary_AuthExpiry` | `UC4-S02` | candidate records or expiry/revocation → continue/stop | Authorization remains active throughout | Interrupts collection and discards uncommitted records | `COLLECTION_INTERRUPTED_AUTHORIZATION` | §§11.1, 16.3 |
| `Catch_SourceRecords` + `Boundary_SourceTimeout` | `UC4-S02` | wait → timeout | 5 s synthetic timeout (configurable) | Deny with source-timeout metadata | `COLLECTION_SOURCE_TIMEOUT` | A019/config |
| `Task_Minimize` | `UC4-S02` | candidates → authorized field projection | Records still in scope | Redacted/out-of-scope fields never enter package | `RECORDS_MINIMIZED` | §11.4 |
| `GW_NonEmpty` | `UC4-S02` | projection → package/deny | Minimization completed | Default deny when empty | `MINIMIZED_RESULT_EVALUATED` | §11.4 |
| `Task_PackageCandidates` | `UC4-S02` | projected records → source bytes/provenance/decision ref | Non-empty allowed projection | Not yet a verified evidence item | `EVIDENCE_CANDIDATES_PACKAGED` | §12.1 |
| `Task_Deny` | `UC4-S02` | failure reason → denial metadata | Any failed gate or empty projection | Payload count fixed to zero | `ACQUISITION_DENIED` | Invariant §16.3 |
| `Task_RecordDecision`, `Send_Result` | `UC4-S02` | allow/deny → append-only decision + response | Terminal policy outcome exists | Audit failure is fatal and withholds payload | `POLICY_DECISION_RECORDED` | §§11.3, 16.3 |
| `Task_AcceptCandidates` / `Task_AcceptDenial` | `UC4-A02` | response → preservation handoff or closure | Correlation/request IDs match | Denial cannot be treated as empty evidence | `ACQUISITION_RESPONSE_ACCEPTED` | §11.3 |

Completion: allow and deny results are mutually exclusive; every request has exactly one policy decision; deny results have zero evidence payload; expiration/revocation prevents later source commits.

## 7. `UC4-PR05` — Evidence collection and investigation

This process turns authorized candidates into immutable evidence, maintains custody, reconstructs a traceable timeline, and subjects the package to an independent technical audit. Repository and custody responsibilities are modeled as separate lanes.

| BPMN node(s) | Responsible entity | Input → output | Preconditions / guard | Failure or alternate path | Audit event | Formal reference |
|---|---|---|---|---|---|---|
| `Task_BindDecision`, `Send_Candidates` | `UC4-S02` | candidates + policy decision → preservation transfer | Acquisition outcome is allow | Denial path cannot enter this process | `EVIDENCE_TRANSFER_INITIATED` | §§11.3, 12.1 |
| `Task_ValidateCandidate` | `UC4-S03` | candidate → validated source/provenance | Schema, scope proof and hash fields present | Invalid candidate is quarantined by implementation adapter | `EVIDENCE_CANDIDATE_VALIDATED` | §12.1 |
| `Task_Canonicalize` | `UC4-S03` | source metadata → canonical metadata | Source bytes immutable | Normalized data becomes derived data | `EVIDENCE_METADATA_CANONICALIZED` | §§12.1–12.2 |
| `Task_HashStore` | `UC4-S03` | source bytes → SHA-256/content-addressed object | Candidate valid | `Boundary_StorageFailure` interrupts; no incomplete item exposed | `EVIDENCE_STORED` / `EVIDENCE_STORAGE_FAILED` | §12.1 |
| `Task_AppendCustody` | `UC4-S04` | evidence ID/hash → chained custody entries | Stored object resolvable | Missing predecessor invalidates chain | `CUSTODY_TRANSITION_APPENDED` | §12.3 |
| `Task_VerifyIntegrity`, `GW_Integrity` | `UC4-S03/S04` | bytes/hash/chain → valid/invalid | Hash and full chain readable | Default quarantine | `EVIDENCE_INTEGRITY_VERIFIED` / `EVIDENCE_INTEGRITY_FAILED` | §§12.1, 12.3 |
| `Send_VerifiedEvidence` | `UC4-S03` | evidence IDs/hashes → verified manifest | Integrity gateway passed | Raw ground truth and unverified items excluded | `VERIFIED_MANIFEST_SENT` | §§5.3, 12 |
| `Task_QuarantineIntegrity` / `Task_QuarantineStorage` | `UC4-S03/S04` | defect → quarantine record | Failure detected | No reconstruction use | `EVIDENCE_QUARANTINED` | Invariant §16.4 |
| `Task_LoadEvidence` | `UC4-S05` | verified manifest → allowed evidence set | Every item listed and verified | Unknown/unlisted item rejected | `RECONSTRUCTION_EVIDENCE_LOADED` | §§12.2, 13 |
| `Task_NormalizeClocks` | `UC4-S05` | local timestamps/clock bounds → uncertainty intervals | Clock domain known or bounded assumption exists | Unknown domain widens interval | `CLOCKS_NORMALIZED` | §13.1 |
| `GW_OrderingCertain`, `Task_OrderCertain`, `Task_OrderUncertain` | `UC4-S05` | intervals → deterministic or alternative partial orders | Normalization complete | Overlap defaults to uncertain ordering | `EVENT_ORDERING_CLASSIFIED` | §13.1 |
| `Task_Correlate` | `UC4-S05` | ordered evidence → causal/relational groups | Entity, correlation or temporal links available | Unlinked items stay explicit orphans | `EVIDENCE_CORRELATED` | §§12.2, 13.2 |
| `Task_ScoreClaims` | `UC4-S05` | support/contradiction/missingness → claim scores | Weights/reliabilities configured | Missing evidence penalizes; it is not negative proof | `CLAIMS_SCORED` | §13.3; A033 |
| `Task_Alternatives` | `UC4-S05` | correlated evidence → incident and benign alternatives | At least one candidate explanation | No forced binary conclusion | `ALTERNATIVES_EVALUATED` | §13.4 |
| `GW_Support`, `Task_QualifiedFinding`, `Task_Inconclusive` | `UC4-S05` | score/integrity → qualified or inconclusive finding | No fatal integrity defect for supported branch | Default is inconclusive | `RECONSTRUCTION_OUTCOME_DECIDED` | §§13.3–13.4 |
| `Send_Reconstruction` | `UC4-S05` | timeline/alternatives/trace → report | Outcome and all evidence references complete | Report generation failure leaves case open | `RECONSTRUCTION_REPORT_SENT` | §13 |
| `Task_AuditReview`, `GW_PackageValid` | `UC4-A02/A06` | report + policy/hash/custody proofs → accept/reject | Reviewer has read access under case scope | Default reject/quarantine | `INVESTIGATION_PACKAGE_AUDITED` | §§16.3–16.4 |
| `Task_AcceptReport` / `Task_RejectReport` | `UC4-A02/A06` | audit decision → final technical bundle or defect record | Gateway decision | Acceptance states no legal/admissibility conclusion | `INVESTIGATION_PACKAGE_ACCEPTED` / `INVESTIGATION_PACKAGE_REJECTED` | §19 limitations |

Completion: each evidence item has source provenance, an authorization/policy-decision reference, content hash, and valid custody chain; every reconstruction assertion points only to verified evidence IDs and reports uncertainty, missingness, assumptions, and alternatives.

## 8. Cross-file handoffs and ordering

The intended orchestration is:

1. `UC4-PR01` establishes valid normal state and baseline records.
2. `UC4-PR02` applies the configured incident and produces a lossy observable trace alongside an isolated oracle trace.
3. `UC4-PR03` evaluates observable data, optionally creates `UC4-DO06`, and may open a case; it never grants collection authority.
4. `UC4-PR04` obtains/verifies `UC4-DO01`, enforces scope and minimization, and emits candidates only on an allowed transaction.
5. `UC4-PR05` preserves, verifies, correlates, reconstructs, and audits the technical investigation package.

The system-level collaboration in `diagrams/process_flows/UC4_system_collaboration.bpmn` is a compact context view. If it conflicts with a detailed family diagram, the detailed family diagram and this catalogue govern; if BPMN behavior conflicts with the formal model's invariants, the formal model governs and the BPMN must be corrected.

## 9. BPMN validation contract

Before simulator implementation, automated validation must confirm for every authoritative BPMN file:

- well-formed XML and unique IDs;
- resolvable `processRef`, `sourceRef`, `targetRef`, `messageRef`, `attachedToRef`, `dataStoreRef`, `errorRef`, and BPMNDI `bpmnElement` references;
- at least one collaboration, participant, process, start event, end event, and BPMN diagram;
- message flows cross participant boundaries and sequence flows remain inside a process;
- every exclusive gateway has an explicit default and every non-default decision branch has a condition;
- each boundary event has an outgoing exception path;
- all flow nodes and flows intended for reporting have BPMNDI shapes/edges;
- no Mermaid or generic flowchart is used as an authoritative process representation.

SVG/PNG renderings are generated views only. They must never be edited independently of the `.bpmn` source.

The six required entity/service lifecycles are modeled separately in `diagrams/state_machines/UC4_entity_lifecycles.bpmn` and specified in `docs/processes/UC4_lifecycles.md`.
