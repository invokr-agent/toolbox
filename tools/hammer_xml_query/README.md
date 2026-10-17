# hammer_xml_query

Select XML elements by a simple ElementTree path; reject DTDs and entities.

Uses the standard ElementTree subset, not full XPath/XQuery. Namespaced names use {URI}tag notation. XML is supplied text, never a path or URL. DTD/entity declarations fail before parsing.

## Usage and isolation

Copy this directory into `~/.invokr/toolbox/` and refresh discovery. Keep the
namespace sandbox, isolated environment and per-tool venv enabled. This tool
has no network, workspace access, persistent writes or shared runtime imports.
Scratch: none used; invokr provides a private ephemeral `/tmp`.
64 KiB request, 30 KB result, 2-second alarm / 3-second runtime timeout, 128 MiB.

```json
{"name": "hammer_xml_query", "arguments": {"text": "<root><item id=\"1\">hello</item></root>", "path": "./item"}}
```

Binary-document examples are illustrative placeholders; supply the actual base64
document. Success is `{"result":"<JSON with data>"}`; errors are
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
