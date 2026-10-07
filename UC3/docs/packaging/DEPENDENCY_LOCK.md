# Dependency lock

`requirements.lock` pins the validated Python dependency environment. Create a clean environment, install the lock, then install this package with `--no-deps -e .`. Run `pip check`, validation, tests, scenarios, and the final manifest. Caches, environments, egg metadata, and temporary files are excluded from manifests.
