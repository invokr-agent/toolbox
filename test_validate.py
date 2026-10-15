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
    def test_catalog_has_one_decision_for_every_source_tool(self):
        inventory = json.loads((ROOT / 'catalog/hermes.json').read_text())['tools']
        decisions = json.loads((ROOT / 'catalog/coverage.json').read_text())
        names = [entry['name'] for entry in decisions]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {entry['name'] for entry in inventory})
        for entry in decisions:
            self.assertIn(entry['status'], {'adapter', 'native', 'runtime', 'gateway', 'artifact'})
            self.assertTrue(entry['reason'])
            self.assertTrue(entry['source'])
            self.assertTrue(entry['target'])

    def test_long_network_timeout_requires_network_permission(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'template'
            shutil.copytree(ROOT / 'template', target)
            spec = json.loads((target / 'plugin.json').read_text())
            spec['limits']['timeout_seconds'] = 60
            (target / 'plugin.json').write_text(json.dumps(spec))
            with self.assertRaises(ValueError):
                validator.validate_tool(target, template=True)
            spec['capabilities']['network'] = True
            spec['network'] = {'allow_hosts': ['api.example.com']}
            (target / 'plugin.json').write_text(json.dumps(spec))
            validator.validate_tool(target, template=True)

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

    def test_dependency_lock_requires_complete_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'template'
            shutil.copytree(ROOT / 'template', target)
            (target / 'requirements.txt').write_text('PyYAML==6.0.3\n')
            (target / 'dependencies.json').write_text('{"yaml":"PyYAML==6.0.3"}')
            lock = target / 'requirements.lock'
            for content in ['PyYAML==6.0.3', 'PyYAML==6.0.3 --hash=sha256:bad',
                            'other==1 --hash=sha256:' + '0' * 64]:
                lock.write_text(content)
                with self.assertRaises(ValueError):
                    validator.validate_tool(target, template=True)
            lock.write_text('PyYAML==6.0.3 --hash=sha256:' + '0' * 64)
            validator.validate_tool(target, template=True)


if __name__ == '__main__':
    unittest.main()
