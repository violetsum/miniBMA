.PHONY: test

test:
	PYTHONPATH=src/ python -m pytest -vs tests/
