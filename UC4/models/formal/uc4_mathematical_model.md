# UC4 formal hybrid mathematical model

## 1. Model identity and scope

| Field | Value |
|---|---|
| Model ID | `UC4-HYBRID-MODEL-001` |
| Version | `1.0.0` |
| Use case | `UC4` |
| Scenario | Unauthorized entry followed by door-sensor tampering and lawful remote acquisition |
| Entity model | `models/instances/uc4_entities.json` version `1.0.0` |
| Relationship model | `models/relationships/uc4_relationships.csv` version `1.0.0` |
| Assumptions | `docs/assumptions/UC4_assumptions.md` |
| Configuration contract | `models/schemas/simulation_config.schema.json` |

This document is the normative mathematical specification for the UC4 simulator. Code may optimize its implementation, but observable behavior, state invariants, authorization decisions, evidence provenance, and reported metrics must remain equivalent to the definitions below.

The model is a **stochastic hybrid discrete-event system**:

- physical and logical states change at discrete event times;
- time, delays, buffer occupancy, traffic volume, power, and confidence measures are continuous-valued;
- seeded random variables represent imperfect sensing, loss, delay, jitter, and clock offset;
- deterministic policy rules govern authorization, minimization, evidence release, and custody.

It is not a packet-accurate network emulator, a calibrated model of a named device, a legal decision system, or a probabilistic attribution-of-guilt model.

## 2. Sets, identifiers, and notation

### 2.1 Core sets

Let:

\[
\begin{aligned}
\mathcal V &= \text{set of canonical UC4 entities},\\
\mathcal D &= \{D01,D02,D03,D04,D05,D06\},\\
\mathcal T &= \{DT01,DT02,DT03,DT04,DT05,DT06\},\\
\mathcal S &= \{S01,\ldots,S06\},\\
\mathcal A &= \{A01,\ldots,A06\},\\
\mathcal O &= \{DO01,\ldots,DO09\},\\
\mathcal Z &= \{NZ01,NZ02,NZ03\}.
\end{aligned}
\]

Identifiers in equations omit the constant `UC4-` prefix when no ambiguity is possible. Implementations and exports must always use complete canonical IDs.

The static entity and relationship graph is a directed attributed multigraph:

\[
G_0=(\mathcal V,\mathcal E_0).
\]

Runtime relations produce a temporal multigraph:

\[
G(t)=(\mathcal V\cup\mathcal V_r(t),\mathcal E_0\cup\mathcal E_r(t)),
\]

where runtime nodes and edges include concrete events, evidence items, policy decisions, custody actions, and reconstruction claims. Each edge is:

\[
e=(u,v,r,[t_s,t_e),a_e),
\]

with controlled relationship type \(r\), inclusive start \(t_s\), exclusive end \(t_e\), and attributes \(a_e\).

### 2.2 Time and indexes

- Simulation time: \(t\in\mathbb R_{\ge 0}\), measured in seconds.
- Event index: \(k\in\mathbb N_0\).
- Event execution times: \(0\le t_0\le t_1\le\cdots\le T\).
- A half-open interval is written \([a,b)\).
- \(\mathbf 1[P]\) is one when proposition \(P\) is true and zero otherwise.
- \(\bot\) represents absent/unknown data, never an inferred value.
- `clamp(x,a,b)=min(b,max(a,x))`.

### 2.3 Units

All exported numeric properties must state or inherit a unit. The canonical units are seconds, bytes, bits per second, watts, and dimensionless probability/ratio values in \([0,1]\). Simulation time is monotonic numeric time; external timestamps are derived UTC representations and do not determine event ordering.

## 3. Global hybrid state

Immediately before event \(k\), the complete system state is:

\[
\Sigma_k=(t_k,X_k,Q_k,R_k,A_k,C_k,O_k,H_k,M_k),
\]

where:

- \(X_k=\{x_i(t_k):i\in\mathcal V\}\) is entity state;
- \(Q_k\) is the future-event priority queue;
- \(R_k\) is retained source-record state;
- \(A_k\) is authorization and policy state;
- \(C_k\) is collected evidence state;
- \(O_k\) is the observable/investigator-visible state partition;
- \(H_k\) is custody-chain state;
- \(M_k\) accumulates metrics.

Given event \(q_k\), configuration \(\theta\), and seeded random innovation \(\xi_k\), the transition is:

\[
\Sigma_{k+1}=F(\Sigma_k,q_k;\theta,\xi_k).
\]

`F` is composed in this fixed order:

\[
F=F_{metrics}\circ F_{emit}\circ F_{effects}\circ F_{guard}\circ F_{dequeue}.
\]

Thus an event is dequeued, guards are evaluated, state effects are applied, resulting events/records are emitted, and metrics are updated. A failed guard emits an audit/failure event when required but does not apply the forbidden state effect.

