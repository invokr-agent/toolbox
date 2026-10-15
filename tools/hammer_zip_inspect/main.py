import json
import math
import signal
import sys
from pathlib import Path

import base64
import binascii
import io
import stat
import zipfile
from pathlib import PurePosixPath

def run(args):
    try:
        blob = base64.b64decode(args["base64"], validate=True)
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            infos = archive.infolist()
            entries = []
            for item in infos[:args["limit"]]:
                path = PurePosixPath(item.filename.replace("\\", "/"))
                unsafe = path.is_absolute() or ".." in path.parts or ":" in item.filename or stat.S_ISLNK(item.external_attr >> 16)
                entries.append({"name": item.filename, "bytes": item.file_size, "compressed_bytes": item.compress_size,
                                "unsafe_path": unsafe, "encrypted": bool(item.flag_bits & 1)})
            return {"entries": entries, "total": len(infos), "truncated": len(infos) > len(entries)}
    except (binascii.Error, zipfile.BadZipFile, NotImplementedError) as exc:
        raise ValueError("invalid ZIP/base64: " + str(exc)) from exc


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
