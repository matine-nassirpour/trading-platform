"""
Governance layer ensuring structural and architectural test integrity.
This is part of the Clean Testing Policy (ISO / DO-178C / IEC 62304 compliance).
"""

# @pytest.mark.internal
# def test_no_test_files_outside_designated_paths():
#     """
#     Ensure all test files are under 'tests/' or '<src>/.../tests/'.
#     """
#     violations = []
#     for path in PROJECT_ROOT.rglob("test_*.py"):
#         if not (
#             str(path).startswith(str(TEST_DIR))
#             or "src\\quantum" in str(path) and "\\tests\\" in str(path)
#         ):
#             violations.append(str(path))
#
#     assert not violations, (
#         "The following test files are outside allowed locations:\n"
#         + "\n".join(violations)
#     )


# @pytest.mark.internal
# def test_test_functions_naming_convention():
#     """
#     Enforce pytest naming convention: test_*, not test*, not *_test.
#     """
#     invalid = []
#     for path in TEST_DIR.rglob("*.py"):
#         for line in path.read_text(encoding="utf-8").splitlines():
#             if re.match(r"^\s*def\s+(?!test_)\w+test", line):
#                 invalid.append(f"{path}: {line.strip()}")
#
#     assert not invalid, (
#         "Invalid test naming convention found:\n" + "\n".join(invalid)
#     )


# @pytest.mark.internal
# def test_fixture_dependency_visibility(pytestconfig):
#     """
#     Verify that all fixtures are properly declared and discoverable.
#     Prevents hidden test coupling via undeclared imports.
#     """
#     fixture_manager = pytestconfig.pluginmanager.get_plugin("fixtures")
#     known = list(fixture_manager._arg2fixturedefs.keys())
#     assert "iso_env" in known or "tmp_workspace" in known, (
#         "Expected global fixtures are missing from registry: "
#         f"{known[:10]}..."
#     )


# @pytest.mark.internal
# def test_fixture_naming_policy():
#     """
#     Fixtures must follow visibility rules:
#     - start with "_" if autouse or internal helper
#     - no "_" if used by tests directly
#     """
#     violations = []
#     for path in Path("tests").rglob("*.py"):
#         text = path.read_text(encoding="utf-8")
#         for match in re.finditer(r"@pytest\.fixture(?:\([^)]*\))?\s*\ndef\s+(_?\w+)", text):
#             name = match.group(1)
#             if name.startswith("_") and "@pytest.fixture(autouse=True)" not in text:
#                 # internal fixtures must be autouse=True or used internally
#                 # (not strict, but signals possible misuse)
#                 continue
#             if not name.startswith("_") and "autouse=True" in match.group(0):
#                 violations.append(f"{path}: public fixture '{name}' should be private")
#
#     assert not violations, (
#         "Fixture naming convention violated:\n" + "\n".join(violations)
#     )
