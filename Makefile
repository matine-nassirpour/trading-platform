# Makefile — Windows (cmd) + Poetry
# Default shell: cmd.exe. PowerShell is called explicitly via $(PS).

SHELL := cmd.exe
.SHELLFLAGS := /V:ON /E:ON /C

PKG := quantum
SRC := src/$(PKG)
PS  := powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command

.DEFAULT_GOAL := help

.PHONY: help fmt-check fmt typecheck pre-commit test audit clean check-ci ui

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

clean: ## Remove build/test caches
	-@$(PS) "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .pytest_cache,.mypy_cache,.ruff_cache,htmlcov,dist,build,*.egg-info,.coverage,coverage.xml,test-results"

check-ci: pre-commit test ## Run CI-equivalent checks locally
	@echo "All CI checks completed"

ui: ## Launch Streamlit
	poetry run streamlit run src/quantum/ui/streamlit_app.py --server.headless true
