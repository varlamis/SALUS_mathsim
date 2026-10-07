# UC1 entity model

The canonical entity collection is `models/instances/uc1_entities.json`; the CSV inventories are review views. Entity classes cover environments, zones, physical assets, logical services, actors, data, and twins. Every record has a stable UC1 ID, lifecycle states, designation, sensitivity, record status, source references, and assumption IDs.

Physical state, observed cyber state, Digital Twin state, evidence, and reconstructed claims are distinct. Only observations may update twins. Each modelled physical/twin mapping is one-to-one and expressed through `MIRRORED_BY` plus `SYNCHRONIZES_WITH` relations.

