# UC5 deterministic simulation design

The discrete-time engine resolves and validates YAML configuration before output creation. A local seeded random generator creates abstract flow counts/bytes and collection loss. Stable namespaced IDs and canonical JSON make equal input plus seed produce an equal `canonical_run_hash`.

## Pipeline

`truth generation -> observation channel/queue -> observable features -> detector/XAI -> clinical-safety policy -> requested/applied mitigation -> evidence/custody -> redaction/sharing -> evidence-only reconstruction -> graph/metrics/export`

Ground-truth events may contain `attack_truth`; observed events, alerts, evidence, share packages and reconstruction may not. Every downstream operational decision is computed from observations and declared configuration.

The baseline disables the attack. The nominal configuration uses one essential monitor with no approved backup, so an alert can request isolation while the safety service rejects it. The backup-active branch demonstrates eligible bounded isolation. The health-fault branch exercises fault/attack separation.

## Outputs

Each run writes resolved configuration, static model snapshots, restricted truth, observations, alerts, safety/policy decisions, mitigation actions, evidence and custody, a redacted share package, reconstruction, runtime graph, competency queries, metrics, validation, a narrative summary, SVG overview and run manifest.

## Interpretation

This is an abstract executable specification, not a clinical or network emulator. Synthetic detection results demonstrate invariants and branch behavior; they are not estimates of effectiveness in a real hospital.
