# UC4 canonical entity and relationship model

## 1. Scope and authoritative artefacts

This document describes the Stage 3 canonical model for the agreed UC4 scenario. The authoritative files are:

- `models/schemas/entity.schema.json`: one canonical entity;
- `models/schemas/entity_collection.schema.json`: versioned entity collection;
- `models/schemas/relationship.schema.json`: one controlled graph relationship;
- `models/schemas/event.schema.json`: runtime event contract;
- `models/schemas/evidence.schema.json`: preserved evidence contract;
- `models/schemas/simulation_config.schema.json`: executable scenario configuration contract;
- `models/instances/uc4_entities.json`: 38 canonical UC4 entity instances;
- `models/relationships/uc4_relationships.csv`: 123 graph-ready relationships;
- `data/inventory/uc4_entity_inventory.csv`: source inventory corresponding exactly to the entity-instance IDs;
- `data/inventory/device_inventory.csv`: roadmap-compatible six-device inventory.

All schemas use JSON Schema Draft 2020-12 and schema version `1.0.0`. Instance data and schemas are separate. The preliminary JSON documents under `models/schemas/entities/devices/` remain legacy input and are not canonical JSON Schemas.

## 2. Entity hierarchy

The implemented UC4 hierarchy specializes the roadmap model as follows:

```text
SALUS_Entity
├── UseCase
├── Environment
│   ├── PhysicalEnvironment
│   └── NetworkZone
├── Actor
│   ├── HumanActor
│   ├── LEAUser
│   ├── HumanOrganisationActor
│   ├── OrganisationSystemActor
│   └── SystemActor
├── Asset
│   ├── Gateway
│   ├── GatewayServer
│   ├── Sensor
│   ├── SensorActuator
│   └── Actuator
├── ProcessService
│   ├── CloudService
│   ├── ForensicsService
│   └── DigitalTwinService
├── DataObject
│   ├── PolicyDataObject
│   ├── NetworkFlowLogEntry
│   ├── EventLogEntry
│   ├── EventTelemetry
│   ├── EvidenceItem
│   ├── Alert
│   ├── PolicyDecision
│   ├── CustodyEvent
│   └── AnalysisResult
└── DigitalTwinObject
    └── TwinEntity
```

The collection contains one use-case root, one physical environment, three network zones, six physical devices, six digital counterparts, six services, six actors, and nine data/policy/evidence entities.

## 3. Identity and reference rules

- `UC4` is the use-case graph root.
- Physical devices use `UC4-D01` through `UC4-D06`.
- Their twins use `UC4-DT01` through `UC4-DT06`.
- Services, actors, environments/zones, and data objects use `S`, `A`, `ENV/NZ`, and `DO` prefixes.
- Relationships use a gap-free `UC4-REL-###` sequence.
- Every entity and edge has `schema_version`, use-case membership, provenance, status, confidence, and applicable assumption IDs.
- All data references, network zones, relationship endpoints, twin IDs, and physical-entity IDs must resolve within the same collection.

## 4. Physical/digital twin invariant

For each enabled physical device `D_i`, exactly one active twin `DT_i` exists:

```text
UC4-D01 -> UC4-DT01  CPE
UC4-D02 -> UC4-DT02  Home Assistant
UC4-D03 -> UC4-DT03  Door sensor
UC4-D04 -> UC4-DT04  Presence sensor
UC4-D05 -> UC4-DT05  Smart plug
UC4-D06 -> UC4-DT06  Smart light
```

The physical instance carries `twin_id`; the twin carries `physical_entity_id`; the relationship inventory carries one matching `MIRRORED_BY` edge. A valid model requires all three representations to agree. Twin synchronization uses separately modelled `SYNCHRONIZES_WITH` edges and must reject stale versions as specified by `ASSUMPTION-UC4-022`.

## 5. Canonical relationship vocabulary

