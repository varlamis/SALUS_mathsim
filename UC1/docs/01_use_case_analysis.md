# UC1 use-case analysis

The selected slice crosses four trust boundaries: vehicle internal to OBU, OBU to Car2X channel, Car2X channel to RSU, and roadside infrastructure to SALUS services. The primary protected asset is the bounded traffic-controller decision path; sensitive secondary assets are vehicle/location identity, certificate linkability, infrastructure state, and evidence.

The attacker can submit symbolic messages with configured credential, freshness, sequence, form, and rate properties. The attacker cannot read hidden simulation truth, bypass code, access secrets, transmit radio frames, or control a real device. Attack success is decomposed into transmitted, delivered, observed, validated, policy-passed, controller-accepted, and bounded-effect stages.

The DS1 CAN dataset is relevant to UC1 but represents an in-vehicle OBD-II injection context. It may later calibrate a separate internal-network branch; it cannot validate the nominal Car2X channel.