## 4. Deterministic event queue and canonical event

### 4.1 Queue order

Every scheduled event has queue key:

\[
K(q)=(t_{scheduled},n),
\]

where \(n\) is a strictly increasing insertion sequence. Events are processed lexicographically by \(K\). Wall-clock time, hash-map iteration order, and thread timing must never break ties.

### 4.2 Canonical event tuple

The mathematical event is:

\[
q_k=(id,t_e,t_i,s,d,y,p,c,\pi,v),
\]

where:

| Symbol | Meaning |
|---|---|
| \(id\) | Stable event ID |
| \(t_e\) | Source event time |
| \(t_i\) | Ingest time |
| \(s\) | Source entity ID |
| \(d\) | Optional target entity ID |
| \(y\) | Controlled event type |
| \(p\) | Typed payload |
| \(c\) | Correlation IDs |
| \(\pi\) | Provenance: source record, sequence, clock domain, quality |
| \(v\) | Visibility class |

The serialization contract is `models/schemas/event.schema.json`.

The event-time causality invariant is:

\[
t_i\ge t_e-d_{clock,max},
\]

because a positive source-clock offset can make a reported event time appear later than ingest time. The simulator also retains true monotonic time internally for evaluation.

## 5. Clock and observation model

### 5.1 Local clocks

For source \(i\), reported local time is:

\[
\tau_i(t)=t+\delta_i+\epsilon_i(t),
\]

where:

\[
\delta_i\sim U(-\Delta_{clock},\Delta_{clock}),\qquad
\epsilon_i(t)\sim \operatorname{TruncNormal}(0,\sigma_t^2,-J_{max},J_{max}).
\]

One \(\delta_i\) is sampled per source per run. Jitter innovations are sampled per emitted event from a source-specific seeded stream. Defaults are \(\Delta_{clock}=2\,s\), \(\sigma_t=0.05\,s\), and \(J_{max}=0.20\,s\) (`ASSUMPTION-UC4-018`).

### 5.2 Observation and loss

For a ground-truth event \(g_j\) emitted by source \(i\), define:

\[
Z_j\sim Bernoulli(1-p_{loss,i}(\Sigma,t)).
\]

If \(Z_j=1\), an observable event is created after non-negative reporting/network delay \(D_j\). If \(Z_j=0\), the observable event does not exist; the ground-truth stream records the cause as a restricted evaluation marker.

The default independent base loss is:

\[
p_{loss,i}=0.005,
\]

before source, queue, outage, or scenario overrides (`ASSUMPTION-UC4-020`). Queue overflow loss is deterministic and applied in addition to the stochastic base loss.

### 5.3 Visibility partition

Let \(\mathcal G\) be hidden ground truth, \(\mathcal B\) retained source records, \(\mathcal C\) collected evidence, and \(\mathcal I\) investigator-visible data. The access relation must satisfy:

\[
\mathcal I\subseteq\mathcal C\subseteq\mathcal B,
\qquad
\mathcal G\not\subseteq\mathcal I,
\]

and reconstruction service `UC4-S05` may read only \(\mathcal I\), never \(\mathcal G\).

## 6. Entity state spaces

### 6.1 Smart-home environment `UC4-ENV01`

\[
x_{ENV}(t)=(o(t),a(t)),
\]

where occupancy \(o\in\{unoccupied,occupied\}\) and security context \(a\in\{armed,disarmed\}\). Initial state is `(unoccupied, armed)`.

### 6.2 CPE `UC4-D01`

\[
x_{CPE}(t)=(m,q,b,r,f,\ell,\alpha,h),
\]

where:

- \(m\in\{online,degraded,offline\}\);
- \(q\in[0,B_{max}]\) is byte-queue occupancy;
- \(b\in\mathbb N_0\) is retained record bytes;
- \(r\) is routing/interface state;
- \(f\) is the active-flow set;
- \(\ell\) is the bounded CPE record log;
- \(\alpha\in\{inactive,request\_received,authorized,collecting,completed,denied,expired,revoked,failed\}\);
- \(h\) is health state.

Initial state is `online`, \(q=0\), \(b=0\), \(f=\varnothing\), \(\ell=\varnothing\), and `acquisition=inactive`.

### 6.3 Home Assistant `UC4-D02`

\[
x_{HA}(t)=(m,\rho,\hat z,L,U,\delta_{HA}),
\]

where \(m\in\{online,degraded,offline\}\), \(\rho\) is the device registry, \(\hat z\) maps device IDs to last-known states, \(L\) is the bounded event log, \(U\) is the configured automation-rule set, and \(\delta_{HA}\) is its fixed run clock offset.

### 6.4 Door sensor `UC4-D03`

The door sensor state is:

