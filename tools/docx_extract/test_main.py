import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'base64': 'UEsDBBQAAAAIAPO+T10F0fQJcgAAAJcAAAARAAAAd29yZC9kb2N1bWVudC54bWxFzjEOwjAMBdCroB4AVwwMUcjMNUJi2kqxHdlBgdvTlIHlfVv+g313WdKLkNvpTYXN9du0tlYdgKUVKdpZKvJ+e4pSbPuqC3TRXFUSmm28UIHLPF+B4sZT8N09JH9G1oEOWrhjKeJhjEM9rIe/OvxfCV9QSwECFAMUAAAACADzvk9dBdH0CXIAAACXAAAAEQAAAAAAAAAAAAAAgAEAAAAAd29yZC9kb2N1bWVudC54bWxQSwUGAAAAAAEAAQA/AAAAoQAAAAAA', 'limit': 8000}, {'text': 'Hello', 'paragraphs': 1, 'truncated': False})]
ERRORS = [{'base64': 'bad'}, {'base64': 'UEsFBgAAAAAAAAAAAAAAAAAAAAAAAA=='}]

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
        self.assertIn("error", self.invoke(ERRORS[0]))

    def test_protocol(self):
        for raw in ("{", "[]", "null", '{"name":"wrong","arguments":{}}',
                    json.dumps({"name": NAME, "arguments": []}), " " * 65537):
            with self.subTest(raw=raw[:80]):
                self.assertIn("error", self.invoke(raw=raw))
        self.assertIn("error", self.invoke({"unknown": 1}))
        self.assertIn("error", self.invoke({}))

    def test_xml_declarations_and_archive_bombs_rejected(self):
        import base64
        import io
        import zipfile
        for content in ['<!DOCTYPE x [<!ENTITY a "boom">]><x>&a;</x>', 'x' * 2000001]:
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('word/document.xml', content)
            result = self.invoke({'base64': base64.b64encode(stream.getvalue()).decode()})
            self.assertIn('error', result)

if __name__ == "__main__":
    unittest.main()
