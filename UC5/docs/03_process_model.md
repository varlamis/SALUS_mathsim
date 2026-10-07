# UC5 process model

The end-to-end chain is `synthetic flow/health truth -> lossy bounded observation -> feature extraction -> explainable alert -> clinical-safety review -> requested/applied response -> evidence/custody -> redaction/authorization -> sharing -> evidence-only reconstruction`.

Seven process BPMN files and one lifecycle BPMN are authoritative. They cover normal monitoring, compromise detection, clinical-safety response, evidence sharing, investigation/reconstruction, failure recovery and collaboration. Unavailable collectors produce missingness; stale context reduces confidence; policy/enforcement uncertainty prevents isolation; no approved backup rejects isolation for an essential monitor; hash/custody/redaction/authority failures deny sharing.

Hard invariants are zero essential-monitoring interruption, zero clinical actuation, zero patient/clinical content, no hidden truth in operational/investigator views, explicit requested-versus-applied action, and default-deny evidence sharing.
