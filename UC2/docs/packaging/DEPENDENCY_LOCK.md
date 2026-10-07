# UC2 dependency lock

`requirements.lock` pins the package runtime and test stack. Reproduction uses the repository `.venv`, installs the lock, installs UC2 with `--no-deps -e .`, runs `pip check`, validation, tests and the manifest verifier. Direct and transitive upgrades must be reviewed together and recorded with Python/platform versions. The UC2 package imports no sibling UC package.
