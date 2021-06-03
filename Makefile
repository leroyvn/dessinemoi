ifeq ($(OS), Windows_NT)
	PLATFORM := win-64
else
	uname := $(shell sh -c 'uname 2>/dev/null || echo unknown')
	ifeq ($(uname), Darwin)
		PLATFORM := osx-64
	else ifeq ($(uname), Linux)
		PLATFORM := linux-64
	else
		@echo "Unsupported platform"
		exit 1
	endif
endif

all:
	@echo "Detected platform: $(PLATFORM)"

# -- Dependency management with Conda ------------------------------------------

# Lock conda dependencies
conda-lock:
	conda-lock --file pyproject.toml \
	    --filename-template "requirements/environment-{platform}.lock" \
	    -p $(PLATFORM)

conda-lock-all:
	conda-lock --file pyproject.toml \
	    --filename-template "requirements/environment-{platform}.lock"

# Initialise development environment
conda-init:
	conda update --file requirements/environment-$(PLATFORM).lock
	python setup.py develop --no-deps

conda-update: conda-lock-all conda-init

.PHONY: conda-lock conda-lock-all conda-init conda-update

# -- Testing -------------------------------------------------------------------

test:
	pytest --cov=src --doctest-glob="*.rst" docs tests

.PHONY: test

# -- Documentation -------------------------------------------------------------

docs:
	make -C docs html

.PHONY: docs

# -- Build ---------------------------------------------------------------------

build:
	poetry build

dist-clean:
	rm -rf dist

publish: build
	poetry publish --dry-run

.PHONY: build dist-clean publish
