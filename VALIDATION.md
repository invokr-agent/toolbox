# Validation record

Date: 2026-10-15. Python 3.14.7. Invokr contract:
`3ffb0f91204d461706f79b7e448f51d5c4c9f24e`. Go toolchain: `go1.26.3`.

| Check | Result |
| --- | --- |
| Standalone `GOTOOLCHAIN=go1.26.3 make test` | PASS: nine isolated tool suites, template suite, validator mutation tests |
| Standalone `GOTOOLCHAIN=go1.26.3 make lint-ci` | PASS: manifest/dependency/import contract and Python syntax checks |
| `contracts/run_invokr.py /tmp/hammer-invokr-contract-3ffb0f9` | PASS: all nine actual manifests/examples, both Go result decoders, actual sandboxed invocations |
| `TestHammerSiblingContainment` | PASS: sibling/host read denial, source/sibling write denial, env isolation, private scratch, distinct network namespace |
| Invokr snapshot `GOTOOLCHAIN=go1.26.3 GOMAXPROCS=2 make test` | PASS: complete default Go test suite |
| Invokr snapshot `GOTOOLCHAIN=go1.26.3 GOMAXPROCS=2 make lint-ci` | PASS: custom linter, 0 issues |
| Official Hermes source comparison | PASS: six inspected source files match installed revision by SHA-256 |

Python tests include malformed envelopes, required/unknown fields, types, error
recovery, input bounds, Unicode output overflow, regex timeout, ZIP metadata
traversal/symlinks, ambiguous text replacement, quoted CSV, arithmetic syntax
limits and explicit date offsets. Validator mutation tests reject permission
drift, invalid schemas/examples, dependencies, cross-tool imports, symlinks and
missing/empty tests. No network installation occurs in these checks.

Invokr runs used a disposable `git archive` snapshot, not the user's checkout.
The external tests use Go's file overlay; no invokr source is changed. The kit
has no remote, push or PR. The model server at 127.0.0.1:8080, benchmark lock and
the two protected live-run cache directories were not used or modified.

Limits: namespace support is required; direct Python tests alone do not prove
containment. Baseline Go lint applies to invokr; kit Python lint is intentionally
a stdlib syntax/contract gate, not a third-party style checker. Invokr has no
manifest-level scratch-path field or complete malicious-process cgroup quotas;
the README states those upstream boundaries rather than claiming stronger
isolation than was exercised.
