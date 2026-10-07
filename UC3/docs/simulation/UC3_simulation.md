# UC3 deterministic simulation

The simulator uses independent seeded process, channel, and observation streams. A one-vessel balance evolves at one-second scans; process observations are emitted every five seconds. Attack messages are scheduled from configuration and validated without constructing protocol payloads. Equal code, inputs, and seed yield the same canonical result hash.

The detector sees observations only. Evidence collects allowlisted fields. Reconstruction reads evidence only. Output paths are constrained beneath `reports/generated/uc3`. No network sockets or industrial-control adapters exist.