\[
x_D(t)=(z_D,c_D,gamma_D,v_D,t_D^{last}),
\]

where:

- \(z_D\in\{closed,open,tampered\}\) is physical/logical sensor state;
- \(c_D\in\{online,offline\}\) is connectivity;
- \(\gamma_D\in\{0,1\}\) indicates tamper capability;
- \(v_D\in\mathbb N_0\) is state version;
- \(t_D^{last}\) is the last heartbeat/event time.

Initial state is `(closed, online, 1, 0, 0)` in the primary run.

Allowed guarded transitions are:

| Current state | Event | Guard | Next state | Emission |
|---|---|---|---|---|
| `closed/online` | `door.open` | physical entry | `open/online` | open event and heartbeat update |
| `open/online` | `door.close` | physical close | `closed/online` | close event |
| `closed/online` or `open/online` | `device.tamper` | \(\gamma_D=1\) | `tampered/online` | tamper event |
| any online state | `device.disconnect` | true | same logical state / `offline` | offline event if observable |
| `tampered/online` | `device.disconnect` | true | `tampered/offline` | offline event if observable |
| any offline state | `device.restore` | authorized maintenance | configured recovered state / `online` | recovery event |

Each accepted state transition increments \(v_D\) by one. A duplicate/debounced transition does not increment the version.

### 6.5 Presence sensor `UC4-D04`

\[
x_P(t)=(z_P,c_P,t_P^{last},t_P^{refractory},v_P),
\]

where \(z_P\in\{clear,motion\}\) and \(c_P\in\{online,offline\}\).

For true movement \(m(t)=1\) while online and outside the refractory interval:

\[
Y_P\mid m=1\sim Bernoulli(p_d),\qquad p_d=0.95.
\]

For no true movement:

\[
Y_P\mid m=0\sim Bernoulli(p_{fp}),\qquad p_{fp}=0.01
\]

per configured evaluation window. A detected event is reported after \(d_P=0.20\,s\) plus clock/network effects. After detection, no new motion event is emitted for refractory period \(r_P=2\,s\) (`ASSUMPTION-UC4-009`). A missed detection is recorded only in hidden truth/metrics.

### 6.6 Smart plug `UC4-D05`

\[
x_{SP}(t)=(u_{SP},c_{SP},w_{SP},s_{cmd},v_{SP}),
\]

where \(u_{SP}\in\{off,on\}\), \(c_{SP}\in\{online,offline\}\), \(w_{SP}\ge0\) watts or \(\bot\), and \(s_{cmd}\) is the last accepted command source.

A command is accepted only when online and the command source is permitted by scenario configuration. In the primary scenario \(u_{SP}=off\), optional power measurement is disabled, and no incident command is sent (`ASSUMPTION-UC4-011`).

### 6.7 Smart light `UC4-D06`

\[
x_L(t)=(u_L,c_L,\beta_L,s_{cmd},v_L),
\]

where \(u_L\in\{off,on\}\), \(c_L\in\{online,offline\}\), and optional brightness \(\beta_L\in[0,100]\cup\{\bot\}\).

For accepted command `light.on` at time \(t_c\):

\[
u_L(t_c+d_{ack})=on,
\qquad d_{ack}=0.15\,s.
\]

The state acknowledgment is subject to the observation model. Brightness remains \(\bot\) in the primary run.

### 6.8 Services and data objects

Service and data-object lifecycle states are the finite sets declared in `uc4_entities.json`. A transition is legal only if both current and next states appear in `allowed_states` and a transition rule in this model or its later process model permits the edge. Unknown states are schema errors, not dynamic fallbacks.

## 7. Home Assistant behavior and automation

### 7.1 Event ingestion

When Home Assistant receives device event \(q\) from device \(i\):

1. reject it if `D02` is offline;
2. classify it as stale if its version is not newer than the accepted version for \(i\);
3. update \(\hat z_i\) when accepted;
4. append a Home Assistant event to bounded log \(L\);
5. evaluate enabled automation rules;
6. emit resulting commands and correlation IDs.

### 7.2 Entry-light rule

Define:

\[
R_{light}(q,X)=
\mathbf 1[y(q)=door.open]
\mathbf 1[o=unoccupied]
\mathbf 1[a=armed]
\mathbf 1[U_{light}=enabled].
\]

If \(R_{light}=1\), Home Assistant schedules `light.on` after processing delay \(d_{HA}=0.10\,s\), with a correlation ID linking the door event, automation event, command, acknowledgment, and light state event.

The rule is deterministic given an observed door event. If the door event is lost before Home Assistant ingestion, the automation is not triggered unless another configured rule does so.

### 7.3 Bounded retention

Let \(N_L=10{,}000\) be the default maximum Home Assistant event count. Appending to a full log evicts the oldest record under FIFO retention and increments `records_overwritten`. Time-based retention also evicts records older than \(R_{HA}=1200\,s\) in the nominal run. The effective retained set is the intersection of count and time constraints.

