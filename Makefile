SHELL := bash -euo pipefail

.PHONY: venv requirements.txt

venv:
	devel/check-python-version
	rm -rf .venv
	python -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools wheel pip-tools
	.venv/bin/pip install -r requirements.txt

requirements.txt: requirements.in
	devel/check-python-version
	.venv/bin/pip-compile --generate-hashes --reuse-hashes
