# UC2 process model

The process chain is `passive observation -> pseudonymization -> bounded collection -> association -> probabilistic classification -> approval lookup -> explainable alert -> bounded review -> evidence/custody -> evidence-only reconstruction/consultation`.

Six BPMN process files and one lifecycle file are authoritative. They identify producer/consumer responsibility and cover normal observation, association/classification, alert/response, evidence/investigation, expert consultation and system collaboration. Failure defaults are explicit: observation loss remains missing; queue overflow is counted; insufficient association remains ambiguous; unavailable/stale registry becomes unknown; low confidence suppresses certainty; policy failure prevents response; and evidence verification failure prevents a supported claim.

Process invariants are: no active RF operation; no payload capture; no person/subscriber identity; alerts use observable information only; requested and applied actions remain distinct; evidence is allow-listed, hashed and custody-linked; and reconstruction does not consume hidden truth.
