# UC5 dependency lock

`requirements.lock` pins the runtime and test dependencies. Reproduce in the repository `.venv`: install the lock, install UC5 with `--no-deps -e .`, run `pip check`, validation, all tests, and manifest verification. Review direct and transitive upgrades together and record Python/platform versions. UC5 is a per-UC package with compatible envelopes but no sibling imports.
