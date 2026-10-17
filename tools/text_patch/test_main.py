import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'text': 'a\nb\n', 'old': 'b', 'new': 'c'}, {'text': 'a\nc\n', 'diff': '--- before\n+++ after\n@@ -1,2 +1,2 @@\n a\n-b\n+c', 'changed': True}), ({'text': 'a', 'old': 'a', 'new': 'a'}, {'text': 'a', 'diff': '', 'changed': False})]
ERRORS = [{'text': 'aa', 'old': 'a', 'new': 'b'}, {'text': 'a', 'old': '', 'new': 'b'}, {'text': 'a', 'old': 'x', 'new': 'b'}]

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

    def test_overlapping_matches_are_ambiguous(self):
        self.assertIn('error', self.invoke({'text': 'aaa', 'old': 'aa', 'new': 'b'}))

    def test_unicode_output_overflow_remains_json(self):
        result = self.invoke({'text': 'x', 'old': 'x', 'new': '界' * 4000})
        self.assertIn('output exceeds', result['error'])

if __name__ == "__main__":
    unittest.main()
