import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'base64': 'UEsFBgAAAAAAAAAAAAAAAAAAAAAAAA=='}, {'entries': [], 'total': 0, 'truncated': False})]
ERRORS = [{'base64': '!!!'}, {'base64': 'aGVsbG8='}]

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

    def test_suspicious_members_are_only_listed(self):
        import base64
        import io
        import stat
        import zipfile
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('../escape', 'x' * 1000000)
            link = zipfile.ZipInfo('link')
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(link, '/etc/passwd')
        args = {'base64': base64.b64encode(stream.getvalue()).decode()}
        data = json.loads(self.invoke(args)['result'])['data']
        self.assertEqual(data['total'], 2)
        self.assertTrue(all(item['unsafe_path'] for item in data['entries']))
        self.assertEqual(data['entries'][0]['bytes'], 1000000)

if __name__ == "__main__":
    unittest.main()
