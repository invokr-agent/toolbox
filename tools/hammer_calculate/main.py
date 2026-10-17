import json
import math
import signal
import sys
from pathlib import Path

import ast
import operator

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}

def evaluate(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        value = node.value
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = evaluate(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
    elif isinstance(node, ast.BinOp) and type(node.op) in OPS:
        value = OPS[type(node.op)](evaluate(node.left), evaluate(node.right))
    else:
        raise ValueError("only numbers and + - * / // % are allowed")
    if not math.isfinite(value) or abs(value) > 1e100:
        raise ValueError("intermediate magnitude exceeds 1e100")
    return value

def run(args):
    if len(args["expression"]) > 512:
        raise ValueError("expression exceeds 512 characters")
    try:
        tree = ast.parse(args["expression"], mode="eval")
    except SyntaxError as exc:
        raise ValueError("invalid arithmetic syntax") from exc
    if sum(1 for _ in ast.walk(tree)) > 100:
        raise ValueError("expression exceeds 100 syntax nodes")
    return {"value": evaluate(tree.body)}


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
