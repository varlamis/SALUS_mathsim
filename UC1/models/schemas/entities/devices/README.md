# Device-schema policy

UC1 device records use the canonical `entity.schema.json` and `entity_collection.schema.json`; canonical instances are in `models/instances/uc1_entities.json`. This directory is intentionally documentation-only because UC-specific duplicate device schemas would drift from the common envelope. Add a specialized schema here only when an expert-confirmed field cannot be represented by the canonical entity attributes, with a migration and compatibility test.
