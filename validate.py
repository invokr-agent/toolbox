#!/usr/bin/env python3
"""Offline contract gate. No plugin imports and no package installation."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def check(value, rule, path='$'):
    """Validate only the explicitly supported JSON Schema subset; fail closed."""
    supported = {'type', 'properties', 'required', 'additionalProperties', 'items',
                 'enum', 'const', 'minimum', 'maximum', 'minLength', 'maxLength',
                 'minItems', 'maxItems', 'pattern', 'description', '$schema', 'title'}
    if set(rule) - supported:
        raise ValueError(f'{path}: unsupported schema keywords')
    types = {'object': (dict,), 'array': (list,), 'string': (str,),
             'integer': (int,), 'number': (int, float), 'boolean': (bool,)}
    if 'type' in rule and type(value) not in types[rule['type']]:
        raise ValueError(f'{path}: expected {rule["type"]}')
    if 'const' in rule and json.dumps(value, sort_keys=True) != json.dumps(rule['const'], sort_keys=True):
        raise ValueError(f'{path}: constant differs')
    if 'enum' in rule and value not in rule['enum']:
        raise ValueError(f'{path}: not in enum')
    if isinstance(value, dict):
        if set(rule.get('required', [])) - value.keys():
            raise ValueError(f'{path}: missing required fields')
        props = rule.get('properties', {})
        extra = rule.get('additionalProperties', True)
        if extra is False and value.keys() - props.keys():
            raise ValueError(f'{path}: unknown fields')
        for key, item in value.items():
            child = props.get(key, extra if isinstance(extra, dict) else {})
            check(item, child, path + '.' + key)
    if isinstance(value, list):
        if not rule.get('minItems', 0) <= len(value) <= rule.get('maxItems', sys.maxsize):
            raise ValueError(f'{path}: array size')
        for item in value:
            check(item, rule.get('items', {}), path + '[]')
    if isinstance(value, str):
        if not rule.get('minLength', 0) <= len(value) <= rule.get('maxLength', sys.maxsize):
            raise ValueError(f'{path}: string size')
        if 'pattern' in rule and re.fullmatch(rule['pattern'], value) is None:
            raise ValueError(f'{path}: pattern mismatch')
    if type(value) in (int, float):
        if not rule.get('minimum', -1e100) <= value <= rule.get('maximum', 1e100):
            raise ValueError(f'{path}: number outside range')


def validate_tool(directory, template=False):
    if directory.is_symlink():
        raise ValueError(f'{directory}: symlink directory forbidden')
    for file in directory.rglob('*'):
        if '.venv' in file.relative_to(directory).parts[:-1]:
            continue
        if file.is_symlink():
            raise ValueError(f'{file}: symlink forbidden')
    for name in ('plugin.json', 'main.py', 'requirements.txt', 'README.md', 'test_main.py'):
        if not (directory / name).is_file():
            raise ValueError(f'{directory}: missing {name}')
    spec = json.loads((directory / 'plugin.json').read_text())
    check(spec, json.loads((ROOT / 'contracts/plugin.schema.json').read_text()))
    network = spec['capabilities']['network']
    if network != ('network' in spec):
        raise ValueError('network tools require an explicit hostname allowlist')
    if spec['limits']['timeout_seconds'] not in ((15, 60) if network else (3,)):
        raise ValueError('timeout must match network/offline profile')
    if spec['name'] != ('template' if template else directory.name):
        raise ValueError(f'{directory}: name/directory mismatch')
    parameters = spec['parameters']
    if set(parameters['required']) - parameters['properties'].keys():
        raise ValueError('required references unknown arguments')
    for name, prop in parameters['properties'].items():
        if 'default' in prop:
            check(prop['default'], {k: v for k, v in prop.items() if k != 'default'}, name)
    example = json.loads(spec['example'])
    if set(example) != {'name', 'arguments'} or example['name'] != spec['name']:
        raise ValueError('invalid example envelope')
    example_schema = json.loads(json.dumps(parameters))
    for prop in example_schema['properties'].values():
        prop.pop('default', None)
    check(example['arguments'], example_schema)
    pins = []
    for line in (directory / 'requirements.txt').read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            if not re.fullmatch(r'[A-Za-z0-9_.-]+==[A-Za-z0-9_.+!-]+', line):
                raise ValueError('requirements must be exact registry pins')
            pins.append(line)
    modules = {}
    if pins:
        metadata = directory / 'dependencies.json'
        lock = directory / 'requirements.lock'
        if not metadata.is_file() or not lock.is_file():
            raise ValueError('dependencies need an import map and complete SHA-256 lock')
        modules = json.loads(metadata.read_text())
        if not isinstance(modules, dict) or not all(isinstance(k, str) and v in pins for k, v in modules.items()):
            raise ValueError('dependency import map must reference exact requirement pins')
        locked = {}
        for line in lock.read_text().splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            fields = line.split()
            if len(fields) < 2 or any(not re.fullmatch(r'--hash=sha256:[0-9a-f]{64}', h) for h in fields[1:]):
                raise ValueError('every locked artifact needs SHA-256 hashes')
            if fields[0] in locked:
                raise ValueError('duplicate lock entry')
            locked[fields[0]] = fields[1:]
        if set(locked) != set(pins):
            raise ValueError('requirements must declare the complete locked dependency closure')
    for file in directory.glob('*.py'):
        tree = ast.parse(file.read_text(), filename=str(file))
        if file.name == 'test_main.py' and not any(
                isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
                for node in ast.walk(tree)):
            raise ValueError('test_main.py must contain tests')
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    raise ValueError(f'{file}: relative imports forbidden')
                names = [node.module or '']
            else:
                continue
            if any(name.split('.')[0] not in sys.stdlib_module_names | modules.keys() for name in names):
                raise ValueError(f'{file}: non-stdlib or cross-tool import')
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    tool_root = ROOT / 'tools'
    directories = [ROOT / 'template'] + (sorted(tool_root.iterdir()) if tool_root.exists() else [])
    names = set()
    for directory in directories:
        if not directory.is_dir():
            raise ValueError(f'unexpected entry: {directory}')
        spec = validate_tool(directory, directory.name == 'template')
        if spec['name'] in names:
            raise ValueError('duplicate tool name')
        names.add(spec['name'])
        if not args.check_only:
            python = directory / '.venv/bin/python'
            subprocess.run([str(python) if python.exists() else sys.executable, '-I', '-B', str(directory / 'test_main.py')],
                           check=True, cwd=directory, timeout=40,
                           env={'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1'})
        print('PASS', spec['name'], flush=True)
    print(f'Validated {len(directories)-1} tools plus template')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        sys.exit(str(exc))
