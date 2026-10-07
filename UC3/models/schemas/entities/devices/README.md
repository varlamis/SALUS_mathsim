# Device-schema policy

UC3 process/control assets use the canonical entity schemas and the instances in `models/instances/uc3_entities.json`. This directory does not duplicate PLC, sensor or actuator schemas because the package deliberately models a non-sensitive surrogate. Specialized schemas require an expert-confirmed need, no operational secrets, and explicit migration/compatibility tests.
