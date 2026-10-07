# UC5 final handoff

## Delivered vertical slice

UC5 implements deterministic synthetic patient-monitor flow/health generation, lossy bounded observation, explainable anomaly detection, clinical-continuity-constrained response, minimized evidence/custody, default-deny redacted sharing, evidence-only reconstruction, graph queries and uncertainty analysis. It has no medical, clinical or production-network interface.

## Reproduced results

- Baseline canonical hash: `568e0bd53207a02537370567b7f41acf56f0d9ee05247628cace16fb39d216a5`.
- Nominal compromised-monitor canonical hash: `a68d437a709b1df8af086849bc1f6996e3f2addb59edc56de52f2028cd2862b3`.
- Nominal metrics: 80 flow truths/observations, 1 alert, 1 safety rejection, 0 applied effects, 0 essential-monitoring interruptions, 84 verified/shared minimized evidence items, 0 safety/privacy/patient-disclosure/integrity violations.
- The backup-active experiment permits one bounded isolation while preserving zero essential-monitoring interruption.
- All 9 experiment branches pass continuity and privacy invariants; unauthorized sharing exports zero evidence IDs.
- The 100-sample uncertainty run reports zero essential interruptions, patient disclosures, privacy violations and safety violations.
- 13 automated tests pass, including schema validation of the retained event and evidence fixtures.

## Expert-owned open parameters

Hospital topology/device inventory; abstract flow baselines; clinical essentiality and approved-backup rules; detector calibration; mitigation and sharing authority; review/enforcement/sharing delay; retention/purpose; DS8 licensing/mapping; participant interfaces; and WP6 KPI baselines remain TBD.

## Reproduce and verify

Use the commands in `README.md`. Verify `reports/final/UC5_artifact_manifest.json` with the CLI after any change. Regenerate it only after reviewed changes because it hashes the complete package.

## Claims boundary

The deliverable is a synthetic executable specification. It does not establish medical-device safety, diagnostic or treatment capability, hospital/network fidelity, GDPR or regulatory compliance, production readiness or proposal KPI attainment.
