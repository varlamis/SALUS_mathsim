# UC5 mathematical model

Let devices be (D), zones (Z), discrete times (t=0,\ldots,T), and the active monitor (m\in D). Device availability is (x_i(t)\in\{0,1\}), abstract health is (h_i(t)\in\{normal,fault,missing\}), essentiality is (r_i\in\{0,1\}), and approved backup availability is (b_i(t)\in\{0,1\}).

## Flow and observation model

Normal connection count and bytes are seeded bounded variables

\[
N_{i,t}=\max(0,\lfloor \mu_i+\sigma_i\epsilon_t\rceil),\qquad
B_{i,t}=\max(0,\lfloor \beta_i+\tau_i\eta_t\rceil).
\]

The symbolic attack state (a_i(t)\in\{inactive,anomalous\_egress,persistence,contained\}) changes destination class and multiplies rate/bytes; it has no executable payload. Collection indicator (o_{i,t}\sim Bernoulli(1-p_{loss})), delay (d_{i,t}\), and capacity (K) yield an observed set (O_t). Conservation requires generated = delivered + lost + overflow.

## Detection and explanation

From observations only,

\[
z_t=(z_N,z_B,z_{dest},z_h,z_{miss},r_m),\qquad
s_t=\sum_k w_k z_{k,t},\qquad A_t=\mathbf{1}[s_t\ge\theta].
\]

The explanation exports each (w_kz_{k,t}), threshold, alternatives and missingness. Attack truth is unavailable to this function.

## Continuity-constrained response

For candidate isolation (u_t=1), authorization (q_t), enforcement availability (e_t), and approved backup (b_m(t)), eligibility is

\[
u_t \le q_t e_t\,[1-r_m(1-b_m(t))].
\]

The selected action minimizes residual cyber risk, operational cost and review delay subject to this hard constraint. The essential-monitoring interruption metric is

\[
I=\sum_t \mathbf{1}[r_m=1\land x_m(t)=0\land b_m(t)=0],
\]

and every accepted experiment must satisfy (I=0).

## Evidence, custody and sharing

For canonical observable record (y_j), evidence digest is (H_j=SHA256(canon(y_j))). Custody event (c_j) includes the previous custody digest, producing a tamper-evident chain. Share eligibility is

\[
S=authorized\land redacted\land evidenceValid\land custodyValid.
\]

The share projection is an allow-list of evidence IDs/hashes, time window, pseudonymous device class and authorized metadata. Patient identifiers and clinical payload have cardinality zero. Reconstruction (R(E)) consumes verified evidence (E) only; restricted truth is used solely to evaluate (R).

## Open calibration parameters

The distributions, feature weights, threshold, essentiality, backup approval, response cost, review delay, retention, sharing authorization and KPI baselines require UC-expert agreement and validation data.
