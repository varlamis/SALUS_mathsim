# UC3 formal hybrid mathematical model

## State

The hybrid state is \(X(t)=(x_p,x_c,x_n,x_a,x_d,x_e)\): process, controller/device, network/queue, alert/policy, twin, and evidence/custody state. Exported causal times are separate from monotonic simulation time.

## Process and PLC

For vessel level \(h\), area \(A>0\), pump command \(u_p\), valve command \(u_v\), and disturbance \(w\):

\[
\dot h=(q_{in}(u_p)-q_{out}(u_v,h))/A+w, \qquad h_{min}\le h\le h_{max}.
\]

At scan \(k\), \(y_k=h(t_k)+b_k+v_k\). The PLC uses hysteretic synthetic control: pump on below target minus tolerance and valve open above target plus tolerance. Commands change only at scan boundaries. Attempted bound violations are counted before saturation.

## Network and attack

For arrivals \(A_k\), service \(S_k\), capacity \(Q_{max}\):

\[
Q_{k+1}=\min(Q_{max},\max(0,Q_k+A_k-S_k)).
\]

Delivered, channel-lost, overflow, observation-lost, validation-dropped, and policy-dropped messages are distinct. The attack automaton is `inactive → discovering → fuzzing → write_attempt → flooding → stopped`; its messages contain only abstract function classes and outcomes.

## Detection, policy, and safety

With observed feature rules \(r_i\), missingness \(m_i\), weights \(w_i\), and threshold \(\tau\):

\[
s_k=\sum_i w_i r_i(f_{i,k},m_{i,k}),\qquad a_k=\mathbf{1}[s_k\ge\tau].
\]

Each alert stores features, contributions, threshold, and missing inputs. Candidate mitigation minimizes security loss subject to capability, authorization, process safety, telemetry availability, duration, and rollback constraints. Requested, applied, and observed-effective action states are distinct.

Invariants are bounded level, valid actuator commands, scan-only controller updates, no unauthorized external actuation, no hidden-truth detector access, and no mitigation that suppresses required safety telemetry without a safe alternative.

## Evidence and reconstruction

Canonical evidence content has digest \(d_i=SHA256(C_i)\). Custody records link as \(H_j=SHA256(H_{j-1}\parallel C_j)\). This is an integrity model, not a production blockchain. Reconstruction is a function of verified observed evidence only; evaluation against hidden truth occurs afterward. Claims carry supporting items, alternatives, missing evidence, time uncertainty, and confidence limitations.
