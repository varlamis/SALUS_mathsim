# UC4 — Lawful forensic investigation in a smart home for IoT-enabled crime

## 0. Document status and authority

This document defines the agreed UC4 vertical slice to be modelled and simulated end-to-end for SALUS Task 4.3. It is the authoritative scenario contract for subsequent UC4 entity schemas, relationships, mathematical models, processes, code, tests, and generated deliverables.

The selected scenario and source precedence were approved as project implementation decisions. The implementation must therefore proceed without waiting for partner feedback. Details absent from the proposal are represented as explicit engineering decisions, configurable synthetic defaults, abstract interfaces, or `TBD` fields with safe fallbacks.

### 0.1 Status vocabulary

| Status | Meaning |
|---|---|
| `proposal` | Stated or directly supported by the SALUS proposal. |
| `roadmap` | Required or recommended by the T4.3 roadmap. |
| `agreed_decision` | Agreed for this end-to-end implementation but not claimed to be proposal text. |
| `assumed` | Needed for a complete model and considered plausible, but not source-confirmed. |
| `proposed` | A technical design choice to be implemented and kept replaceable. |
| `TBD` | A real deployment value is unavailable; the simulator must use a documented synthetic default. |

### 0.2 Source precedence

When sources disagree, use this order:

1. `docs/Proposal-SEP-211108743.pdf`.
2. `docs/SALUS_HUA_T4.3_Roadmap.docx`.
3. Existing repository content, after quality and provenance checks.
4. Explicit assumptions and engineering decisions in this document and the UC4 assumption register.
5. Later confirmed technical input, incorporated as a versioned configuration or adapter update rather than as a prerequisite.

### 0.3 Source references used here

| Reference ID | Source and relevant requirement |
|---|---|
| `PROPOSAL-PDF-p162-p164` | SDN/Digital Twin architecture; physical and digital entities, relations, intelligent services, simulation, evidence collection, and chain-of-custody context. |
| `PROPOSAL-PDF-p169-p170` | UC4 motivation, threats, lawful access through CPEs, DD-WRT/Home Assistant validation setting, representative devices, expected outcomes, and legal/privacy constraints. |
| `PROPOSAL-PDF-p171` | Candidate UC4 research datasets: IDSH smart-thermostat data and a smart-home intrusion-detection dataset. |
| `PROPOSAL-PDF-p190` | T4.3 obligation to formally and mathematically model physical entities, properties, processes, information exchange, digital replicas, and relations. |
| `ROADMAP-Phase-1` | Use-case decomposition template and minimum questions. |
| `ROADMAP-Phase-3-to-7` | Entity, relationship, process, graph, simulation, and validation requirements. |
| `LEGACY-UC4-CPE-INVENTORY` | Preliminary CPE fields in `data/inventory/device_and_system_inventory.csv`, `models/schemas/entities/devices/cpe_smart_home_gateway.json`, and the matching aggregate JSON entry; treated as hypotheses pending canonical mapping. |
| `AGREED-UC4-001` | Use UC4 and the unauthorized-entry/device-tampering scenario defined below as the end-to-end vertical slice. |
| `AGREED-UC4-002` | Proceed using the stated source precedence and replaceable defaults; partner feedback is not a completion dependency. |

## 1. Scenario summary

### 1.1 Agreed scenario

After an unauthorized entry into a smart home and suspected tampering with an IoT device, an authorized law-enforcement investigator remotely acquires scoped smart-home evidence through a lawful-interception module on the customer-premises equipment (CPE). The investigator correlates CPE network records with Home Assistant and device events to reconstruct the entry and tampering, while authorization, minimization, integrity, chain-of-custody, access, retention, and privacy controls are enforced and audited.

For a reproducible first implementation, the primary incident is fixed as follows:

1. An unauthorized actor opens a monitored door while the home is in a configured unoccupied/armed context.
2. The door/window sensor reports an `open` event.
3. A presence sensor may corroborate movement, subject to its configured detection probability, delay, and loss model.
4. A configured Home Assistant automation turns on a smart light, creating a causally related actuator event.
5. The unauthorized actor disconnects or disables the door/window sensor. Its state changes to `tampered` and then `offline`, or only to `offline` when the simulated device lacks a tamper capability.
6. The Home Assistant and CPE layers record partially overlapping traces. Observation delay, loss, clock offset, and CPE buffer pressure may make the evidence incomplete.
7. A separate synthetic case trigger causes an investigator to request remote acquisition. An anomaly never creates legal authority by itself.
8. A synthetic authorization object is verified and activated for specific entities, data types, purpose, and time window.
9. The CPE lawful-interception module collects only eligible CPE, Home Assistant, and device records. Out-of-scope data are denied or minimized.
10. Collected artefacts are hashed, registered in an append-only custody record, normalized, correlated, and used to reconstruct a supported timeline with uncertainty and missing observations.

