# UC1 task scope

UC1 supplies a source-aware, machine-readable and executable T4.3 model of a controlled Car2X security scenario. It models physical and digital entities, message and state transitions, trust checks, detection, policy response, evidence, and reconstruction. It provides contracts to T3.3, T3.4, T4.2, T4.4, T4.5 and WP6 but does not implement those production components.

The selected vertical slice is a forged or replayed abstract control-affecting request sent by a synthetic adversarial transmitter to an RSU associated with a simulated traffic-signal controller. The protected branch rejects the request and preserves evidence. No live interface exists.

Proposal-backed facts use `PROPOSAL-*`; the agreed vertical slice uses `AGREED-UC1-001`; executable fallbacks use `ASSUMPTION-UC1-*`. Missing pilot details do not block execution but remain visible and replaceable.

