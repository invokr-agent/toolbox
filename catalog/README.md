# Full catalog and branch stack

The installed Hermes revision contains **94 named core/toolset tools** in
`hermes.json`. Dynamic MCP/provider registrations are runtime-dependent and
cannot be enumerated from static source alone. Entries record source paths,
registration lines, schema symbols, source hashes and toolset membership.

The initial nine tools remain on `master`. Expansion uses `stack/00-foundation`
as the common base, followed by one branch per tool in usefulness order. Each
branch contains its predecessors. Infrastructure commits precede tool commits;
each tool remains a complete independent directory in exactly one commit.
Every commit is pushed immediately. No PRs are created.

Priority order:

1. Web fetch/extraction, search and scoped HTTP APIs.
2. Structured documents, conversions, code/text inspection and the original utilities.
3. Provider-backed vision, image/audio/video tools and read-only integrations.
4. Remote mutations and automation, after explicit configuration and scoped credentials.
5. Hermes-native UI/session/orchestration tools requiring invokr runtime integration.

Native runtime tools are not silently counted as implemented Python plugins.
Desktop panes, a live browser session, an agent delegate, a scheduler and memory
cannot be reproduced by a stateless subprocess without an explicit host API.
The inventory retains them so missing integration work remains visible.

Network tool profile: explicit hostname allowlist in `plugin.json`, approval
`ask`, 15-second runtime deadline, 128 MiB memory, 32 KiB output. Individual
implementations pin a validated public address, verify TLS, disable redirects,
proxies and ambient credentials, and cap response bytes. Invokr's own hostname
scoping is DNS-based, not a literal-IP firewall: these Python checks protect
honest implementations from hostile inputs, not a malicious replacement script.
Workspace writes remain disabled. No provider calls occur during tests.
