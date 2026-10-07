# UC1 formal hybrid model

## State and transition system

At simulation time \(t\),

\[
X(t)=(V(t),O(t),R(t),S(t),K(t),N(t),D(t),P(t),E(t),C(t)),
\]

where the components represent vehicle/OBU, RSU, channel, signal controller, trust, queue/network, detector, policy, evidence, and custody/reconstruction state. Given event \(e_k\), configuration \(\theta\), and component-specific seeded random input \(\xi_k\):

\[
(X,Q)_{k+1}=F((X,Q)_k,e_k,\theta,\xi_k).
\]

The future-event queue is ordered by `(simulation_time, deterministic_sequence)`. Wall-clock time never changes ordering.

## Message and time semantics

An abstract message is

\[
m=(id,t_s,t_r,src,dst,class,seq,credential,permissions,payloadHash,size,provenance).
\]

Sender, receiver, ingest, detection, decision, enforcement, collection, and custody times remain distinct. Export timestamps may be UTC; dynamics use non-negative seconds.

## Validation

\[
accept(m,t)=parse(m)\land available(K,t)\land credential(m,t)\land authorized(src,m)\land fresh(m,t)\land sequenceOK(m)\land plausible(m,X(t))\land policyAllows(m,t).
\]

Each predicate is auditable. Unknown/unavailable predicates fail closed. This is abstract validation, not cryptographic verification.

## Channel and finite queue

For arriving messages \(A_k\), service capacity \(C_k\), step \(\Delta t\), and buffer \(B_{max}\):

\[
B_{k+1}=\min(B_{max},\max(0,B_k+A_k-C_k\Delta t)).
\]

Every message is classified as delivered, channel-lost, overflowed, validation-dropped, or policy-dropped. Delay equals non-negative base delay plus bounded seeded jitter. This is not a PHY/MAC simulator.

## Detection

\[
z=w_a f_{auth}+w_f f_{freshness}+w_s f_{sequence}+w_r f_{rate}+w_p f_{plausibility},\qquad alert=[z\ge\tau].
\]

Weights are non-negative and sum to one. The exported explanation lists each non-zero feature. Missing observation means the operational detector cannot use the event; truth remains evaluation-only.

## Policy and controller safety

\[
a=\pi(alert,entity,trust,capabilities,policyVersion,t).
\]

Requested and applied actions are distinct. Only declared capabilities are valid. The traffic controller phase lies in `{safe_all_red,north_south,east_west}`; conflicting phases are unreachable, and the implementation exposes no live control adapter. An invalid message cannot cause a controller effect.

## Evidence and custody

Evidence collection uses an event-type and field allowlist. Content is hashed over canonical sorted JSON. For custody event \(k\):

\[
H_k=SHA256(H_{k-1}\Vert artifactHash_k\Vert action_k\Vert time_k\Vert actor_k).
\]

Hash or chain mismatch quarantines the affected record. The construction is an integrity model, not a production blockchain.

## Reconstruction and metrics

Reconstruction consumes only observed, authorized evidence. Claims carry supporting evidence IDs, confidence, and alternatives. Metrics preserve undefined denominators as null and include attack observation/detection, controller effects, safety violations, disclosure, evidence capture, integrity, and attributed loss.

## Invariants

1. Simulation and ingest time are non-negative.
2. Equal configuration and seed produce equal canonical content.
3. Hidden truth is absent from graph, queries, evidence, and investigator summary.
4. Safety violation and live-control counts are always zero.
5. Invalid/untrusted/stale/malformed requests cannot cause controller effects.
6. Evidence fields are a subset of the configured allowlist.
7. All relationship endpoints and twin mappings resolve.

## Calibration status

All numerical values are `synthetic_default`. DS1 is not used in the nominal model. The experiment and Monte Carlo designs vary declared uncertainty without representing real-pilot performance.

