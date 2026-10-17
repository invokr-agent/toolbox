# template

Return supplied text.

Copy this directory and replace the operation.

## Example

Pass this call on stdin to `python3 main.py` (Python 3.11+ on Linux):

```json
{"name":"template","arguments":{"text":"hello"}}
```

Success: `{"result":"<JSON string containing a data object>"}`.
Failure: `{"error":"invalid_request: short explanation"}`.
All arguments and defaults are in `plugin.json`; unknown fields are rejected.

## Isolation and limits

One-shot process, no shared imports/state, no network, no credentials, no
workspace access and no persistent writes. Scratch: none used; invokr provides
a private ephemeral `/tmp`. Tool and venv are mounted read-only at execution.
64 KiB request, 30 KB encoded response, 2-second Python alarm, 3-second invokr
timeout, 128 MiB invokr memory limit. Oversized responses fail, never truncate JSON.
Invoke through invokr's namespace sandbox with env isolation enabled; direct
Python is for trusted offline testing, not a security boundary.

## Dependencies and tests

`requirements.txt` explicitly contains zero third-party dependencies. No installs
or downloads in tests. Copy this complete directory into `~/.invokr/toolbox/`,
then restart invokr or refresh toolbox discovery. Keep per-tool venv defaults.

```sh
python3 -B -m unittest discover -s . -p 'test_*.py' -v
```

## Specification provenance

Invokr browser_agent JSON envelope and hammer bounded one-shot template.
See kit `SOURCES.md` for exact source paths, revisions and discarded features.
Implementation is original stdlib Python, not copied Hermes implementation.
