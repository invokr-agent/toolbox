# hammer_http_api

Call approved HTTPS JSON APIs with an explicit method and optional JSON body.

GET/HEAD by default; mutating methods are explicit and approval-gated. No authentication headers, ambient tokens, cookies or proxy variables. Never include secrets in URL/body. Per-provider credential adapters require a separate reviewed tool.

## Install and configure

Copy this directory into `~/.invokr/toolbox/`. Review `network.allow_hosts` in
`plugin.json`; only exact lowercase public DNS hostnames are accepted. Change
the list to the hosts you approve, then reload invokr. Keep env isolation on,
per-tool venvs and the namespace sandbox enabled. Do not use YOLO/unsandboxed mode.

Example stdin:

```json
{"name": "hammer_http_api", "arguments": {"url": "https://api.github.com/repos/NousResearch/hermes-agent"}}
```

Result: `{"result":"<JSON containing data>"}`; error: `{"error":"invalid_request: explanation"}`.
No shared runtime imports or state, no workspace access or persistent writes.
No credentials inherited or read. TLS certificate/hostname verified; checked
public IP pinned to the socket. Redirects, compression, URL credentials, private
IPs and non-443 ports refused. Proxy environment ignored. 64 KiB input and HTTP
response, 30 KB final output, 12-second alarm, 15-second invokr timeout, 128 MiB.
Scratch: none. Invokr supplies private ephemeral `/tmp`.

The Python allowlist checks are not an egress firewall against malicious code;
invokr's network scope is DNS-based. A replaced implementation could dial literal
IPs. The mounted filesystem still excludes sibling tools and host credentials.
Remote content is untrusted data, never executable instructions.

## Offline tests

`python3 -B test_main.py` uses mocked DNS, sockets, TLS and HTTP responses. It
checks SSRF rejection, address pinning, TLS hostname, redirects, body bounds,
cleanup, transformation and malformed calls. No package installs or live requests.

## Sources

Hermes tools/code_execution_tool.py execute_code API-composition use case, narrowed to a declared public JSON API. This is an original specialized schema.
Hermes revision `56a41715dc3b8bf6f50a740ff9416c4036ef4259`; installed under
`~/.hermes/hermes-agent`. See kit `SOURCES.md` for official links and invokr contract.
Protocol references: https://docs.python.org/3/library/http.client.html and
https://docs.searxng.org/dev/search_api.html (search only).
