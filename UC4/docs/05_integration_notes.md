# UC4 integration notes

The versioned machine-readable contracts are in `contracts/integration/uc4_integration_contracts.yaml`. They define abstract boundaries for CPE/Home Assistant/device observations, case and authorization context, acquisition, evidence/custody, reconstruction, Digital Twin and evaluation consumers.

No contract is a live endpoint or a grant of investigative authority. Transport, authentication, partner deployment, lawful basis, identity mapping, retention and operational error handling require owner approval. Adapters must validate schema/version, use stable UC4 IDs, preserve source and ingest times, report missingness, separate case trigger from authorization, minimize before disclosure and fail closed on invalid scope or evidence integrity.

Compatibility changes require a schema-version increment, migration entry, fixture update, negative test and regenerated manifest. Restricted real data remains outside the repository.
