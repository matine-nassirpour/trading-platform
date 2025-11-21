# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Makefile — Quantum Trading Platform (Windows + Poetry)                     │
# │ Purpose: unified software assurance and build orchestration                │
# ╰────────────────────────────────────────────────────────────────────────────╯
SHELL := powershell.exe
.SHELLFLAGS := -NoLogo -NoProfile -ExecutionPolicy Bypass -Command

PKG := quantum
SRC := src/$(PKG)

.DEFAULT_GOAL := help

.PHONY: help fmt-check fmt lint typecheck bandit pre-commit test verify-coverage assurance-report audit contracts check-ci clean ui tree log-schema


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Help                                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
help: ## Display structured list of available Make targets
	@Write-Host "╭──────────────────────────────────────────────────────────────────────────────╮"
	@Write-Host "│                  QUANTUM PLATFORM — MAKE COMMANDS OVERVIEW                   │"
	@Write-Host "╰──────────────────────────────────────────────────────────────────────────────╯"
	@(Get-Content '$(MAKEFILE_LIST)' | Select-String '^\S+:.*?## ' | ForEach-Object {$$t = ($$_.Line -replace ':.*',''); $$d = ($$_.Line -split '## ')[1]; Write-Host ("  {0,-20} {1}" -f $$t, $$d) -ForegroundColor Gray})
	@Write-Host ""


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
	@poetry run bandit -r $(SRC) -c assurance/security/bandit.yaml

pre-commit: ## Run all pre-commit hooks
	@Write-Host "`n▶ Running pre-commit hooks...`n" -ForegroundColor Cyan
	@poetry run pre-commit run --all-files --show-diff-on-failure --config assurance/quality/.pre-commit-config.yaml


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Tests & Quality Gates                                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
test: ## Run test suite with full coverage
	@Write-Host "`n▶ Running tests with coverage...`n" -ForegroundColor Cyan
	@poetry run pytest -v

verify-coverage: ## Run full coverage verification and enforce thresholds
	@Write-Host "Running full test suite with coverage..."
	@$(MAKE) test
	@Write-Host "Verifying coverage thresholds..."
	@poetry run python scripts/verify_coverage.py; if ($$LASTEXITCODE -ne 0) { Write-Host "[WARNING] Coverage verification failed."; exit 1 }
	@Write-Host "Coverage verification completed successfully."

assurance-report: ## Generate unified HTML Assurance Report
	@Write-Host "Generating unified Assurance Report..."
	@poetry run python scripts/generate_assurance_report.py

audit: ## Dependency and vulnerability audit
	@poetry check
	@poetry run pip-audit -l; if ($$LASTEXITCODE -ne 0) { Write-Host "pip-audit found issues"; exit 1 }

contracts: ## Enforce architectural boundaries (Import Linter)
	@Write-Host "Checking architecture contracts..."
	@poetry run lint-imports --config assurance/architecture/.importlinter

check-ci: ## Run full CI-equivalent validation suite
	@Write-Host "`n╭──────────────────────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
	@Write-Host "│ CI VALIDATION SUITE — FULL PIPELINE EXECUTION                                │ " -ForegroundColor Cyan
	@Write-Host "╰──────────────────────────────────────────────────────────────────────────────╯`n" -ForegroundColor Cyan
	@$(MAKE) pre-commit
	@$(MAKE) test
	@Write-Host "`n✔ All CI checks passed successfully.`n" -ForegroundColor Green


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Utilities                                                                  │
# ╰────────────────────────────────────────────────────────────────────────────╯
clean: ## Remove build/test artifacts and caches
	-@Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .pytest_cache,.mypy_cache,.ruff_cache,.isort_cache,htmlcov,dist,build,*.egg-info,.coverage,coverage.xml,test-results,build/coverage

ui: ## Launch Streamlit
	@$$env:PYTHONPATH = 'src;.'; poetry run streamlit run apps/streamlit/pages/observability_page.py --server.headless true

tree: ## Generate documentation of directory structure
	@New-Item -ItemType Directory -Force -Path 'docs/architecture' | Out-Null
	@Write-Host "`n▶ Generating architecture directory tree ..." -ForegroundColor Cyan
	@poetry run python scripts/print_tree.py . --output docs/architecture/tree.txt --respect-gitignore --max-depth 10
	@Write-Host "`n✔ Architecture tree generated: docs/architecture/tree.txt`n"  -ForegroundColor Green

log-schema: ## Generate canonical JSON schema for LogPayload
	@Write-Host "Generating LogPayloadV1 schema..."
	@New-Item -ItemType Directory -Force -Path 'docs/observability' | Out-Null
	@$$env:PYTHONPATH = 'src;.'; poetry run python scripts/generate_log_schema.py
	@Write-Host "Schema generated at docs/observability/log_schema_v1.json"
