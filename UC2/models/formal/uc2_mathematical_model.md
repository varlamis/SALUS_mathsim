# UC2 formal observation, association and classification model

For device (i), interface (j) and emission (t), observation is

\[
O_{ijt}\sim Bernoulli(c_{ij}(1-p_{loss,j})),\qquad y_{ijt}=g(d_i,j)+\epsilon_{ijt}.
\]

The bounded queue obeys (B_{k+1}=B_k+A_k-S_k-D_k), with
(0\le B_{k+1}\le B_{max}). Observations may join hypothesis (h) only when
their pseudonyms/interfaces are compatible and their timestamps differ by no
more than association window (W). Classification exports
(P(C=k\mid y_h)), top class, confidence and alternatives without exporting
hidden class.

Registry state is one of approved, unapproved, unknown or stale. An alert is
eligible only for unapproved state and confidence at least threshold \(\tau\).
Policy maps an alert to observe, request-review, pause-simulated-event or
quarantine-hypothesis; all are abstract and active RF action is invariantly
false. Evidence content (b_i) has digest (h_i=SHA256(JCS(b_i))), and custody
record (H_i=SHA256(H_{i-1}\Vert h_i\Vert action_i)). Reconstruction consumes
verified evidence only.
