import ast

import pytest

from tests.support.governance_common import candidate_files


@pytest.mark.internal
def test_fixture_naming_policy():
    """
    Fixtures must follow visibility rules:
      - start with "_" if autouse=True
      - no "_" if used by tests directly
    """
    violations = []

    for path in candidate_files():
        if not path.exists() or not path.is_file():
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue

            for dec in node.decorator_list:
                # Handle @pytest.fixture and @pytest.fixture(...)
                if isinstance(dec, ast.Attribute) and dec.attr == "fixture":
                    fixture_name = node.name
                    if fixture_name.startswith("_"):
                        violations.append(
                            f"{path}:{node.lineno} → internal fixture '{fixture_name}' missing autouse=True"
                        )

                elif (
                    isinstance(dec, ast.Call)
                    and getattr(dec.func, "attr", "") == "fixture"
                ):
                    fixture_name = node.name
                    autouse_kw = next(
                        (
                            kw
                            for kw in dec.keywords
                            if kw.arg == "autouse"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                        ),
                        None,
                    )

                    if autouse_kw:
                        if not fixture_name.startswith("_"):
                            violations.append(
                                f"{path}:{node.lineno} → autouse fixture '{fixture_name}' must start with '_'"
                            )
                    else:
                        if fixture_name.startswith("_"):
                            violations.append(
                                f"{path}:{node.lineno} → internal fixture '{fixture_name}' missing autouse=True"
                            )

    if violations:
        total = len(violations)
        summary_lines = [
            f"\n{total} fixture naming violation{'s' if total > 1 else ''} detected\n"
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