The unauthorized-entry narrative and the precise tampering action are an `agreed_decision` derived from the proposal's wider set of smart-home threats. They are not represented as a verbatim or confirmed pilot script.

### 1.2 Why UC4 is suitable for the first vertical slice

UC4 has a concrete operational boundary, an explicit CPE acquisition point, a named open-source implementation direction, representative sensors and actuators, candidate research datasets, a forensic objective, and strong privacy/authorization constraints. It exercises all T4.3 dimensions in one scenario:

- physical entities and digital replicas;
- device state and behavior;
- communications and network observations;
- normal and abnormal processes;
- a lawful policy decision;
- evidence acquisition and custody;
- temporal/causal reconstruction;
- graph and Digital Twin integration.

## 2. Operational environment

### 2.1 Physical environment

- A controlled smart-home or laboratory representation of a residence.
- One monitored entrance equipped with a door/window contact sensor.
- An interior area covered by a presence/motion sensor.
- A smart light and smart plug representing common controllable actuators.
- A CPE router and a separate Home Assistant host or logical gateway.
- No actual resident, suspect, or investigator personal data are used in the simulator.

Room geometry, device placement, radio propagation, and exact building layout are outside the first model. Location is represented through stable logical zones unless a later configuration provides geometry.

### 2.2 Cyber environment

- A CPE/router providing the WAN/LAN boundary and hosting or exposing the simulated lawful-interception capability.
- A Home Assistant service maintaining a device registry, last-known state, automation rules, and event history.
- Simulated device adapters for the door/window sensor, presence sensor, smart plug, and smart light.
- An optional vendor-cloud service adapter, disabled by default unless a scenario configuration explicitly enables it.
- A secured LEA environment containing the investigator client, evidence repository, custody adapter, and reconstruction service.
- Digital counterparts for each in-scope physical device, synchronized using versioned timestamped state events.

### 2.3 Network environment

The minimum logical interaction is represented by the editable BPMN 2.0 collaboration model at `diagrams/process_flows/UC4_system_collaboration.bpmn`. Its pools separate the smart-home environment, CPE lawful-acquisition boundary, and LEA secured environment. BPMN message flows represent device observations, acquisition requests, scoped records, evidence manifests, and investigation results; they do not assert a confirmed physical link or protocol.

| BPMN participant/pool | Internal responsibility | Message flows |
|---|---|---|
| Smart-home environment | Door/presence events, Home Assistant correlation and automation, smart-light state, source-record availability. | Sends observable smart-home records to the CPE boundary when collected. |
| CPE and lawful-interception boundary | CPE flow logging, authorization decision, scoped acquisition, minimization, and denial paths. | Receives LEA request/authorization; returns eligible records or denial status. |
| LEA secured environment | Case trigger, acquisition request, evidence preservation, custody, reconstruction, and closure. | Sends scoped request; receives acquisition result; emits qualified investigation output. |

The BPMN diagram expresses system collaboration, not network topology. Exact connectivity and application protocols remain configuration parameters. The first simulator uses abstract message/flow objects so Wi-Fi, Ethernet, Zigbee, MQTT, HTTP, vendor protocols, or other adapters can be introduced without changing entity behavior. A separate graph model remains authoritative for physical/logical topology.

Required zones are:

| ID | Zone | Purpose |
|---|---|---|
| `UC4-NZ01` | Home IoT LAN | Internal smart-home devices and Home Assistant. |
| `UC4-NZ02` | WAN/Internet boundary | External network and optional vendor-cloud communication. |
| `UC4-NZ03` | LEA secured environment | Investigator, evidence, custody, and reconstruction services. |

### 2.4 Organizations and operational roles

- Law-enforcement organization: initiates and conducts the authorized investigation.
- Authorizing authority: issues the synthetic authorization object used by the model.
- Resident/data subject: produces normal household interactions and is protected by minimization/privacy rules.
- CPE/operator support role: represents the party or system enabling controlled access at the CPE boundary.
- Optional vendor-cloud operator: provides cloud-side records only if enabled and in scope.

These are model roles, not assertions about which named consortium partner performs each runtime action.

## 3. Main objective

Demonstrate, in a reproducible mathematical model and simulation, that a scoped remote forensic acquisition can retrieve and preserve relevant smart-home traces through a CPE, correlate them across heterogeneous sources, and reconstruct an unauthorized-entry/device-tampering sequence without exposing out-of-scope data.

The implementation must demonstrate technical behavior, not claim that simulation alone proves legal admissibility, GDPR compliance, real-device fidelity, or pilot KPI attainment.

## 4. Scope and boundaries

### 4.1 In scope