| Type | Semantics |
|---|---|
| `BELONGS_TO_USE_CASE` | Places an entity inside the UC4 scope. |
| `PART_OF` | Expresses logical containment of a zone/environment. |
| `DEPLOYED_IN` | Locates a physical asset in an environment. |
| `MEMBER_OF_ZONE` | Assigns an entity/interface to a network zone. |
| `OWNED_BY` | Associates an asset with its operational owner role. |
| `COMMUNICATES_WITH` | Describes directed logical information exchange. |
| `ROUTES_THROUGH` | Identifies the CPE as the communication/observation path. |
| `USES_INTERFACE` | Binds an interaction to an interface when instantiated. |
| `GENERATES` / `CONSUMES` | Connects producers/consumers to canonical data classes. |
| `OBSERVED_BY` / `COLLECTED_BY` | Separates observation from authorized forensic collection. |
| `PRODUCES_EVIDENCE` / `DERIVED_FROM` | Traces evidence creation and source provenance. |
| `AUTHORIZED_BY` / `REQUESTED_BY` | Links acquisition/evidence to authority and requester. |
| `ACCESSED_BY` / `CUSTODIED_BY` | Represents controlled access and custody responsibility. |
| `MIRRORED_BY` / `SYNCHRONIZES_WITH` | Represents physical/digital pairing and twin updates. |
| `TRIGGERS` / `AFFECTS` / `CORRELATES_WITH` | Represents causal, impact, and analytical relations. |
| `PROTECTED_BY` / `VIOLATES_POLICY` / `CONTROLLED_BY` | Represents security and policy controls; unused types remain available for runtime edges. |

Relationship direction is meaningful. `DERIVED_FROM`, for example, points from evidence to its source class. Runtime code may add instance-level edges but must use the same controlled vocabulary or a versioned schema revision.

## 6. Temporal and attribute semantics

The relationship model is a directed attributed temporal multigraph. `valid_from` is inclusive and `valid_to` is exclusive in simulation seconds. Empty CSV values mean an unbounded/static endpoint and are converted to JSON `null` before schema validation.

CSV list fields use semicolon-separated values:

- `source_references`;
- `assumption_ids`;
- `data_types`.

The flattened relationship attributes are `interface`, `protocol`, `authorization_relevance`, `data_types`, and `notes`. A graph loader must reconstruct them as the `attributes` object required by `relationship.schema.json`.

## 7. Provenance and uncertainty

`record_status` distinguishes proposal content, roadmap requirements, agreed decisions, assumptions, proposals, and unresolved `TBD` values. `confidence` expresses source/model confidence, not probability. Unconfirmed protocols remain `TBD/abstract`; they are not inferred from device type.

Assumptions resolve to `docs/assumptions/UC4_assumptions.md`. The legacy CPE inventory is referenced through `LEGACY-UC4-CPE-INVENTORY` and reconciled in `data/inventory/uc4_legacy_cpe_field_mapping.csv`.

## 8. Graph invariants and competency coverage

A conforming loader must enforce:

1. Unique entity and relationship IDs.
2. Existing source/target endpoints for every edge.
3. One `BELONGS_TO_USE_CASE` edge for every non-root entity.
4. Exact agreement among physical `twin_id`, twin `physical_entity_id`, and `MIRRORED_BY` edge.
5. No unknown relationship type.
6. Valid provenance and assumption references.
7. `valid_to > valid_from` when both are present.
8. One connected weak component rooted at `UC4`.

The current graph loads as a NetworkX `MultiDiGraph` with 38 nodes, 123 edges, and one weakly connected component. It supports queries for devices/twins, zones and routing, source artefacts, authorized collection, evidence derivation, custody, reconstruction support, and assumed/TBD relations.

## 9. Validation status and next step

Draft 2020-12 meta-schema validation passes for all seven schemas. All 38 entity instances validate, their IDs exactly match the entity inventory, all 123 relationships validate after canonical CSV conversion, every endpoint resolves, every non-root entity belongs to UC4, and all six twin mappings are reciprocal.

The formal model, BPMN processes/lifecycles, configuration validation, deterministic simulation, and 16-branch experiment matrix are implemented. Stage 9 adds the schema-validated temporal runtime graph, nine competency queries, and an SVG overview documented in `docs/graph/UC4_graph_queries.md`. The next ordered work is Stage 10 metrics, Monte Carlo experiments, and sensitivity analysis.
