# UC2 entity-relationship view

```mermaid
flowchart LR
  D1[3GPP observer] -->|observes| H[Device hypothesis]
  D2[Wi-Fi observer] -->|observes| H
  D3[BLE observer] -->|observes| H
  H -->|classified_by| C[Association/classification]
  C -->|checked_against| R[Approved-device registry]
  R -->|informs| X[Detection and XAI]
  X -->|triggers| P[Policy and review]
  X -->|generates| E[Evidence and custody]
  E -->|supports| I[Investigation/consultation]
  D1 -. mirrored_by .-> T1[Observer twin]
  H -. mirrored_by .-> TH[Hypothesis twin]
```

This view is explanatory. The authoritative endpoints and relation types are `models/relationships/uc2_relationships.csv`; the validated deterministic projection is `models/graph/uc2_graph.json`.