- Normal device, Home Assistant, and CPE behavior before the incident.
- Unauthorized door opening, possible motion detection, automation-triggered light activation, and sensor disconnection/tampering.
- Device, application, network, policy, evidence, and custody events.
- Physical-to-digital twin mappings and synchronization delay/staleness.
- Explicit separation of hidden simulation ground truth from investigator-visible observations.
- A case trigger independent from legal authorization.
- Synthetic authorization verification, activation, expiry, revocation, scope, purpose, and default-deny behavior.
- Historical and live remote acquisition through an abstract lawful-interception module.
- Data minimization, pseudonymous identities, evidence hashing, custody-chain creation, normalization, correlation, reconstruction, and uncertainty.
- Negative paths for absent/expired authorization, out-of-scope data, missing observations, buffer loss, clock skew, and evidence alteration.
- Machine-readable exports, competency queries, metrics, and automated tests.

### 4.2 Out of scope for the first vertical slice

- Interception of a real household or any real personal data.
- Exploitation, firmware modification, or remote control of real CPE/device hardware.
- Production integration with DD-WRT, Home Assistant, vendor clouds, judicial systems, blockchains, or LEA infrastructure.
- Packet-accurate router, wireless channel, or radio propagation emulation.
- Production anomaly-detection/ML model development.
- A conclusion that an identified real person committed an offense.
- Legal advice or proof of legal admissibility, GDPR compliance, or ethical approval.
- Exact manufacturer, protocol, log format, retention period, or deployment topology claims not supported by a source.
- Production SDN mitigation. UC4 policy enforcement is represented by the acquisition authorization gate unless SDN behavior is explicitly enabled in a later configuration.

## 5. Preconditions, trigger, and termination

### 5.1 Preconditions

1. All enabled entity instances and relations pass schema and referential-integrity validation.
2. Physical devices have unique active digital counterparts.
3. Simulation time, random seed, topology, device parameters, observation model, incident time, and policy configuration are resolved.
4. The home begins in the configured `unoccupied/armed` context.
5. Door sensor state is `closed/online`; presence is `clear/online`; smart light and plug have valid initial states.
6. Home Assistant and the CPE are operational and have bounded event/log buffers.
7. No evidence acquisition is active and no authorization is assumed merely from authentication.
8. All identities are synthetic or pseudonymous.

### 5.2 Operational trigger

The scenario incident begins when the seeded simulator dispatches `UC4-EVT-INCIDENT-ENTRY` at the configured incident time. Investigation begins only after a separate `UC4-EVT-CASE-TRIGGER`. Evidence collection begins only after the authorization object reaches `active` and the policy engine approves the specific request.

### 5.3 Success termination

The scenario succeeds technically when:

- collection has stopped at completion, expiry, or revocation;
- every released evidence item is authorized and provenance-linked;
- all evidence hashes and custody links verify;
- the reconstruction service emits claims supported by visible evidence IDs and expresses missing observations/uncertainty;
- all output objects validate against their schemas;
- no out-of-scope payload was disclosed;
- the run manifest contains configuration/schema/code versions, seed, and canonical output hashes.

### 5.4 Failure and degraded termination

The run must terminate safely and report an explicit result when:

- authorization is absent, denied, expired, revoked, or does not cover the requested item;
- source data are missing, overwritten, delayed, malformed, or outside retention;
- a device, Home Assistant, CPE, repository, or custody service is unavailable;
- hash/custody verification fails;
- clock uncertainty prevents a unique ordering;
- reconstruction is inconclusive.

These outcomes are valid experiment results. They must not be converted into fabricated evidence or unsupported conclusions.

## 6. Devices, systems, data objects, and other assets

### 6.1 Physical and software assets

