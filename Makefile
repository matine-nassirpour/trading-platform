# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Makefile — Quantum Trading Platform (Windows + Poetry)                     │
# │ Purpose: unified software assurance and build orchestration                │
# ╰────────────────────────────────────────────────────────────────────────────╯
SHELL := cmd.exe
.SHELLFLAGS := /V:ON /E:ON /C

PKG := quantum
SRC := src/$(PKG)
PS  := powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command

.DEFAULT_GOAL := help

.PHONY: help fmt-check fmt lint typecheck bandit pre-commit test audit contracts check-ci clean ui tree log-schema


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Help                                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
help:
	@$(PS) "Write-Host 'Targets:'; Get-Content '$(MAKEFILE_LIST)' | Select-String '^\S+:.*?## ' | ForEach-Object { $$t = $$_.Line -replace ':.*',''; $$d = ($$_.Line -split '## ')[1]; '{0,-20} {1}' -f $$t, $$d } | Sort-Object"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Code Quality & Formatting                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
fmt-check: ## Check formatting and style compliance (Ruff + Black)
	@poetry run ruff check . --config assurance/quality/ruff.toml
	@poetry run black --check . --config assurance/quality/black.toml

fmt: ## Auto-format and fix style issues (Ruff + Black)
	@poetry run ruff check --fix . --config assurance/quality/ruff.toml
	@poetry run black . --config assurance/quality/black.toml

lint: ## Comprehensive linting (Ruff + Isort)
	@poetry run ruff check . --config assurance/quality/ruff.toml
	@poetry run isort . --check-only --settings-file assurance/quality/isort.cfg


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Typing, Security, and Pre-commit                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
typecheck: ## Strict static typing (Mypy)
	@poetry run mypy --config-file assurance/quality/mypy.ini $(SRC)

bandit: ## Static security analysis (Bandit)
	@poetry run bandit --ini assurance/security/bandit.ini

pre-commit: ## Run all pre-commit hooks
	@echo "Running pre-commit hooks..."
	@poetry run pre-commit run --all-files --show-diff-on-failure --config assurance/quality/.pre-commit-config.yaml


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Tests & Quality Gates                                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
test: ## Run test suite with full coverage
	@echo "Running tests with coverage..."
	@poetry run pytest -v

verify-coverage: ## Run full coverage verification and enforce thresholds
	@echo "Running full test suite with coverage..."
	@$(MAKE) test
	@echo "Verifying coverage thresholds..."
	@poetry run python scripts/verify_coverage.py || (echo "[WARNING] Coverage verification failed."; exit 1)
	@echo "Coverage verification completed successfully."

assurance-report: ## Generate unified HTML Assurance Report
	@echo "Generating unified Assurance Report..."
	@poetry run python scripts/generate_assurance_report.py

audit: ## Dependency and vulnerability audit
	@poetry check
	@poetry run pip-audit -l || (echo "pip-audit found issues" & exit /b 1)

contracts: ## Enforce architectural boundaries (Import Linter)
	@echo "Checking architecture contracts..."
	@set PYTHONPATH=src;. && poetry run lint-imports --config assurance/architecture/.importlinter

check-ci: ## Run full CI-equivalent validation suite
	@echo "Running full CI-equivalent checks..."
	@$(MAKE) pre-commit
	@$(MAKE) test
	@echo "All CI checks passed successfully."


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Utilities                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
clean: ## Remove build/test artifacts and caches
	-@$(PS) "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .pytest_cache,.mypy_cache,.ruff_cache,.isort_cache,htmlcov,dist,build,*.egg-info,.coverage,coverage.xml,test-results,build/coverage"

ui: ## Launch Streamlit
	@set PYTHONPATH=src;. && poetry run streamlit run apps/streamlit/pages/observability_page.py --server.headless true

tree: ## Generate documentation of directory structure
	@$(PS) "New-Item -ItemType Directory -Force -Path 'docs/architecture' | Out-Null"
	@poetry run python scripts/print_tree.py . --output docs/architecture/tree.txt --respect-gitignore --max-depth 10
	@echo "Architecture tree generated: docs/architecture/tree.txt"

log-schema: ## Generate canonical JSON schema for LogPayloadV1
	@echo "Generating LogPayloadV1 schema..."
	@$(PS) "New-Item -ItemType Directory -Force -Path 'docs/observability' | Out-Null"
	@set PYTHONPATH=src;. && poetry run python scripts/generate_log_schema.py
	@echo "Schema generated at docs/observability/log_schema_v1.json"