## 8. Communication and CPE queue model

### 8.1 Flow abstraction

A communication flow is:

\[
f=(id,s,d,t_s,t_e,n_b,n_p,class,allowed,observed),
\]

where \(n_b\) and \(n_p\) are non-negative byte and packet counts. The simulator does not inspect payload by default.

### 8.2 Queue conservation

For update interval \(\Delta t_k=t_{k+1}-t_k\), arriving bytes \(A_k\), service capacity \(C_k\) bytes/s, and queue capacity \(B_{max}\):

\[
S_k=\min(q_k+A_k,C_k\Delta t_k),
\]

\[
D_k=\max(0,q_k+A_k-C_k\Delta t_k-B_{max}),
\]

\[
q_{k+1}=q_k+A_k-S_k-D_k.
\]

Therefore:

\[
0\le q_{k+1}\le B_{max}
\]

and the conservation identity is:

\[
q_{k+1}-q_k=A_k-S_k-D_k.
\]

Default values are \(8C=10{,}000{,}000\) bits/s and \(B_{max}=1{,}048{,}576\) bytes (`ASSUMPTION-UC4-019`).

### 8.3 Utilization, delay, and loss

Over measurement interval \(W\):

\[
U_W=\frac{\sum_{k\in W}S_k}{\sum_{k\in W}C_k\Delta t_k},
\qquad 0\le U_W\le1.
\]

Abstract queue delay for an arriving record of size \(b\) is:

\[
d_q=\frac{q+b}{C}+d_{base}+J_{net},
\]

where \(J_{net}\ge-d_{base}\) ensures non-negative total transport delay. A record affected by \(D_k>0\) is marked dropped and cannot appear in retained CPE evidence.

### 8.4 CPE record retention

The nominal CPE record store has byte capacity \(B_R=50\,MiB\) and time retention at least \(R_{CPE}=1200\,s\) (`ASSUMPTION-UC4-031`). Eviction is FIFO by ingest time. The simulator records evicted record IDs in restricted metrics so absence is distinguishable from non-generation.

## 9. Digital-twin synchronization

For physical device \(D_i\) with version \(v_i\), twin \(DT_i\) stores accepted version \(\hat v_i\), state \(\hat x_i\), and twin-update time \(t_i^{DT}\).

An update \((v,x,t_e)\) is accepted iff:

\[
accept_i=\mathbf 1[v>\hat v_i].
\]

If accepted:

\[
(\hat v_i,\hat x_i,t_i^{DT})\leftarrow(v,x,t_{ingest}).
\]

Otherwise twin state is unchanged and a stale-update decision is emitted.

Synchronization lag is:

\[
L_i=t_i^{DT}-t_e\ge0
\]

after correction to simulation time. With stale threshold \(L_{max}\), twin status is:

\[
status(DT_i)=
\begin{cases}
synchronized,&L_i\le L_{max},\\
stale,&L_i>L_{max},\\
unavailable,&\text{twin service unavailable}.
\end{cases}
\]

The three-way mapping invariant is:

\[
D_i.twin\_id=DT_i.id
\land DT_i.physical\_entity\_id=D_i.id
\land MIRRORED\_BY(D_i,DT_i).
\]

## 10. Incident and causal schedule

The primary configuration uses the following synthetic schedule (`ASSUMPTION-UC4-017`):

| Symbol | Default | Meaning |
|---|---:|---|
| \(T\) | 1800 s | Run horizon |
| \(t_w\) | 300 s | End of warm-up |
| \(t_{entry}\) | 600 s | Unauthorized door opening |
| \(t_{tamper}\) | 610 s | Door sensor tamper/disconnection |
| \(t_{case}\) | 900 s | Independent case trigger |
| \(t_{request}\) | 920 s | Acquisition request |

The causal chain is:

\[
A05.entry
\rightarrow D03.open
\rightarrow
\begin{cases}
D04.motion&\text{with probability }p_d,\\
\varnothing&\text{otherwise},
\end{cases}
\]

\[
D03.open_{observed\ by\ HA}\rightarrow HA.automation\rightarrow D06.on,
\]

\[
A05.tamper\rightarrow D03.tampered\rightarrow D03.offline.
\]

The case trigger occurs later and is not a causal authorization:

\[
DO06\not\Rightarrow authorization.active.
\]

It only enables request preparation.

## 11. Authorization and minimization model

### 11.1 Authorization state machine

Authorization state is:

\[
a\in\{absent,submitted,verified,active,denied,expired,revoked\}.
\]

Legal transitions are:

\[
absent\rightarrow submitted\rightarrow
\begin{cases}
verified\rightarrow active\rightarrow expired,\\
denied.
\end{cases}
\]

