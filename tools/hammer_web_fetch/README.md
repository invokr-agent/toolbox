# hammer_web_fetch

Fetch readable text and links from an approved HTTPS URL.

HTML/text/JSON only, UTF-8 decoding with replacement. No JavaScript, PDFs, downloads or redirect following.

## Install and configure

Copy this directory into `~/.invokr/toolbox/`. Review `network.allow_hosts` in
`plugin.json`; only exact lowercase public DNS hostnames are accepted. Change
the list to the hosts you approve, then reload invokr. Keep env isolation on,
per-tool venvs and the namespace sandbox enabled. Do not use YOLO/unsandboxed mode.

Example stdin:

```json
{"name": "hammer_web_fetch", "arguments": {"url": "https://docs.python.org/3/", "limit": 1000}}
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

Hermes tools/web_tools.py WEB_EXTRACT_SCHEMA: URL input, readable extraction, bounded text without LLM summarization.
Hermes revision `56a41715dc3b8bf6f50a740ff9416c4036ef4259`; installed under
`~/.hermes/hermes-agent`. See kit `SOURCES.md` for official links and invokr contract.
Protocol references: https://docs.python.org/3/library/http.client.html and
https://docs.searxng.org/dev/search_api.html (search only).
