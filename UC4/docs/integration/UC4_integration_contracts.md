# UC4 integration contracts and handoff

## Contract authority and compatibility

The machine-readable authority is `contracts/integration/uc4_integration_contracts.yaml`, validated by `models/schemas/integration_contracts.schema.json`. Contract-set version `1.0.0` uses semantic compatibility: a major version may change required fields or semantics; a minor version may add optional fields; a patch version may clarify documentation without changing wire behavior. Consumers must reject unsupported major versions and any unknown required semantics.

These are boundary contracts, not claims that external partner endpoints are deployed. `implemented_internal` means the behavior exists behind an in-process boundary. `abstract_adapter`, `disabled_by_default`, and `pilot_replacement` identify work that remains outside this repository.

## Contract overview

| ID | Task | Boundary | Current status | Fail-safe behavior |
|---|---|---|---|---|
| `UC4-IC-01` | T4.4 Digital Twin Engine | Physical/entity events, versioned twin state, lag, and simulation control | Internal implementation | Reject unknown/stale updates; preserve last accepted state |
| `UC4-IC-02` | T4.2 SDaaSS | Zones and metadata-only flows; abstract NBI/SBI | Disabled | Continue UC4 without SDN and never infer controller state |
| `UC4-IC-03` | T3.3 AI/XAI | Observed features out; traceable alert/explanation in | Abstract | Unavailable detector is not treated as a negative classification |
| `UC4-IC-04` | T3.4 threat intelligence | Provenance-qualified indicators/context and graph links | TBD adapter | Quarantine malformed/expired context; preserve evidence unchanged |
| `UC4-IC-05` | T3.5 identification/lawful interception | Pseudonymous device identity, scoped request, minimized evidence or denial | Internal implementation | Default deny with zero payload/bytes |
| `UC4-IC-06` | T3.1/T3.6 collection/sharing | Evidence, custody, recipient/purpose/redaction/encryption metadata | Internal evidence/custody; sharing abstract | Quarantine integrity failure and deny incomplete sharing controls |
| `UC4-IC-07` | WP6 UC4 pilot | Measured configuration and adapter provenance | Pilot replacement | Keep assumptions visible and abort schema/unit mismatch |

## Cross-contract invariants

1. `schema_version`, stable UC4 identifiers, units, event time, ingest time, acquisition time, and custody time retain their defined meanings.
2. Hidden ground truth never crosses an integration boundary except into evaluation-only metrics.
3. Case triggering, authentication, threat context, AI alerts, and SDN policy never substitute for acquisition authorization.
4. Device identities are synthetic/pseudonymous until an approved identity adapter supplies a confidence-qualified mapping.
5. Every released evidence item references its authorization and policy decision and is minimized before hashing.
6. Denial emits audit metadata only and releases zero evidence bytes.
7. Encryption and deployment RBAC are required T3.1/T3.6 integration controls but are not claimed as implemented by the synthetic in-memory adapter.
8. Unknown versions, units, identities, scopes, or required fields fail closed.

## WP6 replacement sequence

1. Record lab device, firmware, Home Assistant, CPE, network, clock, retention, and endpoint versions without storing credentials or personal data in the repository.
2. Copy the canonical configuration to a new versioned pilot configuration; never overwrite the synthetic reference.
3. For each numeric parameter, record unit, measurement source, sampling interval, uncertainty, device/firmware applicability, and approval provenance.
4. Implement adapters behind the contract boundaries while retaining canonical IDs and output schemas.
5. Validate source-to-canonical mappings using small approved fixtures, including missing, duplicated, late, stale, malformed, and unauthorized records.
6. Run repository validation, all automated tests, the experiment matrix, and a separately justified pilot analysis design.
7. Compare results against the synthetic reference, investigate hash/metric changes, and update assumptions and changelog.
8. Obtain any external technical, governance, or legal approvals through their owning processes; do not encode their absence as successful validation.

## Handoff checks

```powershell
salus-t43 validate --config configs/uc4/incident_lawful_access.yaml
python -m pytest -q
salus-t43 manifest --output reports/final/UC4_artifact_manifest.json
```

The manifest is self-excluded so it can list stable hashes of every final source, model, configuration, test, and generated report. Re-run it after any repository artefact changes.
