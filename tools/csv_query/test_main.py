import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'text': 'n,v\n"a,b",2\nc,3\n', 'limit': 1}, {'columns': ['n', 'v'], 'rows': [{'n': 'a,b', 'v': '2'}], 'matched': 2, 'truncated': True}), ({'text': 'n,v\na,2\nb,3', 'column': 'v', 'equals': '3'}, {'columns': ['n', 'v'], 'rows': [{'n': 'b', 'v': '3'}], 'matched': 1, 'truncated': False})]
ERRORS = [{'text': ''}, {'text': 'a,a\n1,2'}, {'text': 'a,b\n1'}, {'text': 'a\n1', 'column': 'z'}]

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

    def test_quoted_newline_and_invalid_quote(self):
        data = json.loads(self.invoke({'text': 'a,b\n"hello\nworld",2'})['result'])['data']
        self.assertEqual(data['rows'], [{'a': 'hello\nworld', 'b': '2'}])
        self.assertIn('error', self.invoke({'text': 'a,b\n"unterminated,2'}))

if __name__ == "__main__":
    unittest.main()
