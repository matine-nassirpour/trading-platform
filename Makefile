# Makefile — Windows (cmd) + Poetry
# Default shell: cmd.exe. PowerShell is called explicitly via $(PS).

SHELL := cmd.exe
.SHELLFLAGS := /V:ON /E:ON /C

PKG := quantum
SRC := src/$(PKG)
PS  := powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command

.DEFAULT_GOAL := help

.PHONY: help fmt-check fmt typecheck pre-commit test audit clean contracts check-ci ui tree log-schema

help:
	@$(PS) "Write-Host 'Targets:'; Get-Content '$(MAKEFILE_LIST)' | Select-String '^\S+:.*?## ' | ForEach-Object { $$t = $$_.Line -replace ':.*',''; $$d = ($$_.Line -split '## ')[1]; '{0,-18} {1}' -f $$t, $$d } | Sort-Object"

fmt-check: ## Check the format (without modifying)
	poetry run ruff check .
	poetry run ruff format --check .
	poetry run black --check .

fmt: ## Format & fixe (ruff + black)
	poetry run ruff check --fix .
	poetry run ruff format .
	poetry run black .

typecheck: ## Strict typing (mypy)
	poetry run mypy $(SRC)

test: ## Run tests with coverage (HTML, XML, JUnit)
	@echo "Running tests + Coverage"
	@$(PS) "New-Item -ItemType Directory -Force -Path 'test-results','htmlcov' | Out-Null"
	@poetry run pytest --rootdir=. tests\
		--cov=$(PKG) \
		--cov-report=term-missing \
		--cov-report=xml:coverage.xml \
		--cov-report=html:htmlcov \
		--junitxml=test-results/results.xml \
		--disable-warnings -v
#		--cov-fail-under=90

pre-commit: ## Run pre-commit hooks on the entire repo
	@echo "Running pre-commit hooks"
	@poetry run pre-commit run --all-files --show-diff-on-failure

audit: ## Check pyproject/lock and vulnerabilities
	poetry check
	poetry run pip-audit -l || (echo "pip-audit found issues" & exit /b 1)

contracts: ## Enforce architecture contracts (import-linter)
	@echo "Checking architecture contracts (import-linter)"
	@set PYTHONPATH=src;. && poetry run lint-imports

clean: ## Remove build/test caches
	-@$(PS) "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .pytest_cache,.mypy_cache,.ruff_cache,htmlcov,dist,build,*.egg-info,.coverage,coverage.xml,test-results"

check-ci: pre-commit test ## Run CI-equivalent checks locally
	@echo "All CI checks completed"

ui: ## Launch Streamlit
	@set PYTHONPATH=src;. && poetry run streamlit run apps/streamlit/pages/observability.py --server.headless true

tree: ## Print repo tree into docs/architecture/tree.txt
	@$(PS) "New-Item -ItemType Directory -Force -Path 'docs/architecture' | Out-Null"
	@poetry run python scripts/print_tree.py . --output docs/architecture/tree.txt --respect-gitignore --max-depth 10
	@echo "Done. Output: docs/architecture/tree.txt"

log-schema: ## Generate the canonical JSON schema for LogPayloadV1
	@echo "Generating LogPayloadV1 JSON schema..."
	@$(PS) "New-Item -ItemType Directory -Force -Path 'docs/observability' | Out-Null"
	@set PYTHONPATH=src;. && poetry run python scripts/generate_log_schema.py
	@echo "Schema generated at docs/observability/log_schema_v1.json"
