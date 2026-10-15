# hammer_x_search

Search public X posts using the xAI search tool.

## Install and configure

Copy this directory into your invokr toolbox root and enable Python toolbox execution.
See the kit README for runtime configuration. No pip packages are needed.
Create `.secrets.json` **inside this tool directory only** with `{"token":"YOUR_SCOPED_TOKEN"}`;
set mode `0600`. Provision a dedicated least-privilege token. Never place it in
arguments, environment variables, examples, git or another tool's directory.
Missing/expired credentials fail clearly; this tool does not refresh tokens.

Example arguments: `{"query": "Recent public posts about Python", "model": "operator-selected-model"}`.

Read-only public discovery through a potentially billable provider call. Returns bounded provider output including citations when supplied. No posting, handle filters, date filters, retries or account impersonation. Native invokr web_search remains the general web search owner.

## Permissions and limits

Network: HTTPS port 443 on `api.x.ai` only. Public IPs only; DNS is validated then
pinned, TLS verified, redirects/proxies refused. No ambient credentials.
Approval is `ask`; workspace reads/writes disabled; no persistent scratch or state.
60-second invokr deadline, 58-second process alarm, 50-second socket timeout,
128 MiB declared memory, 64 KiB input/response and 30 KB serialized output cap.
Oversized responses fail; select a smaller page. No automatic pagination or retries.
Remote mutations are not retried after timeout because outcome may be unknown.
Runtime namespace and resource-limit caveats are documented in the kit README.

Success: `{"result":"{\"data\":...}"}`; failure:
`{"error":"invalid_request: ..."}`. Provider errors omit response bodies.

## Source and scope

Hermes source: `tools/x_search_tool.py:324-349 (query, Responses input, x_search tool and store=false)` at `56a41715dc3b8bf6f50a740ff9416c4036ef4259`.
Takes the named operation and its core argument intent; adapts it to a bounded,
stateless subprocess with explicit operator credentials. No Hermes runtime imports.
Primary API reference: https://docs.x.ai/developers/tools/x-search.
Invokr manifest reference: `3ffb0f91204d461706f79b7e448f51d5c4c9f24e`.

## Offline tests

`python3 -I -B test_main.py` tests wire requests, auth isolation, unsafe URLs,
private/mixed DNS, TLS pinning, response limits and protocol errors using mocks.
No installs or live provider calls. No claim of live-provider verification.
