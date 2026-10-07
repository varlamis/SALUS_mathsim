# UC1 entity-relationship view

The authoritative entity set is `models/instances/uc1_entities.json`; the
authoritative typed edges are `models/relationships/uc1_relationships.csv`.
`models/graph/uc1_graph.json` is their generated runtime projection and must not
be edited independently.

```mermaid
flowchart LR
  V[Connected vehicle / OBU] -->|sends V2X message| R[Roadside unit]
  A[Attacker] -->|injects forged message| R
  PKI[V2X trust infrastructure] -->|supports credential validation| R
  R -->|forwards observation| D[Detection service]
  D -->|raises alert| P[Policy decision point]
  P -->|requests bounded mitigation| T[Traffic controller]
  T -->|applies safe phase| I[Intersection]
  D -->|emits evidence| E[Evidence store]
  E -->|supports reconstruction| X[Investigator]
```

This is a readable projection, not a second source of truth. Cardinalities,
identifiers, trust boundaries, and provenance are specified in the canonical
JSON/CSV model and the mathematical model.
