SHELL := /bin/bash
VENV ?= .venv
PYTHON ?= python3
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

OUT_DIR ?= $(HOME)/.config/cliamp/playlists
IFACE ?=
PER_LIST ?= 50
CANDIDATES ?= 120

.DEFAULT_GOAL := help
.PHONY: help venv install genres russia all check prune compile clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

$(PY):
	$(PYTHON) -m venv $(VENV)

venv: $(PY) ## Create the virtualenv

$(VENV)/.installed: requirements.txt | $(PY)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@touch $@

install: $(VENV)/.installed ## Install dependencies (creates the venv)

genres: install ## Build worldwide genre playlists
	$(PY) build_genres.py --out-dir "$(OUT_DIR)" $(if $(IFACE),--iface $(IFACE)) --per-list $(PER_LIST) --candidates $(CANDIDATES)

russia: install ## Build Russian per-genre playlists
	$(PY) build_russia_genres.py --out-dir "$(OUT_DIR)" $(if $(IFACE),--iface $(IFACE)) --per-list $(PER_LIST) --candidates $(CANDIDATES)

all: genres russia ## Build both playlist sets

check: install ## Verify streams in existing playlists
	$(PY) verify_playlists.py --dir "$(OUT_DIR)" $(if $(IFACE),--iface $(IFACE))

prune: install ## Remove dead streams from existing playlists
	$(PY) verify_playlists.py --dir "$(OUT_DIR)" $(if $(IFACE),--iface $(IFACE)) --prune

compile: ## Syntax-check the scripts
	$(PYTHON) -m py_compile build_genres.py build_russia_genres.py verify_playlists.py radio_playlists/*.py

clean: ## Remove caches and the virtualenv
	rm -rf __pycache__ radio_playlists/__pycache__ $(VENV)
