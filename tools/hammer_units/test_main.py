import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'value': 1, 'from_unit': 'in', 'to_unit': 'cm'}, {'value': 2.54, 'unit': 'cm'}), ({'value': 32, 'from_unit': 'F', 'to_unit': 'C'}, {'value': 0.0, 'unit': 'C'})]
ERRORS = [{'value': 1, 'from_unit': 'm', 'to_unit': 'kg'}, {'value': -1, 'from_unit': 'K', 'to_unit': 'C'}]

class ToolTests(unittest.TestCase):
    def invoke(self, args=None, raw=None):
        if raw is None:
            raw = json.dumps({"name": NAME, "arguments": args})
        result = subprocess.run([sys.executable, "-I", "-B", str(HERE / "main.py")],
                                input=raw, text=True, capture_output=True, timeout=4,
                                env={"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertLess(len(result.stdout.encode()), 32768)
        return json.loads(result.stdout)

    def test_examples(self):
        for args, expected in CASES:
            with self.subTest(args=args):
                out = self.invoke(args)
                self.assertEqual(set(out), {"result"})
                self.assertEqual(json.loads(out["result"]), {"data": expected})

    def test_errors_and_recovery(self):
        for args in ERRORS:
            with self.subTest(args=args):
                self.assertIn("error", self.invoke(args))
        self.assertIn("result", self.invoke(CASES[0][0]))

    def test_protocol(self):
        for raw in ("{", "[]", "null", '{"name":"wrong","arguments":{}}',
                    json.dumps({"name": NAME, "arguments": []}), " " * 65537):
            with self.subTest(raw=raw[:80]):
                self.assertIn("error", self.invoke(raw=raw))
        self.assertIn("error", self.invoke({**CASES[0][0], "unknown": 1}))
        self.assertIn("error", self.invoke({}))

    def test_booleans_and_nonfinite_values_rejected(self):
        for value in [True, float('nan'), float('inf')]:
            self.assertIn('error', self.invoke({'value': value, 'from_unit': 'm', 'to_unit': 'cm'}))

if __name__ == "__main__":
    unittest.main()