| ID | Entity | Type | Owner/operator role | Location/zone | Scenario role | Source/status |
|---|---|---|---|---|---|---|
| `UC4-ENV01` | Smart-home premises | PhysicalEnvironment | Resident/lab operator | Physical smart home | Bounds physical incident events. | `proposal` + `agreed_decision` |
| `UC4-NZ01` | Home IoT LAN | NetworkZone | Resident/CPE operator | Home network | Carries internal IoT traffic. | `proposal`/`proposed` |
| `UC4-NZ02` | WAN boundary | NetworkZone | CPE/ISP role | CPE external interface | Bounds external communication. | `proposal`/`proposed` |
| `UC4-NZ03` | LEA secured environment | NetworkZone | LEA | LEA infrastructure | Hosts controlled forensic services. | `proposed` |
| `UC4-D01` | Open-source CPE router | Gateway/NetworkDevice | Resident/CPE operator | `UC4-NZ01`/`UC4-NZ02` | Routes traffic, maintains network records, exposes the controlled acquisition interface. | `proposal` |
| `UC4-D02` | Home Assistant host | Gateway/Server | Resident/lab operator | `UC4-NZ01` | Maintains registry/states/events and executes automations. | `proposal` |
| `UC4-D03` | Door/window contact sensor | Sensor | Resident/lab operator | Entrance, `UC4-NZ01` | Reports open/closed and optional tamper/offline state. | `proposal` + `agreed_decision` |
| `UC4-D04` | Presence sensor | Sensor | Resident/lab operator | Interior, `UC4-NZ01` | Provides probabilistic corroborating occupancy/motion evidence. | `proposal` + `agreed_decision` |
| `UC4-D05` | Smart plug | Sensor/Actuator | Resident/lab operator | Interior, `UC4-NZ01` | Provides command/state and optional consumption evidence. | `proposal` |
| `UC4-D06` | Smart light | Actuator | Resident/lab operator | Interior, `UC4-NZ01` | Executes the configured entry automation and logs state changes. | `proposal` + `agreed_decision` |
| `UC4-S01` | Vendor cloud adapter | CloudService | Vendor role | External/WAN | Optional off-premises events and commands; disabled by default. | `proposal`/`proposed` |
| `UC4-S02` | Lawful-interception module | ForensicsService | CPE/LEA service role | CPE/LEA boundary | Verifies decisions and performs scoped acquisition. | `proposal` |
| `UC4-S03` | Evidence repository | ForensicsService | LEA | `UC4-NZ03` | Stores content-addressed evidence and metadata. | `proposal`/`proposed` |
| `UC4-S04` | Custody ledger adapter | ForensicsService | LEA | `UC4-NZ03` | Records append-only custody actions and hash links. | `proposal`/`proposed` |
| `UC4-S05` | Reconstruction service | ForensicsService | LEA | `UC4-NZ03` | Normalizes/correlates evidence into qualified claims. | `roadmap`/`proposed` |
| `UC4-S06` | Digital Twin service | DigitalTwinService | SALUS | Digital world | Maintains replicas, relations, and simulation state. | `proposal` |

### 6.2 Data, policy, and evidence objects

| ID | Object | Type | Purpose | Required properties |
|---|---|---|---|---|
| `UC4-DO01` | Authorization object | Policy/DataObject | Governs acquisition. | Issuer, subject, case, purpose, target entities, allowed data types, valid interval, evidence time window, status, signature/verification result. |
| `UC4-DO02` | CPE network record | NetworkFlow/LogEntry | Network-level source artefact. | Flow/session ID, endpoints, times, counters, decision, observation status; payload excluded by default. |
| `UC4-DO03` | Home Assistant event | Event/LogEntry | Automation-level source artefact. | Entity ID, state transition, event/ingest times, correlation, context, provenance. |
| `UC4-DO04` | Device state event | Event/Telemetry | Physical-device observation. | Device/twin ID, previous/current state, event/ingest times, quality, sequence/version. |
| `UC4-DO05` | Evidence item | EvidenceItem | Preserved source artefact. | Evidence ID, content hash, source, acquisition method/times, authorization, transformations, sensitivity, custody status. |
| `UC4-DO06` | Case trigger | Alert | Starts investigative workflow, not collection authority. | Trigger ID, time, reason, source, case ID, severity, status. |
| `UC4-DO07` | Policy decision | PolicyDecision | Audits allow/deny/minimize. | Request, authorization, resource, decision, reason code, policy version, time. |
| `UC4-DO08` | Custody action | CustodyEvent | Records handling history. | Evidence, actor, action, time, previous/current hash, storage reference. |
| `UC4-DO09` | Reconstruction claim | AnalysisResult | States a supported investigative inference. | Claim, time interval, evidence IDs, confidence, uncertainty, alternatives, missing observations. |

## 7. Actors

| ID | Actor | Type | Role | Interacts with | Constraints |
|---|---|---|---|---|---|
| `UC4-A01` | Resident/data subject | HumanActor | Generates normal household interactions and protected contextual data. | Devices, Home Assistant | Synthetic identity only; data minimized. |
| `UC4-A02` | Authorized investigator | LEAUser | Submits scoped request and reviews reconstruction. | `UC4-S02`, `UC4-S03`, `UC4-S05` | Authentication plus active authorization required. |
| `UC4-A03` | Authorizing authority | HumanActor/Organisation | Issues the synthetic authorization used by policy tests. | `UC4-DO01`, `UC4-S02` | Simulator models validation semantics, not real judicial procedure. |
| `UC4-A04` | CPE/operator support role | Organisation/SystemActor | Provides/operates controlled CPE access mechanism. | `UC4-D01`, `UC4-S02` | No unrestricted evidence access. |
| `UC4-A05` | Unauthorized actor | HumanActor | Causes entry and disables/disconnects the door sensor. | `UC4-D03`, physical environment | Synthetic actor; identity is not inferred by the model. |
| `UC4-A06` | System auditor | SystemActor/LEAUser | Verifies policy, evidence, and custody records. | `UC4-S03`, `UC4-S04` | Read-only audit role. |

## 8. Data sources

