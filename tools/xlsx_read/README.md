# xlsx_read

Read cached cell values from a base64 XLSX worksheet; never evaluate formulas.

Values stay strings, including Excel date serials. Reads numbered worksheet files, not display-name mapping. Shared and inline strings supported. Formulas are returned as text with their cached value, never evaluated. External links/macros ignored; no archive extraction.

## Usage and isolation

Copy this directory into `~/.invokr/toolbox/` and refresh discovery. Keep the
namespace sandbox, isolated environment and per-tool venv enabled. This tool
has no network, workspace access, persistent writes or shared runtime imports.
Scratch: none used; invokr provides a private ephemeral `/tmp`.
64 KiB request, 30 KB result, 2-second alarm / 3-second runtime timeout, 128 MiB.

```json
{"name": "xlsx_read", "arguments": {"base64": "UEsDBBQAAAAIAPO+T12X0SzhVwAAAGIAAAAUAAAAeGwvc2hhcmVkU3RyaW5ncy54bWwVjDEOgCAMAL9ieIAlDg6mdvYbRKuQUCC0g88Xx7tLDlVteiUX3V00axuAnpEl6Fwbl1Hu2iXYwP6Ats7h0shskmHxfgUJqThCTYRGB+dcEYwQfgFjTh9QSwMEFAAAAAgA875PXUIweaaCAAAAtwAAABgAAAB4bC93b3Jrc2hlZXRzL3NoZWV0MS54bWxNzt0KAiEQBeBXEW+DRveiixgHil5kMDej9QeV3R4/k1i6nPNxDoNbKq/qnWviHZZYjfSt5TNAtd4FrseUXewypxK49bM8oObi+D5KYYFJqRMEfkZJOLIbNyYsaSO0ohh50VI0I2v3lRTCSgj2Z1fd05n0QSPMX592h7EAf5Ow/0ofUEsBAhQDFAAAAAgA875PXZfRLOFXAAAAYgAAABQAAAAAAAAAAAAAAIABAAAAAHhsL3NoYXJlZFN0cmluZ3MueG1sUEsBAhQDFAAAAAgA875PXUIweaaCAAAAtwAAABgAAAAAAAAAAAAAAIABiQAAAHhsL3dvcmtzaGVldHMvc2hlZXQxLnhtbFBLBQYAAAAAAgACAIgAAABBAQAAAAA="}}
```

The example is a tiny valid fixture. Supply your document as base64. Success is `{"result":"<JSON with data>"}`; errors are
`{"error":"invalid_request: explanation"}`. Unknown arguments fail.

## Offline tests and dependencies

Run `python3 -B test_main.py` with the exact pinned dependencies already available,
or use a prepared `.venv/bin/python`. Tests do not install or access network.
Dependency-bearing tools include `requirements.lock` (PyPI wheel SHA-256 hashes)
and an import map. No extras are enabled; Python 3.11+ needs no transitive deps
for these pins. Invokr performs its normal approved wheel-only hash-checked
preparation at install time. Standard-library tools have empty dependency sets.

## Provenance

Hermes `tools/file_tools.py` READ_FILE_SCHEMA's document extraction and
`tools/code_execution_tool.py` EXECUTE_CODE_SCHEMA's structured processing
inspired this narrow operation. Revision
`56a41715dc3b8bf6f50a740ff9416c4036ef4259`, installed at `~/.hermes/hermes-agent`;
official repository https://github.com/NousResearch/hermes-agent.
Schemas and implementation here are original, not claims of identical Hermes
tools. Invokr contract is `3ffb0f9`; see kit `SOURCES.md`.
