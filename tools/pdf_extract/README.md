# pdf_extract

Extract a bounded PDF page text layer from base64 bytes; no OCR.

Text layer only, one page per call. Empty text is explicitly flagged and does not mean an image/scanned page is empty. No scripts, attachments, forms or embedded URLs execute. Runs under the tool memory/time caps.

## Usage and isolation

Copy this directory into `~/.invokr/toolbox/` and refresh discovery. Keep the
namespace sandbox, isolated environment and per-tool venv enabled. This tool
has no network, workspace access, persistent writes or shared runtime imports.
Scratch: none used; invokr provides a private ephemeral `/tmp`.
64 KiB request, 30 KB result, 2-second alarm / 3-second runtime timeout, 128 MiB.

```json
{"name": "pdf_extract", "arguments": {"base64": "JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovUHJvZHVjZXIgKHB5cGRmKQo+PgplbmRvYmoKMiAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyA0IDAgUiBdCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKNCAwIG9iago8PAovVHlwZSAvUGFnZQovUmVzb3VyY2VzIDw8Ci9Gb250IDw8Ci9GMSA1IDAgUgo+Pgo+PgovTWVkaWFCb3ggWyAwLjAgMC4wIDEwMCAxMDAgXQovUGFyZW50IDIgMCBSCi9Db250ZW50cyA2IDAgUgo+PgplbmRvYmoKNSAwIG9iago8PAovVHlwZSAvRm9udAovU3VidHlwZSAvVHlwZTEKL0Jhc2VGb250IC9IZWx2ZXRpY2EKPj4KZW5kb2JqCjYgMCBvYmoKPDwKL0xlbmd0aCAzNQo+PgpzdHJlYW0KQlQgL0YxIDEyIFRmIDEwIDUwIFRkIChIZWxsbykgVGogRVQKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNwowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTUgMDAwMDAgbiAKMDAwMDAwMDA1NCAwMDAwMCBuIAowMDAwMDAwMTEzIDAwMDAwIG4gCjAwMDAwMDAxNjIgMDAwMDAgbiAKMDAwMDAwMDI5NCAwMDAwMCBuIAowMDAwMDAwMzY0IDAwMDAwIG4gCnRyYWlsZXIKPDwKL1NpemUgNwovUm9vdCAzIDAgUgovSW5mbyAxIDAgUgo+PgpzdGFydHhyZWYKNDQ5CiUlRU9GCg=="}}
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
