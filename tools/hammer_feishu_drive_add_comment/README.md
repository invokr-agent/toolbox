# hammer_feishu_drive_add_comment

Post a whole-document Feishu comment.

## Install and configure

Copy this directory into your invokr toolbox root and enable Python toolbox execution.
See the kit README for runtime configuration. No pip packages are needed.
Create `.secrets.json` **inside this tool directory only** with `{"token":"YOUR_SCOPED_TOKEN"}`;
set mode `0600`. Provision a dedicated least-privilege token. Never place it in
arguments, environment variables, examples, git or another tool's directory.
Missing/expired credentials fail clearly; this tool does not refresh tokens.

Example arguments: `{"file_token": "doc123", "text": "Example comment"}`.

DOCX documents only. Requires a scoped Feishu bearer token and document access. Posts remote content after invokr approval; no retries or deletion.

## Permissions and limits

Network: HTTPS port 443 on `open.feishu.cn` only. Public IPs only; DNS is validated then
pinned, TLS verified, redirects/proxies refused. No ambient credentials.
Approval is `ask`; workspace reads/writes disabled; no persistent scratch or state.
15-second invokr deadline, 12-second process alarm, 8-second socket timeout,
128 MiB declared memory, 64 KiB input/response and 30 KB serialized output cap.
Oversized responses fail; select a smaller page. No automatic pagination or retries.
Remote mutations are not retried after timeout because outcome may be unknown.
Runtime namespace and resource-limit caveats are documented in the kit README.

Success: `{"result":"{\"data\":...}"}`; failure:
`{"error":"invalid_request: ..."}`. Provider errors omit response bodies.

## Source and scope

Hermes source: `tools/feishu_drive_tool.py (feishu_drive_add_comment schema and request construction)` at `56a41715dc3b8bf6f50a740ff9416c4036ef4259`.
Takes the named operation and its core argument intent; adapts it to a bounded,
stateless subprocess with explicit operator credentials. No Hermes runtime imports.
Primary API reference: https://open.feishu.cn/document/server-docs/docs/drive-v1/file-comment/overview.
Invokr manifest reference: `3ffb0f91204d461706f79b7e448f51d5c4c9f24e`.

## Offline tests

`python3 -I -B test_main.py` tests wire requests, auth isolation, unsafe URLs,
private/mixed DNS, TLS pinning, response limits and protocol errors using mocks.
No installs or live provider calls. No claim of live-provider verification.