| ID | Data source | Produced by | Data type | Frequency/trigger | Sensitivity | Used by | Status/notes |
|---|---|---|---|---|---|---|---|
| `UC4-DS01` | Door state/tamper/connectivity events | `UC4-D03` | Device event | State change/heartbeat | Medium–High contextual | Home Assistant, twin, collector | Tamper capability configurable. |
| `UC4-DS02` | Presence/motion events | `UC4-D04` | Device event | Detection/heartbeat | High contextual | Home Assistant, twin, reconstruction | Includes false-positive/false-negative model. |
| `UC4-DS03` | Smart-light command/state events | `UC4-D06` | Command and device event | Automation/manual state change | Medium contextual | Home Assistant, twin, reconstruction | Brightness optional; on/off mandatory. |
| `UC4-DS04` | Smart-plug command/state/consumption | `UC4-D05` | Command, telemetry | Configured interval/state change | Medium contextual | Home Assistant, twin, reconstruction | Consumption optional. |
| `UC4-DS05` | Home Assistant event log | `UC4-D02` | Application log | Event-driven | High household-context | Collector, reconstruction | Contains device and automation correlations. |
| `UC4-DS06` | Home Assistant registry/last state | `UC4-D02` | Snapshot/configuration | On request/change | High device identity/context | Collector, graph, reconstruction | Historical completeness is configurable. |
| `UC4-DS07` | CPE flow metadata | `UC4-D01` | Network flow/log | Flow/event/aggregation interval | High network metadata | Collector, reconstruction | Payload collection disabled by default. |
| `UC4-DS08` | CPE DHCP/device registry | `UC4-D01` | Network configuration/history | Lease/change | High device identity | Collector, entity correlation | DHCP is `assumed`; adapter is replaceable. |
| `UC4-DS09` | Acquisition/policy audit | `UC4-S02` | Policy/audit log | Every request/decision | Critical operational | Auditor, repository | Must record denied paths without forbidden payload. |
| `UC4-DS10` | Evidence manifest | `UC4-S03` | Evidence metadata | Every collected item | Critical forensic | Custody, reconstruction, auditor | Content-addressed and authorization-linked. |
| `UC4-DS11` | Custody log | `UC4-S04` | Append-only audit | Every custody action | Critical forensic | Auditor | Hash-chain abstraction, not production blockchain. |
| `UC4-DS12` | Optional cloud events | `UC4-S01` | Cloud log | Event-driven | High contextual | Collector/reconstruction | Disabled unless enabled and authorized. |
| `UC4-DS13` | Hidden simulation truth | Simulator only | Evaluation event stream | Every simulated transition | Restricted evaluation | Metrics/tests only | Never available to investigator/reconstruction input. |
| `UC4-DS14` | IDSH dataset adapter | External research dataset | CSV network/environmental | Offline experiment | Dataset-dependent | Calibration/comparison | Candidate named by proposal; acquisition/licensing and mapping remain separate work. |
| `UC4-DS15` | Smart-home IDS dataset adapter | External research dataset | CSV network features | Offline experiment | Dataset-dependent | Calibration/comparison | Candidate named by proposal; not required for first synthetic run. |

Every event source must keep `event_time`, `ingest_time`, `collection_time`, and `custody_time` distinct when applicable. Exports use UTC timestamps; simulation ordering uses monotonic numerical time.

## 9. Normal behavior

Normal operation is defined by configuration and must include:

1. The CPE routes abstract home-LAN messages and generates bounded flow/device records.
2. Home Assistant maintains a registry and last-known state for enabled devices.
3. Online devices emit state changes and optional heartbeats at configured rates.
4. During an expected authorized resident entry, door opening may be followed by presence and light automation events without a tamper/offline transition.
5. The smart light changes state only following a configured automation or valid command.
6. The smart plug follows valid commands and reports its state; optional power measurements remain non-negative and bounded.
7. Digital twins accept newer versioned updates, record synchronization lag, and reject stale updates.
8. Buffers apply explicit retention and overflow rules. Loss is recorded as loss, not silently hidden.
9. The lawful-interception module remains inactive without a verified active authorization and approved request.
10. No forensic evidence is emitted during ordinary monitoring unless the scenario explicitly models a separately authorized collection period.

Normal behavior is a distribution, not a single trace. Rates, delays, observation probabilities, clock offsets, and resident activity use seeded configurable synthetic parameters.

## 10. Abnormal/threat behavior

### 10.1 Primary abnormal sequence

The primary scenario combines:

- unauthorized physical entry;
- use of smart-home devices as witnesses to physical activity;
- device tampering through disconnection/disablement of the door sensor;
- incomplete and heterogeneous observations;
- a later remote forensic acquisition.

Expected traces may include a door-open event, motion event, automation command, light state change, Home Assistant state/context entries, CPE flows or device-presence records, loss of door-sensor heartbeat/connectivity, and a state transition to `unavailable/offline`. Not every trace is guaranteed to be visible.

### 10.2 Alternative explanations to preserve

