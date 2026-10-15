import json
import math
import signal
import sys
from pathlib import Path

import base64
import io
import zipfile
import xml.etree.ElementTree as ET

def archive_from(encoded):
    try:
        archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded, validate=True)))
        if len(archive.infolist()) > 500 or sum(item.file_size for item in archive.infolist()) > 2000000:
            archive.close()
            raise ValueError("document exceeds 500 members or 2 MB expanded size")
        return archive
    except (zipfile.BadZipFile, RuntimeError) as exc:
        raise ValueError("invalid document archive") from exc

def xml_member(archive, name):
    try:
        with archive.open(name) as stream:
            data = stream.read(1000001)
        if len(data) > 1000000 or b"\x00" in data or b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
            raise ValueError("XML exceeds size limit or contains forbidden declarations")
        return ET.fromstring(data)
    except (KeyError, ET.ParseError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ValueError("invalid or missing document XML") from exc

def run(args):
    with archive_from(args["base64"]) as archive:
        document = xml_member(archive, "word/document.xml")
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        paragraphs = ["".join(node.text or "" for node in paragraph.iter(ns + "t"))
                      for paragraph in document.iter(ns + "p")]
        text = "\n".join(paragraphs)
        return {"text": text[:args["limit"]], "paragraphs": len(paragraphs), "truncated": len(text) > args["limit"]}

def reject_constant(value):
    raise ValueError("non-finite JSON number")


def deadline(signum, frame):
    raise TimeoutError("operation exceeded 2 seconds")


def serve():
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(2)
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
