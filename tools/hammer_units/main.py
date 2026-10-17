import json
import math
import signal
import sys
from pathlib import Path

# SI base = value * scale + offset. International inch/pound definitions.
UNITS = {"m": ("length",1,0), "km": ("length",1000,0), "cm": ("length",.01,0),
         "mm": ("length",.001,0), "in": ("length",.0254,0), "ft": ("length",.3048,0),
         "mi": ("length",1609.344,0), "kg": ("mass",1,0), "g": ("mass",.001,0),
         "lb": ("mass",.45359237,0), "s": ("time",1,0), "min": ("time",60,0),
         "h": ("time",3600,0), "day": ("time",86400,0), "C": ("temperature",1,273.15),
         "F": ("temperature",5/9,273.15-32*5/9), "K": ("temperature",1,0)}

def run(args):
    kind, scale, offset = UNITS[args["from_unit"]]
    target, target_scale, target_offset = UNITS[args["to_unit"]]
    if kind != target:
        raise ValueError("units must have the same dimension")
    base = args["value"] * scale + offset
    if kind == "temperature" and base < 0:
        raise ValueError("temperature is below absolute zero")
    return {"value": (base - target_offset) / target_scale, "unit": args["to_unit"]}


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
    except Exception as exc:  # any failure is a one-line error, never a traceback
        output = json.dumps({"error": "invalid_request: " + str(exc)[:200]})
    finally:
        signal.alarm(0)
    print(output)


if __name__ == "__main__":
    serve()