The reconstruction must not equate correlation with identity or guilt. At minimum retain these competing explanations:

- benign authorized entry combined with sensor battery/network failure;
- false-positive presence detection;
- Home Assistant/CPE clock skew or delayed ingestion;
- automation misconfiguration;
- device malfunction rather than deliberate tampering;
- loss/overwrite of records due to buffer limits.

### 10.3 Negative and degraded branches

The same scenario model must support test branches for:

- no authorization;
- invalid signature/verification result;
- authorization not yet valid, expired, or revoked;
- requested device/data type/time outside scope;
- minimization rejection or redaction;
- missing door or presence event;
- CPE/Home Assistant buffer overflow;
- device, gateway, or WAN outage;
- large clock offset/reordering;
- evidence modification after collection;
- broken custody link;
- optional cloud service unavailable.

## 11. End-to-end operational sequence

| Step | Phase | Action | Responsible entity | Input | Output/audit |
|---|---|---|---|---|---|
| 1 | Initialization | Validate configuration, schemas, IDs, relationships, seed, and invariants. | Simulator/validator | Resolved config and instances | Run manifest or actionable failure. |
| 2 | Warm-up | Generate normal states, heartbeats, flows, and twin updates. | Devices, Home Assistant, CPE, twin | Initial states | Ground truth and observable baseline events. |
| 3 | Incident | Open monitored door in the unoccupied/armed context. | `UC4-A05`, `UC4-D03` | Incident event | Door state/event and network/application traces. |
| 4 | Corroboration | Detect presence probabilistically. | `UC4-D04` | Physical movement | Motion event or explicit missed observation in truth. |
| 5 | Automation | Trigger configured light-on rule. | `UC4-D02`, `UC4-D06` | Door/motion context | Command, acknowledgement, state event. |
| 6 | Tampering | Disconnect/disable the door sensor. | `UC4-A05`, `UC4-D03` | Tampering action | Tamper/offline/heartbeat-loss traces. |
| 7 | Case trigger | Create a synthetic investigative case trigger. | External case source | Incident notification | `UC4-DO06`; no collection authority. |
| 8 | Authorization request | Submit a scoped acquisition request. | `UC4-A02` | Case and desired sources/window | Request audit event. |
| 9 | Authorization decision | Verify issuer, status, validity, target, types, purpose, and scope. | `UC4-S02` | `UC4-DO01` and request | Allow/deny/minimize decision with reason. |
| 10 | Acquisition | Retrieve eligible CPE, Home Assistant, and device records. | `UC4-S02` | Approved resources | Source artefacts or safe failure records. |
| 11 | Preservation | Canonicalize, hash, store, and register custody. | `UC4-S03`, `UC4-S04` | Collected artefacts | Evidence items and custody actions. |
| 12 | Normalization | Map source-specific records to canonical events without erasing raw provenance. | `UC4-S05` | Evidence items | Normalized event set. |
| 13 | Reconstruction | Normalize clocks, correlate traces, and form qualified claims. | `UC4-S05` | Visible evidence only | Timeline, confidence, alternatives, gaps. |
| 14 | Closure | Stop collection and verify outputs/custody/policy results. | `UC4-S02`–`UC4-S05` | Completion/expiry/revocation | Metrics, validation report, investigation summary. |

## 12. Required process families

The process-model document expands these into step tables, failure paths, and editable BPMN 2.0 XML diagrams. Pools, lanes, message events, gateways, boundary events, data objects, and data stores are used according to BPMN semantics. The detailed catalogue is `docs/processes/UC4_processes.md`; the five authoritative diagrams are listed below.

### `UC4-PR01` — Normal operation

Device interaction -> device state event -> Home Assistant ingestion -> automation evaluation -> optional actuator command -> CPE observation -> digital-twin synchronization.

Authoritative model: `diagrams/process_flows/UC4_normal_operation.bpmn`.

### `UC4-PR02` — Incident/abnormal behavior

Unauthorized door opening -> possible motion corroboration -> automation/light response -> sensor disconnect/tamper -> incomplete observations and state divergence.

Authoritative model: `diagrams/process_flows/UC4_incident.bpmn`.

### `UC4-PR03` — Detection and case trigger

Observed rule/anomaly or external report -> explainable alert context -> human/system case trigger -> investigation request. The trigger must not activate collection.

Authoritative model: `diagrams/process_flows/UC4_detection_case_trigger.bpmn`.

### `UC4-PR04` — Lawful policy enforcement and acquisition

Request -> authentication -> authorization validation -> scope/time/purpose/minimization decision -> acquisition activation -> eligible collection -> termination on completion/expiry/revocation. Default decision is deny.

Authoritative model: `diagrams/process_flows/UC4_lawful_acquisition.bpmn`.

### `UC4-PR05` — Evidence collection and investigation

Source acquisition -> canonicalization -> content hash -> evidence registration -> custody action -> normalization -> temporal/relational correlation -> qualified reconstruction -> controlled access/closure.

