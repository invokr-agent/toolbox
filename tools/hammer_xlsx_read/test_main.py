import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
NAME = json.loads((HERE / "plugin.json").read_text())["name"]
CASES = [({'base64': 'UEsDBBQAAAAIAPO+T12X0SzhVwAAAGIAAAAUAAAAeGwvc2hhcmVkU3RyaW5ncy54bWwVjDEOgCAMAL9ieIAlDg6mdvYbRKuQUCC0g88Xx7tLDlVteiUX3V00axuAnpEl6Fwbl1Hu2iXYwP6Ats7h0shskmHxfgUJqThCTYRGB+dcEYwQfgFjTh9QSwMEFAAAAAgA875PXUIweaaCAAAAtwAAABgAAAB4bC93b3Jrc2hlZXRzL3NoZWV0MS54bWxNzt0KAiEQBeBXEW+DRveiixgHil5kMDej9QeV3R4/k1i6nPNxDoNbKq/qnWviHZZYjfSt5TNAtd4FrseUXewypxK49bM8oObi+D5KYYFJqRMEfkZJOLIbNyYsaSO0ohh50VI0I2v3lRTCSgj2Z1fd05n0QSPMX592h7EAf5Ow/0ofUEsBAhQDFAAAAAgA875PXZfRLOFXAAAAYgAAABQAAAAAAAAAAAAAAIABAAAAAHhsL3NoYXJlZFN0cmluZ3MueG1sUEsBAhQDFAAAAAgA875PXUIweaaCAAAAtwAAABgAAAAAAAAAAAAAAIABiQAAAHhsL3dvcmtzaGVldHMvc2hlZXQxLnhtbFBLBQYAAAAAAgACAIgAAABBAQAAAAA=', 'sheet': 1, 'limit': 100}, {'cells': [{'cell': 'A1', 'value': 'Hello', 'type': 's', 'formula': ''}, {'cell': 'B1', 'value': '2', 'type': 'n', 'formula': '1+1'}], 'truncated': False})]
ERRORS = [{'base64': 'bad'}]

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
                archive.writestr('xl/worksheets/sheet1.xml', content)
            result = self.invoke({'base64': base64.b64encode(stream.getvalue()).decode()})
            self.assertIn('error', result)

if __name__ == "__main__":
    unittest.main()
