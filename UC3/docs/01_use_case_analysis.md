# UC3 use-case analysis

UC3 combines four causal planes: process physics; controller/actuator logic; monitored industrial communications; and SALUS detection, mitigation, twin, and forensics. Normal level observations drive a scan-cycle controller. Attack messages cross the supervisory/control boundary but must pass parsing, function support, authorization, policy, and interlock gates before any process consequence.

The nominal branch deliberately stops at protected cyber state: unauthorized traffic is observed, explained, and isolated while the vessel remains bounded. Fault and observation-loss branches prevent the model from assuming that every anomaly is malicious. Supply-chain assessment is a separate pre-deployment twin branch.
