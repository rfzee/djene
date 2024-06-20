# --- Project Configuration ---
PROJECT_NAME = $(shell grep '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/')
PROJECT_VERSION = $(shell grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
PROJECT_PATH ?= .

# --- Clean Targets ---

CLEAN_DIRS := .ruff_cache .pytest_cache reports build logs
CLEAN_FILES := $(shell find . -type f \( -name '*.py[co]' -o -name '*~' -o -name '.*\~' -o -name '*.swp' \))

# --- Phony Targets ---

.PHONY: help install-deps update-deps lint lintfix test vtest format clean docs rundocs serve release txtarchive archive

# --- Help Target ---
help:  ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# --- Installation & Dependency Management ---

install-deps: ## Install project dependencies
	poetry install

update-deps: ## Update project dependencies
	poetry update

# --- Code Quality ---

lint: ## Check code style with Ruff
	poetry run ruff check $(PROJECT_PATH)

lintfix: ## Automatically fix code style issues with Ruff
	poetry run ruff check $(PROJECT_PATH) --fix

format: ## Format code with Ruff
	poetry run ruff format $(PROJECT_PATH)

# --- Testing ---

test: ## Run tests with coverage
	poetry run pytest -v --cov=$(PROJECT_PATH) --cov-report=xml

vtest: ## Run tests in verbose mode
	poetry run pytest -vvv

# --- Documentation ---

docs: ## Generate documentation (adjust to your documentation tool)
	$(MAKE) -C docs html  # Assuming Sphinx, change if needed

rundocs: docs ## Serve documentation locally
	$(MAKE) -C docs serve  # Assuming Sphinx

# --- Building & Release ---

release: ## Build a distributable package and publish to PyPI
	poetry build
	poetry publish  # Requires appropriate credentials

# --- Cleaning ---

clean: ## Clean project artifacts and temporary files
	@rm -rf $(CLEAN_DIRS)
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete
	@find . -type d -name '.DS_Store' -delete
	@rm -rf .pytest_cache


# --- Project Archive ---
txtarchive: clean ## Create a text archive of the project files
	mkdir -p tmp
	find $(PROJECT_PATH) -type f \
		! -path './.venv*' \
		! -path './.git*' \
		! -path './tmp*' \
		! -name 'poetry.lock' \
		! -name '.DS_Store' \
		! -name 'Makefile' \
		! -name 'CHANGELOG.md' \
		! -name 'LICENSE' \
		-exec awk ' \
			BEGIN {FS = "\n"; RS = ""; OFS = "\n"} \
			{printf "\n### file: %s\n%s\n", FILENAME, $$0}' {} + > tmp/$(PROJECT_NAME)-$(PROJECT_VERSION).txt

archive: txtarchive  ## Create a ZIP archive of the project code (project-name-version.zip)
	@mkdir -p tmp
	@zip -r tmp/$(PROJECT_NAME)-$(PROJECT_VERSION).zip $(PROJECT_PATH) \
		-x "*.git*" \
		-x "*.venv*" \
		-x "tmp/*" \
		-x "poetry.lock" \
		-x ".DS_Store" \
		-x "Makefile" \
		-x 'CHANGELOG.md' \
		-x 'LICENSE'
