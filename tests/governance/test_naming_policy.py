import ast

import pytest

from tests.support.governance_common import PROJECT_ROOT, candidate_files


@pytest.mark.governance
def test_test_files_naming_convention():
    """
    Enforce pytest naming convention for test files.

    Policy:
        - All test files must start with 'test_'
        - No file should end with '_test.py'
        - Any non-conforming file constitutes a governance violation
    """
    violations: list[str] = []

    for path in candidate_files():
        rel = path.relative_to(PROJECT_ROOT)
        filename = path.name

        # Defensive: only .py files
        if not filename.endswith(".py"):
            continue

        # Must start with 'test_' — anything else is invalid
        if filename.startswith("test") and not filename.startswith("test_"):
            violations.append(
                f"{rel} → invalid test file name '{filename}' (must start with 'test_')"
            )

        # Must not end with '_test.py' — suffix form is non-compliant
        elif filename.endswith("_test.py") and not filename.startswith("test_"):
            violations.append(
                f"{rel} → invalid test file name '{filename}' "
                "(must start with 'test_', not end with '_test.py')"
            )

    if violations:
        total = len(violations)
        summary_lines = [
            f"\n{total} test file naming violation{'s' if total > 1 else ''} detected — "
            f"all test files must start with 'test_'\n"
        ]

        current_dir = None
        for v in sorted(violations):
            file = v.split(":")[0]
            if file != current_dir:
                summary_lines.append(f"\n{file}")
                current_dir = file
            summary_lines.append(f"  {v}")

        summary = "\n".join(summary_lines)
        assert not violations, summary


@pytest.mark.governance
def test_test_functions_naming_convention():
    """
    Enforce pytest naming convention: test_*, not test*, not *_test.

    Policy:
        - Valid names: test_<something>
        - Invalid patterns:
            - test<Something>  (missing underscore)
            - <something>_test (suffix form)
    """
    violations: list[str] = []

    for path in candidate_files():
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        tree = ast.parse(source, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name

                # Only consider potential pytest test functions
                if name.startswith("test") or name.endswith("_test"):
                    # Rule 1 — Must start with "test_"
                    if name.startswith("test") and not name.startswith("test_"):
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} → invalid test name '{name}' "
                            "(must start with 'test_')"
                        )

                    # Rule 2 — Must not end with "_test"
                    elif name.endswith("_test") and not name.startswith("test_"):
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} → invalid test name '{name}' "
                            "(must start with 'test_', not end with '_test')"
                        )

    if violations:
        total = len(violations)
        summary_lines = [
            f"\n{total} test naming violation{'s' if total > 1 else ''} detected — "
            f"tests must start with 'test_' (not 'test' or '*_test')\n"
        ]

        current_file = None
        for v in sorted(violations):
            file = v.split(":")[0]
            if file != current_file:
                summary_lines.append(f"\n{file}")
                current_file = file
            summary_lines.append(v)

        summary = "\n".join(summary_lines)
        assert not violations, summary
