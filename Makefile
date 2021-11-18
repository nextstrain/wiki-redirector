SHELL := bash -euo pipefail

.PHONY: venv requirements.txt

venv:
	rm -rf .venv
	python3.6 -m venv .venv
	.venv/bin/pip install --upgrade pip setuptools wheel pip-tools
	.venv/bin/pip install -r requirements.txt

requirements.txt: requirements.in
	.venv/bin/pip-compile --generate-hashes --reuse-hashes
