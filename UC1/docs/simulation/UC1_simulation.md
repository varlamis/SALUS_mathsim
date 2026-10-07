# UC1 simulation architecture

The runtime uses immutable scheduled events, deterministic sequence ordering, separate seeded channel and observation streams, strict configuration, abstract trust predicates, inspectable detection features, capability-bounded policy response, safe controller decisions, minimized evidence, custody verification, and observable-only reconstruction.

Attack success is not a Boolean: generation, delivery, observation, validation, policy passage, controller acceptance, and bounded effect are separate. The initial implementation guarantees that untrusted, stale, malformed, or policy-dropped requests cannot affect the controller.

The same root, config, model files, and seed produce the same canonical hash. The run manifest stores that hash and marks the output synthetic.

