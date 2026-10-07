# Dependency lock

`requirements.lock` pins the same small Python stack used by the validated UC4 implementation. Create a clean environment, install the lock, install this package with `--no-deps -e .`, run `pip check`, then run all tests. Update direct and transitive versions together and record the Python/platform used. Do not hand-edit only one transitive dependency.

