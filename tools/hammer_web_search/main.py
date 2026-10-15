import json
import math
import signal
import sys
from pathlib import Path
# Copy into the individual tool; never import this shared template at runtime.
import http.client
import ipaddress
import socket
import ssl
from urllib.parse import urlsplit


def request(url, method="GET", body=None, headers=None):
    """One bounded HTTPS request; no proxies, redirects, ambient auth or cookies."""
    if any(ord(char) < 33 or ord(char) == 127 for char in url):
        raise ValueError("URL must not contain whitespace or controls")
    parsed = urlsplit(url)
    spec = json.loads(Path(__file__).with_name("plugin.json").read_text())
    hosts = spec["network"]["allow_hosts"]
    if (parsed.scheme != "https" or parsed.hostname not in hosts or parsed.port not in (None, 443)
            or parsed.username is not None or parsed.password is not None or parsed.fragment):
        raise ValueError("URL must be HTTPS port 443 on a declared host, without credentials or fragment")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("destination must resolve only to public IP addresses")
    family, kind, protocol, _, address = addresses[0]
    raw = socket.socket(family, kind, protocol)
    connection = http.client.HTTPSConnection(parsed.hostname, timeout=8)
    try:
        raw.settimeout(8)
        raw.connect(address)  # Pin the checked address: never resolve the hostname a second time.
        connection.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=parsed.hostname)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        request_headers = {"Accept-Encoding": "identity", "User-Agent": "invokr-hammer/1"}
        request_headers.update(headers or {})
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        if 300 <= response.status < 400:
            raise ValueError("redirect refused; use the approved final URL")
        if not 200 <= response.status < 300:
            raise ValueError("HTTP status " + str(response.status))
        if response.getheader("Content-Encoding", "identity").lower() != "identity":
            raise ValueError("compressed response refused")
        data = response.read(65537)
        if len(data) > 65536:
            raise ValueError("response exceeds 64 KiB")
        return response.status, response.getheader("Content-Type", ""), data
    except (http.client.HTTPException, OSError) as exc:
        # Do not echo URLs, tokens, query parameters or provider error bodies.
        raise ValueError("HTTPS request failed: " + type(exc).__name__) from exc
    finally:
        connection.close()
        raw.close()

from urllib.parse import urlencode

def run(args):
    settings = json.loads(Path(__file__).with_name("settings.json").read_text())
    endpoint = settings.get("endpoint", "")
    if not endpoint:
        raise ValueError("configure endpoint in this tool's settings.json and hostname in plugin.json")
    if urlsplit(endpoint).query or urlsplit(endpoint).fragment:
        raise ValueError("search endpoint must have no query or fragment")
    _, _, body = request(endpoint + "?" + urlencode({"q": args["query"], "format": "json"}))
    payload = json.loads(body)
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("search endpoint must return SearXNG JSON results")
    results = []
    for item in payload["results"][:args["limit"]]:
        if not isinstance(item, dict):
            raise ValueError("search result must be an object")
        link = item.get("url", "")
        if not isinstance(link, str) or urlsplit(link).scheme not in {"http", "https"}:
            continue
        results.append({"title": str(item.get("title", ""))[:300], "url": link[:2000],
                        "snippet": str(item.get("content", ""))[:1000]})
    return {"results": results, "truncated": len(payload["results"]) > args["limit"]}

def reject_constant(value):
    raise ValueError("non-finite JSON number")


def deadline(signum, frame):
    raise TimeoutError("operation exceeded 12 seconds")


def serve():
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(12)
    try:
        raw = sys.stdin.buffer.read(65537)
        if len(raw) > 65536:
            raise ValueError("input exceeds 64 KiB; send a smaller chunk")
        call = json.loads(raw, parse_constant=reject_constant)
        spec = json.loads(Path(__file__).with_name("plugin.json").read_text())
        if not isinstance(call, dict) or call.get("name") != spec["name"]:
            raise ValueError("name must match plugin name")
        args = call.get("arguments")
        if not isinstance(args, dict):
            raise ValueError("arguments must be an object")
        schema = spec["parameters"]
        if set(args) - schema["properties"].keys():
            raise ValueError("unknown argument")
        for key in schema["required"]:
            if key not in args:
                raise ValueError("missing argument: " + key)
        for key, rule in schema["properties"].items():
            if key not in args:
                if "default" in rule:
                    args[key] = rule["default"]
                continue
            value = args[key]
            types = {"string": (str,), "integer": (int,), "number": (int, float), "boolean": (bool,)}
            if type(value) not in types[rule["type"]]:
                raise ValueError(key + " must be " + rule["type"])
            if "enum" in rule and value not in rule["enum"]:
                raise ValueError(key + " must be one of " + str(rule["enum"]))
            if isinstance(value, str) and len(value) > rule.get("maxLength", 32000):
                raise ValueError(key + " is too long")
            if type(value) in (int, float):
                if not math.isfinite(value) or not rule.get("minimum", -1e100) <= value <= rule.get("maximum", 1e100):
                    raise ValueError(key + " is outside allowed range")
        result = json.dumps({"data": run(args)}, ensure_ascii=True, allow_nan=False)
        output = json.dumps({"result": result})
        if len(output.encode()) > 30000:
            raise ValueError("output exceeds 30 KB; send a smaller chunk or lower limit")
    except (ValueError, TypeError, KeyError, IndexError, ArithmeticError, RecursionError, TimeoutError, OSError) as exc:
        output = json.dumps({"error": "invalid_request: " + str(exc)[:200]})
    finally:
        signal.alarm(0)
    print(output)


if __name__ == "__main__":
    serve()
