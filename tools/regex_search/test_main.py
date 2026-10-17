import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'text': 'a\nbA', 'pattern': 'a', 'ignore_case': True}, {'matches': [{'text': 'a', 'start': 0, 'end': 1, 'line': 1}, {'text': 'A', 'start': 3, 'end': 4, 'line': 2}], 'truncated': False}), ({'text': 'aa', 'pattern': 'a', 'limit': 1}, {'matches': [{'text': 'a', 'start': 0, 'end': 1, 'line': 1}], 'truncated': True})]
ERRORS = [{'text': 'a', 'pattern': '['}, {'text': 'a', 'pattern': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}]

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

    def test_pathological_regex_is_bounded(self):
        result = self.invoke({'text': 'a' * 10000 + '!', 'pattern': '(a+)+$'})
        self.assertIn('exceeded 2 seconds', result['error'])

    def test_zero_width_unicode(self):
        result = json.loads(self.invoke({'text': 'é\n界', 'pattern': '^|界'})['result'])['data']
        self.assertEqual(result['matches'][1], {'text': '界', 'start': 2, 'end': 3, 'line': 2})

if __name__ == "__main__":
    unittest.main()