`active -> revoked` is allowed at any time before expiry. `denied`, `expired`, and `revoked` are terminal for that authorization version.

### 11.2 Authorization object

For authorization \(a\), define:

\[
a=(id,issuer,subject,case,purpose,E_a,Y_a,U_a,[v_f,v_t),[w_s,w_e),status,verify).
\]

- \(E_a\): allowed entity IDs;
- \(Y_a\): allowed data types;
- \(U_a\): allowed actions;
- \([v_f,v_t)\): authorization-valid interval;
- \([w_s,w_e)\): evidence event-time window.

The primary synthetic authorization uses \([900,1500)\) for validity and \([540,780)\) for evidence time (`ASSUMPTION-UC4-016`).

### 11.3 Eligibility predicate

For request \(r\), candidate source record \(j\), and evaluation time \(t\):

\[
\begin{aligned}
eligible(j,r,a,t)=&\;
\mathbf 1[a.status=active]\\
&\land\mathbf 1[a.verify=valid]\\
&\land\mathbf 1[t\in[v_f,v_t)]\\
&\land\mathbf 1[eventTime(j)\in[w_s,w_e)]\\
&\land\mathbf 1[entity(j)\in E_a]\\
&\land\mathbf 1[type(j)\in Y_a]\\
&\land\mathbf 1[action(r)\in U_a]\\
&\land\mathbf 1[purpose(r)=a.purpose]\\
&\land\mathbf 1[case(r)=a.case]\\
&\land\mathbf 1[minimize(j,a)=pass].
\end{aligned}
\]

Missing, unknown, or ambiguous operands evaluate to false. The policy decision is:

\[
decision(j)=
\begin{cases}
allow,&eligible=1\land no\ fields\ require\ removal,\\
minimize,&eligible=1\land permitted\ projection\ is\ nonempty,\\
deny,&otherwise.
\end{cases}
\]

### 11.4 Minimization

Let \(F_j\) be fields in candidate record \(j\) and \(F_a\) the permitted field set. Release projection is:

\[
P_a(j)=j|_{F_j\cap F_a}.
\]

If \(F_j\cap F_a=\varnothing\), decision is `deny`. Direct identifiers are transformed to run-scoped pseudonyms before release. Payload capture is always false in version `1.0.0`.

The no-disclosure invariant is:

\[
decision(j)=deny\Rightarrow bytesReleased(j)=0.
\]

## 12. Evidence and provenance model

### 12.1 Evidence construction

