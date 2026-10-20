VENV = .venv
PY = $(VENV)/bin/python

.DEFAULT_GOAL := help

MSG = \033[1m\033[36m>>>\033[0m
NO = \033[0m

.PHONY: help setup envs-sync test test-toolchain test-functional lint clean increment_version

## Print the list of available commands
help:
	@python3 -c "import re,sys; t=open('$(lastword $(MAKEFILE_LIST))').read(); m=re.findall(r'\n## ([^\n]+)\n(?!\.PHONY)([a-zA-Z_.][a-zA-Z0-9_.-]*):', t); print('\nAvailable rules:\n'); print('\n'.join(['\033[36m{:18}\033[0m{}'.format(*reversed(x)) for x in sorted(m, key=lambda x: x[1])]))"

## Create .venv from pyproject.toml with the dev dependencies
setup:
	uv venv --allow-existing $(VENV)
	uv pip install --python $(PY) -r pyproject.toml --extra dev

## Copy the master environment installers into the template
envs-sync:
	cp envs/firmware_env.py envs/firmware-avr.py envs/firmware-esp.py envs/firmware-stm32.py template/resources/envs/
	chmod +x template/resources/envs/firmware-avr.py template/resources/envs/firmware-esp.py template/resources/envs/firmware-stm32.py

## Increment the patch version in pyproject.toml
increment_version:
	@current=$$(grep -oP 'version = "\K[0-9]+\.[0-9]+\.[0-9]+' pyproject.toml); \
	major=$$(echo $$current | cut -d. -f1); \
	minor=$$(echo $$current | cut -d. -f2); \
	patch=$$(echo $$current | cut -d. -f3); \
	new_patch=$$((patch + 1)); \
	new_version="$$major.$$minor.$$new_patch"; \
	sed -i "s/version = \"$$current\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "Version bumped: $$current -> $$new_version"

## Render the template matrix and run every fast test
test:
	$(PY) -m pytest -q

## Also build the rendered AVR project and run its simulator tests
test-toolchain:
	$(PY) -m pytest -q -m toolchain

## Render, build and simulate the five functional projects; run a real copier update
test-functional:
	RUN_FUNCTIONAL=1 $(PY) -m pytest -q tests/test_builds.py tests/test_update_functional.py

## Lint the template scripts and tests
lint:
	$(PY) -m ruff check scripts tests

## Remove caches and rendered scratch projects
clean:
	@rm -rf .pytest_cache .ruff_cache tmp manual_test
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
