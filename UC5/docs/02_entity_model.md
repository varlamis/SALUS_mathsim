# UC5 canonical entity model

The canonical collection contains 34 entities and 45 typed relationships. Seven physical/cyber device classes include the active patient monitor, gateway, switch/enforcement point, collector, console and inactive wearable/infusion classes. Seven twins mirror those assets. Seven services represent registry, detection/XAI, clinical-safety policy, evidence/custody, redaction/sharing, reconstruction and threat context. Human/organization roles, four segregated zones and three data sources complete the model.

Each entity declares stable `UC5-*` ID, class/designation, role, allowed states, zone, optional twin, sensitivity, record status, sources, assumptions and limitations. Relations cover deployment/communication, observation, registration, care dependency, mirroring, protection/governance, triggers/mitigation and evidence/redaction/share/claim lineage. Validation rejects duplicate/dangling IDs and unresolved twin/zone references.

Patient monitor identity is synthetic and pseudonymous. `Critical` marks handling sensitivity, not a certified clinical risk class. The authoritative files are `models/instances/uc5_entities.json` and `models/relationships/uc5_relationships.csv`; the inventory CSV is a review projection.
