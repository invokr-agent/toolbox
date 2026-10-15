# Hammer — Python toolbox extension kit for invokr

Nine small, independent tools for local models. Each directory under `tools/`
is a complete invokr plugin: manifest, Python entrypoint, dependency declaration,
offline tests and README. Python 3.11+ on Linux; standard library only.

## Catalog and permissions

| Tool | One-line specification | Required arguments | Network / workspace / persistent writes |
| --- | --- | --- | --- |
| `hammer_json_query` | Select a JSON value by RFC 6901 pointer or list object keys. | `text` | none / none / none |
| `hammer_csv_query` | Filter CSV rows by an exact column value and return bounded JSON rows. | `text` | none / none / none |
| `hammer_text_patch` | Replace one exact match in supplied text and return text plus diff preview. | `text`, `old`, `new` | none / none / none |
| `hammer_regex_search` | Search supplied text/code with regex, offsets and line numbers. | `text`, `pattern` | none / none / none |
| `hammer_zip_inspect` | Inspect base64 ZIP metadata and flag suspicious paths without extraction. | `base64` | none / none / none |
| `hammer_calculate` | Evaluate bounded arithmetic without arbitrary code execution. | `expression` | none / none / none |
| `hammer_units` | Convert fixed length, mass, duration and temperature units. | `value`, `from_unit`, `to_unit` | none / none / none |
| `hammer_datetime` | Shift an explicit-offset ISO timestamp and convert its UTC offset. | `timestamp` | none / none / none |
| `hammer_html_extract` | Convert supplied HTML to readable text and HTTP(S) links. | `html` | none / none / none |

All declare `executes_code: true` because Python runs, `daemon: false`, approval
`ask`, and tier `code_execution`. This is distinct from accepting arbitrary user
code. No tool spawns a subprocess. Data arrives as arguments, never host paths.

Each request is at most 64 KiB; encoded response at most 30 KB (under invokr's
32 KiB cap); Python alarm 2 seconds; invokr timeout 3 seconds and memory 128 MiB.
Results use `{"result":"<JSON containing a data object>"}`; failures use
`{"error":"invalid_request: explanation"}`. JSON remains parseable on overflow.
Optional parameters have defaults in each manifest; all unknown arguments fail.

## Install and enable

Validate before installing:

```sh
make test
make lint-ci
```

Copy selected complete directories into invokr's toolbox root. For example,
from this repository, with a destination that does not already exist:

```sh
mkdir -p ~/.invokr/toolbox
cp -R tools/hammer_json_query ~/.invokr/toolbox/hammer_json_query
```

Check the destination first; do not accidentally nest or overwrite an existing
installation. Install other tools the same way. Alternatively, set
`INVOKR_TOOLBOX_DIR=/absolute/path/to/toolbox/tools` to load this kit directly;
that selects this root instead of your existing toolbox root. Restart invokr,
or use its toolbox discovery refresh through `tool_search`. The namespace is
`hammer`; call names are the full `hammer_*` names in the table. Per-call approval
still applies. Remove an installed tool directory and restart to disable it.

Required operator settings:

- Keep `toolbox.isolate_env: true` and an empty `toolbox.env` map.
- Keep `toolbox.allow_unsandboxed: false`; do not enable
  `INVOKR_TOOLBOX_ALLOW_UNSANDBOXED`, YOLO mode, or a whole-agent container setup
  that bypasses individual toolbox namespaces.
- Leave `toolbox.venv_dir` unset. No shared venv, state directory, cache override
  or credential passthrough. Use the normal system Python interpreter, outside
  any tool directory.

Invokr may ask to prepare the individual `.venv` on first use. The comment-only
`requirements.txt` parses as zero dependencies, so its current preparation code
creates a venv without package resolution, downloads or pip installs. Runtime
and tests do not require network. Do not manually add hash options to
`requirements.txt`: invokr expects exact direct pins and generates the resolved
hash lock itself (see [contract](contracts/README.md)).

## Isolation model and limits