For eligible minimized record \(j' = P_a(j)\), canonical bytes are:

\[
b_j=JCS(j'),
\]

where `JCS` is RFC 8785 JSON Canonicalization Scheme. Content hash is:

\[
h_j=SHA256(b_j).
\]

Evidence item is:

\[
E_j=(id,source,records,auth,decision,method,[t_s,t_e],t_a,h_j,transforms,sensitivity,storage).
\]

It must conform to `evidence.schema.json`. Hashing occurs after authorized minimization for the released evidence object. If an original collected raw object is retained, it receives its own evidence ID/hash and stricter access class; derived/minimized evidence links to it through an explicit transformation.

### 12.2 Immutable derivation graph

Evidence transformations form a directed acyclic graph:

\[
E_{out}=T(E_{in,1},\ldots,E_{in,n}).
\]

No transformation overwrites an input. A cycle in `DERIVED_FROM` relations is invalid.

### 12.3 Custody hash chain

For custody action \(k\):

\[
H_0=SHA256(runID\Vert caseID\Vert schemaVersion),
\]

\[
H_k=SHA256(H_{k-1}\Vert evidenceHash_k\Vert action_k\Vert time_k\Vert actor_k).
\]

Each custody record stores both \(H_{k-1}\) and \(H_k\). Verification recomputes all content hashes and chain links in sequence order. Any mismatch sets status `verification_failed` and prevents an unqualified reconstruction claim from using the affected item.

This is a deterministic integrity abstraction, not a claim of production blockchain integration.

## 13. Reconstruction and uncertainty

### 13.1 Time normalization

For observed event \(j\) from source \(i\), corrected time estimate is:

\[
\hat t_j=\tau_j-\hat\delta_i.
\]

Let offset-estimation uncertainty be \(u_{\delta,i}\) and timestamp uncertainty be \(u_{\epsilon,j}\). The event interval is:

\[
I_j=[\hat t_j-u_j,\hat t_j+u_j],
\qquad
u_j=u_{\delta,i}+u_{\epsilon,j}+u_{transport,j}.
\]

Event \(i\) is certainly before event \(j\) only if:

\[
\sup I_i<\inf I_j.
\]

Overlapping intervals yield uncertain ordering and must not be forced into a unique sequence.

### 13.2 Claim definitions

The first implementation produces at most these primary claims:

- \(C_{entry}\): the monitored door opened during the incident window while the model context was armed/unoccupied;
- \(C_{presence}\): movement was observed inside after the door event;
- \(C_{automation}\): Home Assistant triggered the configured light automation;
- \(C_{tamper}\): the door sensor was tampered with or became unexpectedly offline;
- \(C_{sequence}\): available evidence is consistent with entry preceding sensor loss.

It must not produce claims about real identity, intent, guilt, legal admissibility, or actual-world occurrence.

### 13.3 Transparent support score

For claim \(c\), let \(J_c^+\) be supporting observations, \(J_c^-\) contradictory observations, and \(J_c^0\) expected but missing observations. Each observation has configured importance \(w_j\ge0\), source reliability \(r_j\in[0,1]\), integrity indicator \(g_j\in\{0,1\}\), and authorization/visibility indicator \(a_j\in\{0,1\}\).

Define:

\[
W_c=\sum_{j\in J_c^+\cup J_c^-\cup J_c^0}w_j,
\]

\[
S_c=
\begin{cases}
\displaystyle
clamp\left(
\frac{\sum_{j\in J_c^+}w_jr_jg_ja_j
-\sum_{j\in J_c^-}w_jr_jg_ja_j
-\lambda\sum_{j\in J_c^0}w_j}{W_c},0,1
\right),&W_c>0,\\
\bot,&W_c=0.
\end{cases}
\]

Default missing-evidence penalty is \(\lambda=0.25\). This is an explainable **support score**, not a calibrated probability.

Qualification labels are:

\[
label(S_c)=
\begin{cases}
unsupported,&S_c<0.25,\\
weak,&0.25\le S_c<0.50,\\
moderate,&0.50\le S_c<0.75,\\
strong,&S_c\ge0.75,\\
indeterminate,&S_c=\bot.
\end{cases}
\]

Weights and reliability values must be configuration/version controlled and reported with each claim. A claim also lists evidence IDs, time interval, contradictions, missing expected observations, and alternative explanations.

### 13.4 Alternative explanations

The reconstruction output must test consistency with at least:

1. authorized/benign entry plus device failure;
2. false-positive presence detection;
3. sensor battery or connectivity failure;
4. Home Assistant automation misconfiguration;
5. clock skew or delayed ingestion;
6. record eviction or queue loss.

An alternative is not eliminated unless a stated constraint conflicts with verified evidence.

## 14. Metrics

### 14.1 Evidence capture

Let \(R_G\) be relevant source artefacts generated and observable under the configured sensor/source model, \(R_C\subseteq R_G\) those preserved as evidence, and \(C\) all preserved items.

\[
captureRecall=\frac{|R_C|}{|R_G|},
\qquad
evidencePrecision=\frac{|R_C|}{|C|}.
\]

If a denominator is zero, the metric is `undefined`, never zero or one by convention.

### 14.2 Disclosure

\[
unauthorizedDisclosureCount=\sum_j\mathbf 1[decision(j)=deny\land bytesReleased(j)>0],
\]

\[
unauthorizedDisclosureBytes=\sum_{j:decision(j)=deny}bytesReleased(j).
\]

Both must be zero in all runs.

### 14.3 Latency

For collected item \(j\):

\[
collectionLatency_j=t_{acquired,j}-t_{request},
\]

and:

\[
investigationLatency=t_{report}-t_{case}.
\]

Report median, 95th percentile, maximum, and count; do not report a percentile for an empty set.

### 14.4 Reconstruction

With ground-truth evaluation events \(G_r\), matched reconstructed events \(R_m\), and all reconstructed events \(R\):

\[
reconstructionRecall=\frac{|R_m|}{|G_r|},
\qquad
reconstructionPrecision=\frac{|R_m|}{|R|}.
\]

Timestamp mean absolute error is:

\[
MAE_t=\frac{1}{|R_m|}\sum_{j\in R_m}|\hat t_j-t_j^{truth}|.
\]

Ground truth is used only by the metrics evaluator after reconstruction completes.

### 14.5 Twin and network metrics

\[
meanTwinLag=\frac{1}{N_u}\sum_{j=1}^{N_u}L_j,
\]

\[
staleFraction=\frac{\text{time twin is stale}}{T},
\qquad
queueLossRate=\frac{\sum_kD_k}{\sum_kA_k}.
\]

Report maximum queue occupancy, utilization distribution, record evictions, and loss by cause.

### 14.6 Assumption coverage

For model fields \(F\):

\[
coverage_s=\frac{|\{f\in F:status(f)=s\}|}{|F|},
\]

for statuses `proposal`, `roadmap`, `agreed_decision`, `assumed`, `proposed`, and `TBD`.

## 15. Initial conditions and executable defaults

| Component | Initial/default value | Unit/status | Assumption |
|---|---|---|---|
| Run horizon | 1800 | seconds; synthetic | `ASSUMPTION-UC4-017` |
| Warm-up end | 300 | seconds; synthetic | `ASSUMPTION-UC4-017` |
| Door entry | 600 | seconds; synthetic | `ASSUMPTION-UC4-017` |
| Door tamper/disconnect | 610 | seconds; synthetic | `ASSUMPTION-UC4-017` |
| Case trigger | 900 | seconds; synthetic | `ASSUMPTION-UC4-017` |
| Acquisition request | 920 | seconds; synthetic | `ASSUMPTION-UC4-017` |
| Authorization validity | `[900,1500)` | seconds; synthetic | `ASSUMPTION-UC4-016` |
| Evidence window | `[540,780)` | seconds; synthetic | `ASSUMPTION-UC4-016` |
| Presence detection | 0.95 | probability; synthetic | `ASSUMPTION-UC4-009` |
| Presence false positive | 0.01 | per evaluation window; synthetic | `ASSUMPTION-UC4-009` |
| Presence evaluation window | 1.0 | seconds; synthetic | `ASSUMPTION-UC4-009` |
| Presence report delay | 0.20 | seconds; synthetic | `ASSUMPTION-UC4-009` |
| Presence refractory period | 2.0 | seconds; synthetic | `ASSUMPTION-UC4-009` |
| HA automation delay | 0.10 | seconds; synthetic | `ASSUMPTION-UC4-010` |
| Light acknowledgment delay | 0.15 | seconds; synthetic | `ASSUMPTION-UC4-010` |
| Base observation loss | 0.005 | probability; synthetic | `ASSUMPTION-UC4-020` |
| Clock-offset bound | 2.0 | seconds; synthetic | `ASSUMPTION-UC4-018` |
| Timestamp jitter std. dev. | 0.05 | seconds; synthetic | `ASSUMPTION-UC4-018` |
| Timestamp jitter bound | 0.20 | seconds; synthetic | `ASSUMPTION-UC4-018` |
| CPE service capacity | 10,000,000 | bits/s; synthetic | `ASSUMPTION-UC4-019` |
| CPE traffic buffer | 1,048,576 | bytes; synthetic | `ASSUMPTION-UC4-019` |
| Network base delay | 0.01 | seconds; synthetic | `ASSUMPTION-UC4-019` |
| Network jitter bound | 0.005 | seconds; synthetic | `ASSUMPTION-UC4-019` |
| CPE record capacity | 52,428,800 | bytes; synthetic | `ASSUMPTION-UC4-031` |
| HA maximum events | 10,000 | events; synthetic | `ASSUMPTION-UC4-007` |
| Nominal source retention | 1200 | seconds; synthetic | `ASSUMPTION-UC4-031` |
| Twin stale threshold | 5.0 | seconds; engineering default | `ASSUMPTION-UC4-022` |
| Missing-evidence penalty | 0.25 | dimensionless; engineering default | `ASSUMPTION-UC4-033` |
| Support weights | door open 1.0; presence 0.6; light command 0.5; light state 0.5; CPE flow 0.4; tamper 0.9; offline 0.8; heartbeat cessation 0.5 | non-negative; engineering defaults | `ASSUMPTION-UC4-033` |
| Source reliability | D01 0.80; D02 0.90; D03 0.95; D04 0.80; D06 0.90; S03 1.00 | ratio; engineering defaults | `ASSUMPTION-UC4-033` |
| Cloud adapter | disabled | boolean | `ASSUMPTION-UC4-012` |
| SDN mitigation | disabled | boolean | `ASSUMPTION-UC4-027` |
| Payload capture | disabled | invariant | `ASSUMPTION-UC4-015`, `ASSUMPTION-UC4-019` |

These values belong in versioned configuration. They must not be duplicated as unexplained constants in code.

## 16. Safety, consistency, and correctness invariants

The simulator must check the following during or immediately after every run:

### 16.1 Structural invariants

1. All entity/event/relationship/evidence/custody IDs are unique.
2. All references resolve.
3. Every enabled physical device has exactly one reciprocal twin mapping.
4. Every non-root entity belongs to UC4.
5. Runtime relation types belong to the controlled vocabulary.

### 16.2 Dynamic invariants

1. Simulation time and dequeue keys are monotonic.
2. Entity state always belongs to its declared state space.
3. Device version increments only on accepted state transitions.
4. Power and queue quantities remain non-negative and bounded.
5. Queue conservation holds within floating-point tolerance.
6. Offline devices do not emit ordinary state/heartbeat events unless the event represents transition to offline or restoration.
7. Stale twin updates cannot alter twin state.

### 16.3 Authorization and privacy invariants

1. Case trigger does not imply authorization.
2. Authentication does not imply authorization.
3. Missing/unknown/invalid inputs default to deny.
4. Denial releases zero protected bytes.
5. Released fields are a subset of authorized minimized fields.
6. Payload capture remains disabled in schema/model version `1.0.0`.
7. All generated identities are synthetic/pseudonymous.

### 16.4 Evidence invariants

1. Evidence has source, authorization, policy decision, collector, hash, and storage references.
2. Canonical content recomputes to the stored hash.
3. Custody links recompute from \(H_0\) through \(H_n\).
4. Raw evidence is never overwritten.
5. Evidence derivation is acyclic.
6. Failed integrity/custody prevents unqualified claim use.
7. Reconstruction has no dependency path to hidden ground truth.

## 17. Required experiments

### 17.1 Nominal experiment

Run the accepted schedule and valid authorization with the documented seed. Expected properties:

- hidden truth contains entry and tampering;
- observable evidence is subject to seeded uncertainty;
- valid in-scope records are collected and minimized;
- hashes and custody verify;
- reconstruction emits qualified claims with evidence IDs and alternatives;
- unauthorized disclosure is zero.

### 17.2 Baseline experiment

Run the same duration without unauthorized entry/tampering. Normal resident/device activity may be generated using the same source models. The detector must not assume the primary incident occurred.

### 17.3 Negative/degraded experiments

At minimum vary one factor at a time:

1. authorization absent;
2. authorization invalid;
3. authorization expired/revoked;
4. requested entity/type/time outside scope;
5. presence event missed;
6. door event lost before Home Assistant;
7. CPE/HA record evicted;
8. CPE queue overflow;
9. source clock skew causing ambiguous ordering;
10. evidence bytes modified;
11. custody link modified;
12. Home Assistant or CPE unavailable.

Every negative authorization run must satisfy zero evidence disclosure. Corruption runs must fail verification deterministically.

## 18. Equation-to-code and equation-to-test traceability

| Formal element | Planned implementation | Required test |
|---|---|---|
| Global transition \(F\) | `uc4/simulation.py` | End-to-end state/output test |
| Queue key \((t,n)\) | `uc4/event_queue.py` | Monotonic order and deterministic tie test |
| Canonical event tuple | `uc4/entities.py` or shared runtime models | Event schema round-trip test |
| Clock/observation equations | `uc4/dynamics.py` | Seeded loss/jitter/bound tests |
| Door FSM | `uc4/entities.py`, `uc4/dynamics.py` | Legal/illegal/debounce transition tests |
| Presence Bernoulli model | `uc4/dynamics.py` | Boundary probabilities and seed reproducibility |
| HA rule \(R_{light}\) | `uc4/dynamics.py` | Guard and causal correlation tests |
| CPE conservation | `uc4/traffic.py` | Conservation/capacity/overflow tests |
| Twin acceptance | `uc4/entities.py` | Newer accepted; equal/older rejected |
| Eligibility predicate | `uc4/authorization.py` | Scope/time/purpose/status/default-deny matrix |
| Minimization projection | `uc4/authorization.py` | Field-subset and zero-disclosure tests |
| Evidence hash | `uc4/collection.py` | Canonicalization and corruption test |
| Custody chain | `uc4/custody.py` | Valid chain and broken-link test |
| Time intervals/order | `uc4/reconstruction.py` | Certain versus ambiguous ordering test |
| Support score | `uc4/reconstruction.py` | Positive/negative/missing/undefined cases |
| Metrics | `uc4/metrics.py` | Hand-calculated fixtures and zero denominator |

## 19. Model limitations

1. Synthetic parameters are not calibrated measurements of a real UC4 deployment.
2. Abstract flow/queue dynamics cannot support packet-level performance or protocol-security claims.
3. The presence and loss models use simplified independent draws unless a later profile introduces dependence.
4. The support score is explainable but is not a calibrated posterior probability.
5. Hash-chain integrity is not production ledger deployment.
6. Authorization semantics exercise technical controls but do not encode or determine actual law.
7. Successful simulation does not prove legal admissibility, GDPR compliance, real-device fidelity, production readiness, or pilot KPI attainment.

## 20. Formal model completion criteria

This mathematical model is ready for implementation when:

- every symbol maps to a canonical entity, configuration field, runtime object, or explicitly local variable;
- initial values and units are specified or marked configurable;
- every stochastic operation uses an injected seeded random stream;
- all state transitions and guards are implementable without consulting hidden prose assumptions;
- authorization and evidence rules are deterministic and default-deny;
- all invariants have a planned automated test;
- reconstruction separates observations, claims, uncertainty, alternatives, and ground truth;
- later real-device adapters can replace abstract interfaces without changing core semantics.

Version `1.0.0` meets these criteria and is the normative input to process modelling and simulator implementation.
