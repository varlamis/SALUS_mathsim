# UC2 simulation architecture

The deterministic runtime uses separate seeded observation and classification
streams. A finite observation queue records overflow independently from coverage
or stochastic loss. Hidden class selects synthetic generation only; operational
classification exports its observable inputs, confidence and alternatives.

The output bundle contains resolved configuration, snapshots, observations,
hypotheses, classifications, registry decisions, alerts, policy/action records,
evidence, custody, evidence-only reconstruction, graph, competency queries,
metrics, validation and a canonical result hash.
