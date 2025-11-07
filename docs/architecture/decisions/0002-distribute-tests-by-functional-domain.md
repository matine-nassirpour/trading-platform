# ADR 0002 – Distribute Tests by Functional Domain

> **Status:** Accepted <br>
> **Date:** 2025-11-07 <br>

---

## 1. Context
The current testing structure uses a centralized `tests/` directory at the repository root, containing `unit/`, `integration/`, and `e2e/` test suites.

While this approach is common, it creates long-term limitations in traceability, maintainability, and modular scaling—especially in a system built under strict **Clean Architecture** and **high-assurance engineering standards** (DO-178C, ISO 26262, IEC 62304, NASA-STD-8739.8).

In such contexts, verification artifacts must maintain **direct traceability** to the software items they validate. Tests should therefore reside within the same architectural boundary and version control context as their corresponding production code.

---

## 2. Decision
Tests will be **co-located within their respective functional domains**, under dedicated `tests/` directories that mirror the production package hierarchy.

> **Subdomain tests isolation principle**
>
> Subdomain-level `tests/` directories (e.g. `config/tests/`, `observability/tests/`) are **reserved for local unit tests only** — verifying the subdomain’s internal logic in isolation.
>
> 🚫 No integration, cross-validation, performance, or end-to-end tests belong there.
> It is a closed, pure, and conceptually consistent testing environment.

The root `tests/` directory will remain as a **global test harness**, hosting:
- end-to-end (E2E) and system integration tests,
- cross-domain fixtures (`conftest.py`),
- global test governance (coverage, CI configuration, reports).

---

## 3. Rationale
This structure provides:

- **Traceability** — each test is co-located with its code, ensuring bidirectional traceability (DO-178C §6.4.1, ISO 26262 §9.4).
- **Maintainability** — modular updates do not disrupt unrelated test structures (ISO/IEC 25010).
- **Scalability** — each domain becomes an independently verifiable “unit” of assurance.
- **Observability alignment** — local tests can validate metrics, logs, and health probes within their own domain context.
- **Cognitive coherence** — developers can navigate directly between code and tests, improving verification efficiency.

---

## 4. Consequences
- Developers must add tests under the corresponding domain subdirectory.
- Continuous Integration (CI) and coverage tools will be reconfigured to include both `src/` and root-level `tests/` paths.
- The global `tests/` directory becomes optional for module-specific work but remains mandatory for cross-cutting validation.