Authoritative model: `diagrams/process_flows/UC4_evidence_investigation.bpmn`.

## 13. Authorization, privacy, and evidence constraints

1. Authentication and authorization are separate.
2. The policy engine defaults to deny for missing, invalid, unknown, or ambiguous inputs.
3. Authorization scope includes case, purpose, target entities, allowed data types, valid interval, evidence time window, and permitted actions.
4. Out-of-scope requests generate a decision record but no protected payload.
5. Payload/content capture is disabled by default; flow metadata is collected only when in scope.
6. Minimization happens before release into the investigator-visible evidence set.
7. Fixtures contain synthetic/pseudonymous identifiers only.
8. Hidden ground truth is restricted to simulator evaluation and cannot be consumed by reconstruction code.
9. Raw source, normalized event, evidence item, custody action, and reconstruction claim are separate objects linked by provenance.
10. Every evidence transformation creates a new derived object; raw evidence is not overwritten.
11. Every evidence item records content hash, source, acquisition method and times, authorization ID, transformations, sensitivity, and custody status.
12. The simulated append-only hash chain is an integrity/custody abstraction, not a production blockchain claim.
13. A technical test of these controls does not constitute a legal-compliance or admissibility determination.

## 14. Forensic questions

The model and generated investigation package must answer:

1. What physical and digital events occurred around the configured incident window?
2. Was the door reported open, and by which source(s)?
3. Did presence, light, plug, Home Assistant, or CPE evidence corroborate activity?
4. When did the door sensor become tampered/offline, and what observations support that claim?
5. Which events are direct observations, derived events, or inferred claims?
6. Which source artefacts were expected but missing, and why might they be missing?
7. How do clock offset, latency, loss, and retention affect event ordering?
8. Which devices communicated, through which abstract interfaces and zones?
9. Which CPE/Home Assistant/device records were eligible for collection?
10. Which authorization and policy decision permitted each evidence item?
11. Were any requests denied, minimized, expired, or revoked, and why?
12. Did all evidence content hashes and custody links verify?
13. What competing benign or technical explanations remain?
14. Can the available evidence support unauthorized entry and sensor tampering as separate qualified claims?
15. What cannot be concluded, especially about actor identity, intent, guilt, or legal admissibility?

## 15. Modelling requirements

### 15.1 Entity and graph requirements

- Stable IDs for all entities, twins, events, relations, policies, evidence, custody actions, and claims.
- A directed attributed temporal multigraph with controlled relation vocabulary.
- Exactly one active digital counterpart for each enabled physical device.
- Source/status/confidence and validity interval on every relationship.
- No dangling entity or evidence references.
- Graph queries linking incident -> observations -> evidence -> authorization -> custody -> reconstruction.

### 15.2 Behavioral requirements

- Explicit state machines for the door sensor, presence sensor, smart light, smart plug, Home Assistant, CPE acquisition module, authorization, evidence lifecycle, and investigation case.
- Hybrid discrete-event semantics with a monotonic simulation clock.
- Separate event and ingest times, configurable delays/loss/clock offsets, and bounded buffers.
- Seeded randomness with no hidden module-level random state.
- Reversible configuration for unconfirmed rates, protocols, formats, and capabilities.
- Enforced state bounds and transition invariants.

### 15.3 Formal mathematical requirements

The formal model must define:

- system state, entity state vectors, event tuple, queue, and transition function;
- sensor detection/error behavior and actuator transitions;
- CPE capacity, buffering, observation, delay, and loss abstraction;
- authorization eligibility and default-deny rules;
- digital-twin synchronization, lag, and stale-update rejection;
- evidence hash/custody transition rules;
- reconstruction correlation and uncertainty representation;
- initial conditions, units, valid ranges, synthetic-default status, and calibration path.

### 15.4 Simulation/output requirements

- Deterministic canonical outputs for identical code/configuration/seed.
- Baseline, primary incident, and negative/degraded executions.
- Strict ground-truth/observed-evidence separation.
- Validated JSON/JSONL/YAML/CSV exports and a run manifest.
- Evidence capture, disclosure, latency, reconstruction, custody, twin-lag, network, and assumption-coverage metrics.
- Automated tests for schemas, graph integrity, dynamics, authorization, custody, corruption, reproducibility, and the end-to-end run.

## 16. Configuration decisions and replaceable defaults

The following values must be configured, never buried in code:

