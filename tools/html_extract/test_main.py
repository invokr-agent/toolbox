import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'html': '<h1>A &amp; B</h1><script>bad()</script><p>OK</p>'}, {'text': 'A & B\nOK', 'links': [], 'truncated': False}), ({'html': '<a href="javascript:bad()">a</a><a href="https://example.org">b</a>', 'limit': 1}, {'text': 'a', 'links': ['https://example.org'], 'truncated': True})]
ERRORS = [{'html': 1}, {'html': 'abc', 'limit': 0}]

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

    def test_untrusted_markup_and_link_cap(self):
        html = '<template><p>hidden</p></template><!--hidden--><style>hidden</style>'
        html += '<a href="https://user:password@example.org">visible</a>'
        html += ''.join('<a href="https://example.org/' + str(i) + '">x</a>' for i in range(101))
        data = json.loads(self.invoke({'html': html})['result'])['data']
        self.assertNotIn('hidden', data['text'])
        self.assertEqual(len(data['links']), 100)
        self.assertFalse(any('password' in link for link in data['links']))

if __name__ == "__main__":
    unittest.main()
