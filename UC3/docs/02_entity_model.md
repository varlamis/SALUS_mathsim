# UC3 entity model

The canonical source is `models/instances/uc3_entities.json`; relationships are in `models/relationships/uc3_relationships.csv`. Entities cover four network zones, process/sensor/actuator/controller assets, supervisory/network systems, nine twins, security/forensic services, human/organisation roles, and synthetic/dataset inputs.

Every record carries stable ID, class, designation, state vocabulary, zones, twin mapping, sensitivity, status, source references, assumptions, and limitations. The generated graph is never edited independently. Physical truth, controller state, observations, alerts, evidence, and claims are distinct types.