| Decision area | First-build decision | Replacement mechanism |
|---|---|---|
| Device brands/models | Generic devices only. | Entity-instance configuration and adapter. |
| Device protocols | Abstract event/flow interface. | Protocol adapter plus relation attributes. |
| CPE platform | Generic open-source-router model compatible with the proposal direction. | CPE adapter; optional DD-WRT adapter later. |
| Home automation | Home Assistant logical model. | Home Assistant API/log adapter later. |
| Cloud access | Disabled by default. | Enable configured cloud adapter plus authorization scope. |
| Tampering mechanism | Door sensor disconnect/disable after entry. | Incident configuration strategy. |
| Event rates/delays/loss | Named synthetic defaults with units/status. | YAML parameters or calibrated dataset profile. |
| Authorization workflow | Synthetic signed/verified policy object and state machine. | Authorization provider adapter. |
| Retention | Synthetic bounded buffers with explicit durations/capacities. | Policy configuration. |
| Evidence storage | Local content-addressed simulation repository. | Evidence-store adapter. |
| Custody | Append-only SHA-256 hash chain. | Production ledger adapter. |
| SDN mitigation | Disabled/not applicable for first UC4 acquisition path. | Explicit T4.2 policy configuration/adapter. |
| External datasets | Optional; not required for initial synthetic execution. | Dataset loader, licence/provenance record, field mapping. |

## 17. Acceptance criteria

The scenario contract is satisfied by the eventual implementation only when all criteria below are testable and pass:

1. A clean command validates all UC4 model inputs and runs the agreed incident with a documented seed.
2. The run includes all enabled entities and unique physical-to-digital mappings.
3. The hidden truth contains the door entry and configured sensor tampering transitions.
4. Investigator-visible data contain only observations produced and successfully retained/collected by the configured observation model.
5. The case trigger alone cannot start collection.
6. Missing, invalid, expired, revoked, or out-of-scope authorization yields no protected evidence payload.
7. Valid authorization releases only eligible data types, entities, actions, and time ranges after minimization.
8. Every evidence item resolves to source artefact(s), policy decision, authorization, collector, hash, and custody history.
9. Deliberate evidence or custody alteration is detected.
10. Reconstruction code cannot access hidden ground truth.
11. Reconstruction claims cite evidence IDs, confidence/uncertainty, alternatives, and missing expected observations.
12. Equal seeds and resolved configurations produce identical canonical result hashes.
13. Buffer loss, missed presence detection, and clock skew are visible in metrics and can degrade reconstruction without crashing the run.
14. Graph competency queries resolve entities, zones, communications, evidence derivation, authorization, custody, twins, and assumptions.
15. All JSON Schema, runtime-model, graph-integrity, unit, negative-path, and end-to-end tests pass.
16. The generated report clearly labels synthetic defaults and makes no claim of real-device fidelity, legal admissibility, GDPR compliance, production readiness, or pilot KPI attainment.

## 18. Required run outputs

One end-to-end run must emit:

```text
run_manifest.json
resolved_config.yaml
entities.json
relationships.json
ground_truth_events.jsonl
observed_events.jsonl
policy_decisions.jsonl
evidence_manifest.json
custody_events.jsonl
reconstructed_timeline.json
graph.json
metrics.json
validation_report.json
investigation_summary.md
```

Canonical serialization must be defined before calculating hashes. Generation time is stored separately so it does not break seeded reproducibility.

## 19. Traceability from requirement to deliverable

| Requirement | Primary future artefact |
|---|---|
| Use-case decomposition and boundaries | This document |
| Canonical entities and devices | `data/inventory/uc4_entity_inventory.csv`, `data/inventory/device_inventory.csv`, `models/instances/uc4_entities.json` |
| Formal entity/process/information-exchange model | `models/formal/uc4_mathematical_model.md` |
| Relations/digital world | `models/relationships/uc4_relationships.csv`, `models/graph/uc4_graph.json` |
| Process families | `docs/processes/UC4_processes.md`, `diagrams/process_flows/UC4_*.bpmn` |
| Physical/digital state behavior | `src/salus_t43/uc4/entities.py`, `dynamics.py`, `diagrams/state_machines/UC4_entity_lifecycles.bpmn` |
| Lawful access control | `authorization.py`, `collection.py`, policy tests |
| Evidence integrity/custody | `collection.py`, `custody.py`, integrity tests |
| Reconstruction | `reconstruction.py`, generated timeline and summary |
| Digital Twin simulation | `simulation.py`, graph/twin state exports |
| Validation and competency questions | `tests/`, `reports/validation/UC4_validation_matrix.md` |
| Integration contracts | `docs/05_integration_notes.md` |

## 20. Scenario readiness decision

The UC4 scenario, assumption register, inventories, schemas, formal model, BPMN models, validation, deterministic simulator, and 16-branch experiment matrix are complete through Stage 8. Stage 9 is complete: each run exports a schema-validated temporal graph, nine data-driven competency-query results, and an SVG overview; all experiment packages have been regenerated. The graph excludes hidden ground truth and preserves traversable observation, source, evidence, authorization, policy, custody, and claim provenance. Missing deployment facts remain replaceable synthetic defaults. The next ordered action is Stage 10: implement statistically documented Monte Carlo and sensitivity analysis over the existing metric definitions.
