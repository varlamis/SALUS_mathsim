# UC4 Stage 9 graph-query validation report

## Outcome

Stage 9 passes. The nominal lawful-incident temporal graph conforms to `runtime_graph.schema.json`, contains no unresolved endpoints or duplicate edge IDs, and excludes hidden ground truth.

| Measure | Nominal result |
|---|---:|
| Enabled static nodes | 37 |
| Runtime nodes | 134 |
| Total nodes | 171 |
| Total edges | 408 |
| Physical-to-twin pairs | 6 |
| Home-LAN entities routed through CPE | 5 |
| Canonical source-artefact classes | 3 |
| Evidence provenance paths | 17 |
| Evidence authorization paths | 17 |
| Policy outcomes | 33 |
| Claim-support paths | 3 |
| Assumption/TBD records | 170 |

## Competency findings

- All six configured physical devices resolve to exactly one canonical twin.
- Home Assistant and the four smart devices on `UC4-NZ01` resolve through the routing-capable CPE.
- CPE records, Home Assistant events, and device-state telemetry are identified from their entity classes and `GENERATES` relations.
- Every nominal evidence item resolves to a source record/entity, one authorization, one policy decision, and custody actions.
- Every reconstructed claim resolves to supporting evidence and observed event IDs; no claim path resolves to hidden ground truth.
- Policy results retain decision and reason codes, including record-window denials within an otherwise lawful acquisition.
- Provenance queries expose assumed/TBD interfaces and relationships rather than presenting them as confirmed deployment facts.
- Evidence repository, custody, and Digital Twin feeds resolve from capabilities and relationships.
- No canonical service declares a detection capability, and no SDN service is enabled. Both are explicitly reported gaps; no component is fabricated to satisfy the query.

## Generated artefacts

Each regenerated experiment package now includes:

- `graph.json`: complete static-plus-runtime temporal graph;
- `competency_queries.json`: all nine query results;
- `graph_overview.svg`: compact graph-layer visualization.

The nominal artefacts are under `reports/generated/uc4/experiments/nominal_lawful_incident/`. All 16 Stage 8 packages were regenerated so policy-denial, missing-observation, integrity-failure, and service-unavailable paths can be queried independently.

## Limitations

The graph is an internally consistent synthetic model, not a discovered production topology. Instance paths demonstrate provenance and access-control behavior but do not establish legal admissibility, real-device fidelity, or actual deployment integration.
