# Inspected sources and design decisions

## Hermes

Installed checkout: `~/.hermes/hermes-agent`, revision
`56a41715dc3b8bf6f50a740ff9416c4036ef4259`.
Official repository: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent).
The six files below were fetched from the official repository at that revision
and SHA-256 compared with the installed files: all matched. Only specifications
and capability ideas informed this kit; implementation is original Python, with three explicitly locked parser dependencies.

| Inspected source / tool | What was taken or deliberately omitted |
| --- | --- |
| [`toolsets.py`](https://github.com/NousResearch/hermes-agent/blob/56a41715dc3b8bf6f50a740ff9416c4036ef4259/toolsets.py), `TOOLSETS` | Evaluated web, file, code_execution, memory and cronjob categories; chose independent narrow operations. No registry or composed toolset runtime copied. |
| [`tools/file_tools.py`](https://github.com/NousResearch/hermes-agent/blob/56a41715dc3b8bf6f50a740ff9416c4036ef4259/tools/file_tools.py), `PATCH_SCHEMA` | `hammer_text_patch`: exact old/new strings, unique-match requirement and diff feedback. Omitted fuzzy matching, multi-file patch dialect and disk writes. |
| Same file, `SEARCH_FILES_SCHEMA` | `hammer_regex_search`: pattern, bounded matches, line numbers. Supplied text replaces filesystem roots, globs and ripgrep subprocesses. |
| Same file, `READ_FILE_SCHEMA` | Bounded readable/structured inspection inspired `hammer_zip_inspect`. ZIP metadata is a new specialization, not an existing Hermes ZIP schema. No office converter or package auto-install. |
| Same file, `WRITE_FILE_SCHEMA` | Evaluated and omitted persistent file overwrite; invokr's native file-edit owner already exists. |
| [`tools/web_tools.py`](https://github.com/NousResearch/hermes-agent/blob/56a41715dc3b8bf6f50a740ff9416c4036ef4259/tools/web_tools.py), `WEB_EXTRACT_SCHEMA` | `hammer_html_extract`: readable text without LLM summarization, explicit character budget. Omitted URL fetching, PDFs, saved full-text files and provider credentials. |
| Same file, `WEB_SEARCH_SCHEMA` | Evaluated query/limit shape; dropped online search from initial kit due to network/provider needs and native invokr ownership. |
| [`tools/code_execution_tool.py`](https://github.com/NousResearch/hermes-agent/blob/56a41715dc3b8bf6f50a740ff9416c4036ef4259/tools/code_execution_tool.py), `build_execute_code_schema`, `EXECUTE_CODE_SCHEMA` | Structured transformations and computation motivate `hammer_json_query`, `hammer_csv_query`, `hammer_calculate`, `hammer_units`. Their schemas are original narrow replacements, not purported Hermes equivalents. Omitted generated scripts, arbitrary code, tool RPC and inherited execution context. |
| [`tools/memory_tool.py`](https://github.com/NousResearch/hermes-agent/blob/56a41715dc3b8bf6f50a740ff9416c4036ef4259/tools/memory_tool.py), `MEMORY_SCHEMA` | Evaluated add/replace/remove and target stores. Omitted duplicate persistent memory and cross-call mutation; native invokr memory remains owner. |
| [`tools/cronjob_tools.py`](https://github.com/NousResearch/hermes-agent/blob/56a41715dc3b8bf6f50a740ff9416c4036ef4259/tools/cronjob_tools.py), `CRONJOB_SCHEMA` | Explicit ISO timestamps inform `hammer_datetime`; scheduling, delivery, scripts and job state omitted. Native invokr scheduler remains owner. |

## Invokr

Contract revision: `3ffb0f91204d461706f79b7e448f51d5c4c9f24e` from the locally
available `origin/dev` reference. The original checkout was inspected read-only;
a `git archive` snapshot was used for compatibility tests and lint builds.
Paths below are relative to that revision of
`https://github.com/antonikliment/invokr-pre-release`.

| Source | Adopted convention / conclusion |
| --- | --- |
| `docs/agents/README.md` | Read routing and existing subsystem ownership before adding behavior. |
| `toolbox/README.md` | Plugin layout, manifest limits, JSON envelope, network caveat and per-tool venv. |
| `toolbox/browser_agent/plugin.json` | Explicit namespace, policy and capability fields. Hammer uses one-shot and explicit per-tool network profiles. |
| `toolbox/browser_agent/main.py` | Outer result must be a string: JSON-encode structured results inside it. Clear error envelope. No browser code copied. |
| `toolbox/browser_agent/requirements.txt` | Exact direct pin convention. Most Hammer tools are stdlib; three document parsers have complete hash locks. |
| `toolbox/browser_agent/test_main.py` | Offline tests of validation and protocol framing without launching external services. |
| `docs/onboarding/05-toolbox.md` | Installation/discovery, namespace mounting, credential isolation, native retired-tool ownership. |
| `docs/agents/adr/0005-python-toolbox-supply-chain.md` | Resolved wheel graph and runtime-generated hashes, approval and restricted installation. Zero deps avoid install-time exposure. |
| `docs/agents/adr/0005-toolbox-namespace-sandbox.md` | All executions must use the same capability-derived seam; daemon mode is not a bypass. |
| `docs/private/plans/python-toolbox-improvements.md` | Historical traversal/env/output issues reinforce no path inputs and explicit bounds; current code/accepted ADRs take precedence over old plan details. |
| `docs/private/plans/toolbox-agent-authored-tools.md` | Evaluate threat model and supply-chain controls; do not confuse proposed scratch/egress controls with runtime-enforced permissions. |
| `tools/system/toolbox/{spec,python_env,mode,daemon,toolbox}.go` | Actual loader fields, pin handling, preparation behavior, approval modes, per-tool/session state and environment. |
| `tools/system/toolbox/{extensions,browser_contract,toolbox,daemon}_test.go` | Core schema checks, result-string framing, limits and daemon isolation; external overlay exercises actual producers. |
| `tools/core/sandbox/sandbox_linux.go` | Runtime/source mounts read-only; private `/tmp`; network disabled without capability; no manifest-named scratch field. |

## Standard-library behavior

Primary references: [Python JSON](https://docs.python.org/3/library/json.html),
[csv](https://docs.python.org/3/library/csv.html),
[difflib](https://docs.python.org/3/library/difflib.html),
[re](https://docs.python.org/3/library/re.html),
[zipfile](https://docs.python.org/3/library/zipfile.html),
[ast](https://docs.python.org/3/library/ast.html),
[datetime](https://docs.python.org/3/library/datetime.html),
[HTMLParser](https://docs.python.org/3/library/html.parser.html), and
[RFC 6901](https://www.rfc-editor.org/rfc/rfc6901).

## Expanded catalog inspection

`catalog/hermes.json` records all 94 registration/toolset entries, schema symbols,
source line numbers and installed file SHA-256 hashes. `catalog/coverage.json`
and its readable table record what was adopted or why a host/gateway tool is not
portable. Dynamic provider registrations are outside that static inventory.

| Inspected Hermes path | Adopted intent / adaptation |
| --- | --- |
| `tools/feishu_doc_tool.py`, `tools/feishu_drive_tool.py` | Document token/raw text; comment IDs, pages and text replies. Direct fixed-host REST calls, per-tool tokens; no gateway session. |
| `tools/homeassistant_tool.py:354-469` | Entity state, domain filtering, service discovery/calls. Explicit public HTTPS proxy only; no LAN discovery or inherited configuration. |
| `tools/discord_tool.py` | Action enums, channel/guild IDs, message reads and guild metadata. Narrow bot adapter; message sends disable mentions; no destructive admin actions. |
| `toolsets.py:378-379` | Seven Spotify capability names. Core checkout has no corresponding provider schemas; original narrow schemas use Spotify's official API, including current playlist /items endpoint. |
| `tools/flux3_video_tool.py` | Examined gateway auth/upload/poll/delivery contracts; rejected borrowing Hermes bearer or faking gateway policy. |
| `tools/kanban_tools.py`, `tools/project_tools.py`, browser/UI/gateway files in inventory | Registration/schema capability audit; no shared mutable runtime or desktop authority copied into stateless tools. |

Primary API references are linked in each adapter README: Home Assistant REST,
Feishu docs/drive APIs, Discord message/guild resources, and Spotify Web API. Dependencies use official PyPI metadata and wheel SHA-256 values:
PyYAML 6.0.3, Markdown 3.10.3 and pypdf 6.19.0. Per-tool READMEs record exact
parser scope and limitations. No third-party blog recipes or executable Hermes
code were copied. Only the original six files above were compared byte-for-byte
with the official repository; the expanded inventory hashes describe local source.
