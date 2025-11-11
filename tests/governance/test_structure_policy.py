import pytest

from tests.support.governance_common import PROJECT_ROOT, candidate_files


@pytest.mark.governance
def test_no_test_files_outside_designated_paths():
    """
    Ensure all test files are under 'tests/' or '<src>/.../tests/'.

    Policy:
        - All test_*.py files must be placed in directories returned by `candidate_files()`
        - Any `test_*.py` outside these locations constitutes a violation.

    Rationale:
        Structural compliance test ensuring that test artifacts remain
        confined to designated governance boundaries.
    """
    all_tests = set(PROJECT_ROOT.rglob("test_*.py"))
    allowed = set(candidate_files())

    ignored_roots = {".venv", ".tox", ".mypy_cache", "__pycache__", ".pytest_cache"}
    all_tests = {
        p for p in all_tests if not any(pr.name in ignored_roots for pr in p.parents)
    }

    # Any test file not returned by candidate_files() is a violation
    violations = sorted(p.relative_to(PROJECT_ROOT) for p in all_tests - allowed)

    if violations:
        total = len(violations)
        summary_lines = [
            f"\n{total} misplaced test file{'s' if total > 1 else ''} detected — "
            f"all test files must be under 'tests/' or '<src>/.../tests/'\n"
        ]

        current_dir = None
        for v in violations:
            parent = v.parent
            if parent != current_dir:
                summary_lines.append(f"\n{parent}/")
                current_dir = parent
            summary_lines.append(f"  - {v}")

        summary = "\n".join(summary_lines)
        assert not violations, summary
