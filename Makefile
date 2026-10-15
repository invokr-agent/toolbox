.PHONY: test lint-ci contract

test:
	python3 -B validate.py
	python3 -B -m unittest discover -s . -p test_validate.py -v

lint-ci:
	python3 -B validate.py --check-only
	python3 -B -c 'import ast,pathlib; [ast.parse(p.read_text(),filename=str(p)) for p in pathlib.Path(".").rglob("*.py") if ".venv" not in p.parts]'

contract:
	python3 -B contracts/run_invokr.py "$(INVOKR_SOURCE)"
