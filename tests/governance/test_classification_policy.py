"""
Enforce explicit pytest classification marks on all test functions.
Compliant with Clean Architecture & Certifiable Software Standards.
"""

import ast

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src" / "quantum"
TEST_DIR = PROJECT_ROOT / "tests"

VALID_MARKS = {"unit", "integration", "e2e", "internal"}
IGNORED_MARKS = {
    "parametrize",
    "skip",
    "skipif",
    "xfail",
    "usefixtures",
    "filterwarnings",
}


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _collect_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    """
    Identify aliases used for 'pytest' and 'pytest.mark' imports.

    Returns:
        - pytest_aliases: all names referring to the pytest module (e.g., {'pytest', 'p'})
        - mark_aliases: all names referring to 'pytest.mark' (e.g., {'mark', 'm'})
    """
    pytest_aliases, mark_aliases = {"pytest"}, {"mark"}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == "pytest" and n.asname:
                    pytest_aliases.add(n.asname)
        elif isinstance(node, ast.ImportFrom) and node.module == "pytest":
            for n in node.names:
                if n.name == "mark":
                    mark_aliases.add(n.asname or "mark")
    return pytest_aliases, mark_aliases


def _is_classification_mark(
    node: ast.AST, *, pytest_aliases: set[str], mark_aliases: set[str]
) -> str | None:
    """
    Accepts:
      - <pytest_alias>.mark.<name>[()]
      - <mark_alias>.<name>[()]

    Ignores non-classification marks (parametrize/skip/...).

    Returns:
         One of the valid marker if decorator is a classification mark.
    """
    target = node.func if isinstance(node, ast.Call) else node

    # <pytest_alias>.mark.<name>
    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Attribute):
        base = getattr(target.value.value, "id", None)
        if base in pytest_aliases and target.value.attr == "mark":
            mark = target.attr
            if mark in VALID_MARKS:
                return mark
            if mark in IGNORED_MARKS:
                return None

    # <mark_alias>.<name>
    if (
        isinstance(target, ast.Attribute)
        and getattr(target.value, "id", None) in mark_aliases
    ):
        mark = target.attr
        if mark in VALID_MARKS:
            return mark

    return None


def _decorator_marks(
    decorators: list[ast.expr], *, pytest_aliases: set[str], mark_aliases: set[str]
) -> set[str]:
    """
    Ensures:
        - Only valid classification marks are returned.
        - Non-classification marks (parametrize/skip/xfail/...) are ignored.
        - The function is deterministic and free of side effects.

    Args:
        decorators:
            List of AST decorator nodes applied to a function or class definition.
        pytest_aliases:
            Set of all names used to reference the 'pytest' module (e.g., {'pytest', 'p'}).
        mark_aliases:
            Set of all names used to reference 'pytest.mark' (e.g., {'mark', 'm'}).

    Returns:
        set[str]:
            The subset of classification marks found among the decorators.
            Each element is one of {'unit', 'integration', 'e2e', 'internal'}.
    """
    return {
        m
        for d in decorators
        if (
            m := _is_classification_mark(
                d, pytest_aliases=pytest_aliases, mark_aliases=mark_aliases
            )
        )
    }


def _iter_tests(tree: ast.Module, *, pytest_aliases: set[str], mark_aliases: set[str]):
    """
    Yield (lineno, display_name, marks) for every test function or method.
    This ignores module-level 'pytestmark' on purpose (policy: explicit per function).
    """
    for node in tree.body:
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef)
        ) and node.name.startswith("test_"):
            yield node.lineno, node.name, _decorator_marks(
                node.decorator_list,
                pytest_aliases=pytest_aliases,
                mark_aliases=mark_aliases,
            )
        if isinstance(node, ast.ClassDef):
            class_marks = _decorator_marks(
                node.decorator_list,
                pytest_aliases=pytest_aliases,
                mark_aliases=mark_aliases,
            )
            for sub in node.body:
                if isinstance(
                    sub, (ast.FunctionDef, ast.AsyncFunctionDef)
                ) and sub.name.startswith("test_"):
                    marks = (
                        _decorator_marks(
                            sub.decorator_list,
                            pytest_aliases=pytest_aliases,
                            mark_aliases=mark_aliases,
                        )
                        | class_marks
                    )
                    yield sub.lineno, f"{node.name}.{sub.name}", marks


def _candidate_files() -> list[Path]:
    """
    Scan both roots:
      - top-level tests/**/test_*.py   (e.g., tests/integration/...)
      - src/quantum/**/tests/test_*.py (module-local unit tests)
    """
    files = list(TEST_DIR.rglob("test_*.py")) + list(SRC_DIR.rglob("tests/test_*.py"))
    return sorted(set(files))


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Test                                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.internal
def test_each_test_function_is_explicitly_marked():
    """
    Verify that each test function or method declares an explicit classification mark.

    Ensures:
        Every test function is decorated with one of:
        @pytest.mark.unit | @pytest.mark.integration | @pytest.mark.e2e | @pytest.mark.internal

    Rationale:
        Enables traceability and coverage classification per DO-178C/ISO 26262 guidelines.
    """
    unmarked = []

    for path in _candidate_files():
        try:
            src = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        tree = ast.parse(src, filename=str(path))
        pytest_aliases, mark_aliases = _collect_aliases(tree)

        for lineno, name, marks in _iter_tests(
            tree, pytest_aliases=pytest_aliases, mark_aliases=mark_aliases
        ):
            if not (marks & VALID_MARKS):
                rel = path.relative_to(PROJECT_ROOT)
                unmarked.append((str(rel), lineno, name))

    if unmarked:
        total = len(unmarked)
        summary_lines = [
            f"\n{total} unmarked test{'s' if total > 1 else ''} detected — Please add a suitable marker\n"
        ]

        current_file = None
        for file, line, name in sorted(unmarked):
            if file != current_file:
                current_file = file
                summary_lines.append(f"\n{file}")
            summary_lines.append(f"{file}:{line} → {name}")

        summary = "\n".join(summary_lines)
        assert not unmarked, summary
