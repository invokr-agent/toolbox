import importlib.util
import json
from pathlib import Path
import tempfile
import shutil
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('validator', ROOT / 'validate.py')
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ValidatorTests(unittest.TestCase):
    def test_template(self):
        validator.validate_tool(ROOT / 'template', template=True)

    def test_rejects_drift(self):
        mutations = [lambda s: s['capabilities'].update(network=True),
                     lambda s: s.update(daemon=0),
                     lambda s: s.update(network={'allow_hosts': ['example.org']}),
                     lambda s: s['capabilities'].update(writes_workspace=True),
                     lambda s: s['limits'].update(timeout_seconds=90),
                     lambda s: s.update(daemon=True),
                     lambda s: s.update(scratch='/host'),
                     lambda s: s['parameters'].update(additionalProperties=True),
                     lambda s: s['parameters']['properties']['text'].update(type='object'),
                     lambda s: s.update(example='{}')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / 'template'
                shutil.copytree(ROOT / 'template', target)
                spec = json.loads((target / 'plugin.json').read_text())
                mutation(spec)
                (target / 'plugin.json').write_text(json.dumps(spec))
                with self.assertRaises(ValueError):
                    validator.validate_tool(target, template=True)

    def test_rejects_dependency_import_and_missing_test(self):
        for filename, contents in [('requirements.txt', 'requests>=2'),
                                   ('requirements.txt', 'requests==2.32.5'),
                                   ('main.py', 'from another_tool import run'),
                                   ('main.py', 'from . import run'),
                                   ('test_main.py', '# no tests'),
                                   ('test_main.py', None)]:
            with self.subTest(filename=filename, contents=contents), tempfile.TemporaryDirectory() as temp:
                target = Path(temp) / 'template'
                shutil.copytree(ROOT / 'template', target)
                file = target / filename
                if contents is None:
                    file.unlink()
                else:
                    file.write_text(contents)
                with self.assertRaises(ValueError):
                    validator.validate_tool(target, template=True)

    def test_symlinks_and_unknown_schema_keywords_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'template'
            shutil.copytree(ROOT / 'template', target)
            (target / 'escape').symlink_to(ROOT)
            with self.assertRaises(ValueError):
                validator.validate_tool(target, template=True)
        with self.assertRaises(ValueError):
            validator.check('x', {'oneOf': []})


if __name__ == '__main__':
    unittest.main()
