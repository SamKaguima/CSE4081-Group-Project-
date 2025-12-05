# Cross-platform Makefile for Haar-Rice compressor
# Targets: help, venv, install, test, demo, clean, clean-venv

# Defaults can be overridden: make test PYTHON=python3
PYTHON ?= python
VENV ?= .venv

ifeq ($(OS),Windows_NT)
	VENV_PY := $(VENV)/Scripts/python.exe
	VENV_PIP := $(VENV)/Scripts/pip.exe
else
	VENV_PY := $(VENV)/bin/python
	VENV_PIP := $(VENV)/bin/pip
endif

INPUT ?= test_images/original_image.ext
COMPRESSED ?= test_out/compressed_image.hrc
OUTPUT ?= test_out/reconstructed_image.ext

.PHONY: help venv install test demo clean clean-venv

help:
	@echo "Common targets:"
	@echo "  make venv          - create virtual env in $(VENV)"
	@echo "  make install       - install dependencies (uses requirements.txt if present)"
	@echo "  make test          - run pytest in quiet mode"
	@echo "  make demo          - run demo_metrics.py (override INPUT/COMPRESSED/OUTPUT)"
	@echo "  make clean         - remove __pycache__, .pytest_cache, coverage files"
	@echo "  make clean-venv    - remove the virtual environment"

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	@if [ -f requirements.txt ]; then \
		"$(VENV_PIP)" install -r requirements.txt; \
	else \
		"$(VENV_PIP)" install numpy Pillow pytest; \
	fi

test: install
	"$(VENV_PY)" -m pytest -q

demo: install
	"$(VENV_PY)" demo_metrics.py $(INPUT) $(COMPRESSED) $(OUTPUT)

clean:
	@"$(PYTHON)" - <<'PY'
import shutil, os
paths = [
    '.pytest_cache',
    '.coverage',
    'coverage.xml',
]
for root, dirs, files in os.walk('.', topdown=False):
    for d in dirs:
        if d == '__pycache__':
            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
    for f in files:
        if f.endswith(('.pyc', '.pyo')):
            os.remove(os.path.join(root, f))
for p in paths:
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
    elif os.path.isfile(p):
        os.remove(p)
PY

clean-venv:
	@if [ -d "$(VENV)" ]; then rm -rf "$(VENV)"; fi