Invokr's Linux user/mount/PID/network namespaces enforce the boundary. Each
invocation sees its own tool directory and venv read-only, the runtime mounts,
and a private ephemeral `/tmp`. No workspace mount is requested. Sibling tools
and their environments are outside that namespace's mounted filesystem. Failed
calls terminate their own one-shot process; there is no shared daemon or state.
No runtime imports come from another tool or from kit-level code.

Scratch policy: **none required or used**. At invokr `3ffb0f9`, `plugin.json`
has no custom scratch-path declaration. We do not invent an ignored permission
field or grant workspace writes to simulate one. The sandbox supplies writable
private `/tmp` even to a read-only plugin; this is ephemeral namespace-local
storage, not permission to write any host directory. A stricter policy allowing
only a manifest-named scratch path requires an invokr runtime change and cannot
be enforced by this standalone kit alone.

Containment assumes a working, patched Linux kernel, namespace support, and the
settings above. Resource caps bound these tools' computations; they do not claim
complete host availability isolation against arbitrary malicious native code
(for example, invokr does not provide per-plugin cgroup CPU/PID quotas here).
Running `python3 main.py` directly is for trusted tests, not sandboxed execution.
The validator checks contracts and obvious import drift, not arbitrary-code
security. Review additions before installation.

## Add a tool

1. Copy `template/` to `tools/hammer_<name>/`.
2. Rename the manifest tool, example and description; define at most three
   required primitive arguments with short descriptions. Update README.
3. Replace `run(args)`; keep validation, time and output bounds. Add useful
   success, malformed-input and adversarial tests in `test_main.py`.
4. Keep `requirements.txt` stdlib-only and permissions minimal. Network,
   workspace access or dependencies need a deliberate contract-policy change.
5. Run `make test`, `make lint-ci`, and the invokr contract check below.
6. Commit the entire directory once as `tool(<name>): <one-line purpose>`.
   Amend/fixup subsequent corrections into that commit. Tools never import each
   other, so their commits remain independently revertible/cherry-pickable.

The template is copied, never imported. `validate.py` discovers directories,
checks the vendored strict manifest schema, permission values, exact dependency
policy, examples, required files and imports, then runs each tool's tests in a
fresh interpreter with a minimal environment. It also validates/tests the
template. No network installs or external services occur during these tests.

## Invokr compatibility checks

The target contract is invokr commit
`3ffb0f91204d461706f79b7e448f51d5c4c9f24e`. Use a disposable source snapshot:

```sh
GOTOOLCHAIN=go1.26.3 make contract INVOKR_SOURCE=/path/to/invokr-snapshot
```

The runner adds an external test using Go's `-overlay`, without modifying invokr
source. It loads each actual manifest, validates its example, passes Python
output through invokr's one-shot and daemon decoders, and invokes every example
inside the real namespace sandbox. Dependencies stay empty. Venvs are created
only in Go test temporary directories. A separate adversarial probe checks
sibling/host access denial, read-only source, isolated environment, private
scratch and a distinct network namespace. Unavailable sandbox support fails
this gate rather than silently testing an unsandboxed fallback.

Run invokr's `GOTOOLCHAIN=go1.26.3 make test` and `make lint-ci` in that disposable
snapshot too. These are baseline compatibility checks; the standalone kit adds
no invokr implementation Go code. See [VALIDATION.md](VALIDATION.md) for recorded
results and [SOURCES.md](SOURCES.md) for inspected Hermes/invokr sources.

## Evaluated and omitted

Web fetch/search and HTTP API clients need network authority. Invokr's hostname
allowlist restricts resolution but does not block literal-IP egress. This kit
keeps network off and provides offline HTML extraction instead. Native invokr
tools cover web access when approved. YAML would add a parser dependency; JSON
and CSV cover the initial structured-data scope. Archive extraction and disk
patching add writes; inventory and text patch previews are provided instead.
General code execution, persistent memory and cron mutations already have
native invokr owners. Avoid parallel stores/schedulers and arbitrary code here.
