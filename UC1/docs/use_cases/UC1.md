# UC1 — Car2X attack-surface identification and controlled penetration simulation

## Scenario summary

A synthetic police test vehicle and OBU exchange abstract authenticated messages with a roadside unit. A controlled adversarial transmitter submits forged, replayed, malformed, or excessive requests. Trust validation and an explainable detector provide inputs to an abstract policy service. The traffic controller remains behind a fail-safe interlock. Authorized observations are minimized, hashed, registered in custody, and reconstructed.

## Source and decision status

The vehicle, OBU-to-infrastructure communication, ITS-G5/C-V2X/mobile-service interface families, PKI concern, traffic-light attack family, and controlled penetration context come from `PROPOSAL-UC1-PP14-15`. The precise forged/replayed request and signal-controller linkage are agreed engineering choices (`AGREED-UC1-001`) needed for an executable vertical slice. Exact hardware, topology, message profile, certificates, timing, controller API, and pilot data remain assumptions or TBD.

## Operational environment

- Physical: controlled laboratory or test-road abstraction; no real coordinates.
- Cyber: OBU, RSU, controller, monitoring, trust, detection, policy, twin, evidence, and reconstruction roles.
- Network: abstract in-vehicle, Car2X, roadside-backhaul, and SALUS zones.
- Actors: pseudonymous vehicle operator, infrastructure operator, authorized red-team operator, and LEA analyst.
- Sensitive data: vehicle identity, operator identity, location, trust material, operational infrastructure state, and evidence metadata.

## Entry and exit criteria

The run begins only after configuration, schema, entity, graph, and safety validation. It ends after the last event, mitigation decision, evidence collection, integrity verification, reconstruction, and export. A run fails if an ID is unresolved, a safety invariant is false, hidden truth appears in an operational artifact, or an output escapes the UC1 output root.

## Acceptance criteria

- Baseline exchange produces no attack alert.
- The nominal forged request is observed, rejected, explained, and linked to evidence.
- No protected branch applies an unauthorized controller effect.
- Conflicting signal phases and live control are unreachable.
- Equal seed and configuration yield the same canonical hash.
- Negative trust, replay, overload, loss, and dependency branches have explicit outcomes.

## Non-claims

The scenario does not establish radio, ETSI, 3GPP, PKI, CAN, controller, AI, SDN, legal, safety, or pilot conformance.

