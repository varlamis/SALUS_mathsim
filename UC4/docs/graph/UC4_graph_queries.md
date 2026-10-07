# UC4 temporal graph and competency queries

## Graph layers

`graph.json` is a directed temporal multigraph with two layers:

1. Validated static entity/relationship data from `uc4_entities.json` and `uc4_relationships.csv`.
2. Run-specific observed events, source records, authorization objects, policy decisions, evidence items, custody actions, and reconstruction claims.

Hidden ground-truth events are intentionally excluded. This prevents the graph query layer used by investigation and reconstruction from becoming an indirect oracle. Every node has `valid_from`/`valid_to` values, every edge uses the existing controlled relationship vocabulary, and every endpoint must resolve. The interchange contract is `models/schemas/runtime_graph.schema.json`.

## Runtime provenance paths

The graph encodes these principal traversals:

```text
physical/digital entity
  -> observed event
  -> retained source record
  <- evidence item
  -> authorization and policy decision
  -> custody action
  <- reconstruction claim
```

Direction follows the controlled relationship semantics rather than visual left-to-right order. For example, an entity `GENERATES` an event or record, evidence is `DERIVED_FROM` a source record, evidence is `AUTHORIZED_BY` an authorization, evidence is `CUSTODIED_BY` custody actions, and a claim `CORRELATES_WITH` supporting evidence.

## Query catalogue

| Query key | Answer and derivation |
|---|---|
| `physical_devices_and_twins` | Finds enabled physical entities carrying a `twin_id` and resolves the twin node. |
| `home_lan_routing` | Finds routing-capable gateways, shared multi-device zones, and `ROUTES_THROUGH` paths. |
| `source_artifacts` | Finds canonical network, Home Assistant, and device telemetry artefact classes and their generators. |
| `evidence_provenance` | Traverses each evidence item to source records/entities, authorization, policy decision, and custody actions. |
| `evidence_authorizations` | Returns the authorization and policy decision governing each collected item. |
| `policy_outcomes` | Returns allow/minimize/deny outcome, record, reason code, authorization, and released-byte count. |
| `claim_support` | Traverses each claim to evidence and matched observed events. |
| `assumptions_and_tbd` | Reports assumption-linked/TBD entities, interfaces, and relationships from provenance fields. |
| `service_feeds` | Classifies services from declared capabilities and resolves evidence/Digital Twin feeds; missing detection or SDN capability is reported as an explicit gap. |

The implementation uses entity classes, designations, capabilities, provenance, and relationship types. It does not maintain a parallel list of device or service names.

## CLI

Run all queries already embedded in a result package:

```powershell
salus-t43 graph-query --graph reports/generated/uc4/experiments/nominal_lawful_incident/graph.json
```

Run one query or write a separate response:

```powershell
salus-t43 graph-query `
  --graph reports/generated/uc4/experiments/nominal_lawful_incident/graph.json `
  --query evidence_provenance `
  --output reports/generated/uc4/evidence_provenance.json
```

Valid query names are the keys in the table above. Every simulation package already includes `competency_queries.json` with all nine results.

## Visualization

`graph_overview.svg` is a deliberately aggregated visualization. It shows the counts and flow across canonical entities, observations, policy decisions, evidence, custody, and claims, plus source-record and authorization totals. Rendering all runtime nodes and hundreds of parallel edges in a single figure would obscure rather than clarify provenance; exact paths remain available in JSON and through queries.

## Nominal graph result

The lawful incident run contains 37 enabled static nodes and 134 runtime nodes, for 171 nodes and 408 edges. It resolves six physical/twin pairs, five home-LAN routes through the CPE, three source-artefact classes, 17 evidence provenance/authorization paths, 33 policy decisions, and three claim-support paths.

The query layer explicitly reports that no enabled canonical service declares a detection capability and no SDN service is enabled. This is a model gap/TBD result, not an invented component. Detection remains represented by the case-trigger process, and SDN remains disabled/not applicable for this first UC4 acquisition path.
