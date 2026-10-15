#!/usr/bin/env python3
"""Run the external contract through Go overlay without editing invokr files."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

KIT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('invokr', type=Path, help='invokr source snapshot at 3ffb0f9')
    args = parser.parse_args()
    source = args.invokr.resolve()
    with tempfile.TemporaryDirectory(prefix='hammer-overlay-') as temp:
        overlay = Path(temp) / 'overlay.json'
        overlay.write_text(json.dumps({'Replace': {
            str(source / 'tools/system/toolbox/hammer_external_test.go'):
            str(KIT / 'contracts/hammer_external_test.go')}}))
        env = {**os.environ, 'GOTOOLCHAIN': 'go1.26.3', 'GOMAXPROCS': '2',
               'HAMMER_TOOLS': str(KIT / 'tools'), 'INVOKR_E2E_LIVE': ''}
        subprocess.run(['go', 'test', '-overlay', str(overlay), '-count=1', '-v',
                        './tools/system/toolbox', '-run', '^TestHammer'],
                       cwd=source, env=env, check=True, timeout=300)


if __name__ == '__main__':
    main()
