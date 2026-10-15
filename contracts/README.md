# Contract source and scope

Expansion adds a second manifest profile: explicit `network.allow_hosts`,
`capabilities.network: true`, 15-second deadline, no workspace access. Missing
allowlists and inconsistent network declarations fail validation. Network tests
mock DNS, sockets, TLS and HTTP; the Go overlay loads those manifests without
contacting providers. Offline tools retain the original 3-second profile.

Dependency-bearing tools must include exact full-closure requirements,
`requirements.lock` with SHA-256 wheel hashes, and `dependencies.json` mapping
allowed import modules to pins. Tests never install anything: use a preprepared
per-tool `.venv`, or an interpreter already carrying the exact versions checked
by that tool's tests. The Go overlay validates these manifests without invoking
the install path. Its sandbox execution checks remain for stdlib-only tools.

Invokr revision: `3ffb0f91204d461706f79b7e448f51d5c4c9f24e`.
Repository: `https://github.com/antonikliment/invokr-pre-release`.

`plugin.schema.json` is an original, stricter schema for the fields used by
Hammer, derived from `tools/system/toolbox/spec.go` (`toolboxSpec`,
`ValidateSpecFields`, `applyLimits`, `applyNetwork`, `ValidateToolDir`), not a
claim that invokr ships this JSON Schema. It deliberately excludes unsupported
fields and permissions. Invokr's own argument validator is shallow: Hammer also
validates types, enum choices, numeric ranges, unknown keys and sizes in Python.

The schema only uses the subset implemented by `validate.check`; unknown schema
keywords fail. Parameter schemas are flat primitive properties. The dependency
policy is stricter than upstream: zero external packages. Thus every declared
dependency is pinned vacuously, and there are no artifact hashes to fabricate.

If external dependencies become necessary, follow
`docs/agents/adr/0005-python-toolbox-supply-chain.md`: exact direct registry pins,
complete wheel-only resolved graph, approved artifact hosts, release cooldown,
explicit approval, SHA-256 lock, verified wheel cache and offline hash-checked
installation. The runtime generates `requirements.lock`; requirement lines
with pip options/URLs/VCS/path references are not an alternative. Tests must
never trigger online installation. Change the validator policy and add offline
fixtures deliberately before introducing any dependency.

`run_invokr.py` uses an external Go test overlay because existing upstream
`browser_contract_test.go` hardcodes the browser path and the other tests create
their own fixtures. They have no option to point directly at an external kit.
The overlay uses the same package's actual loader, argument validator,
`pluginResult`, `parseDaemonResponse` and `Invoke` seam. It does not replace
existing tests. `make test` in invokr runs the upstream suite separately.

Runtime policy source: `tools/core/sandbox/sandbox_linux.go` (`BuildPlan`),
`tools/system/toolbox/toolbox.go` (`pluginEnv`, sandbox command construction),
`python_env.go`, `mode.go`, `daemon.go`, `extensions_test.go`, and
`browser_contract_test.go`. Toolbox environment and namespace boundaries remain
invokr's responsibility; they cannot be strengthened by ignored manifest keys.
