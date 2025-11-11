"""
Enforce explicit pytest classification marks on all test functions.
Compliant with Clean Architecture & Certifiable Software Standards.
"""

import ast

import pytest

from tests.support.governance_common import (
    IGNORED_MARKS,
    PROJECT_ROOT,
    VALID_MARKS,
    candidate_files,
    collect_aliases,
)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Internal Helpers                                                           │
# ╰────────────────────────────────────────────────────────────────────────────╯
def _is_classification_mark(
    node: ast.AST, *, pytest_aliases: set[str], mark_aliases: set[str]
) -> str | None:
    """
    Detect whether a decorator corresponds to a pytest classification mark.

    Accepts:
        - <pytest_alias>.mark.<name>[()]
        - <mark_alias>.<name>[()]

    Ignores:
        - parametrize, skip, xfail, usefixtures, etc.

    Returns:
        The classification mark name if valid, else None.
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
    Extract all classification marks from a function or class decorator list.
    Deterministic, pure, and side-effect-free.
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

    Explicit function-level classification required.
    Class-level marks are inherited for methods.
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
        elif isinstance(node, ast.ClassDef):
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


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Test                                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
@pytest.mark.governance
def test_each_test_function_is_explicitly_marked():
    """
    Verify that each test function or method declares an explicit classification mark.

    Ensures:
        Every test function is decorated with one of:
        @pytest.mark.governance | @pytest.mark.verification
        @pytest.mark.validation | @pytest.mark.qualification
        @pytest.mark.certification | @pytest.mark.performance
        @pytest.mark.system

    Rationale:
        Enables traceability and coverage classification per DO-178C/ISO 26262 guidelines.
    """
    unmarked = []

    for path in candidate_files():
        try:
            src = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        tree = ast.parse(src, filename=str(path))
        pytest_aliases, mark_aliases = collect_aliases(tree)

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
