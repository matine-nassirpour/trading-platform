import ast

from pathlib import Path

# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Project Paths                                                              │
# ╰────────────────────────────────────────────────────────────────────────────╯
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src" / "quantum"
TEST_DIR = PROJECT_ROOT / "tests"


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Classification Constants                                                   │
# ╰────────────────────────────────────────────────────────────────────────────╯
VALID_MARKS = {"governance", "unit", "integration", "e2e"}
IGNORED_MARKS = {
    "parametrize",
    "skip",
    "skipif",
    "xfail",
    "usefixtures",
    "filterwarnings",
}


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Shared File Discovery                                                      │
# ╰────────────────────────────────────────────────────────────────────────────╯
def candidate_files() -> list[Path]:
    """
    Discover Python test files within project boundaries.

    Scans both:
        - Top-level tests/** (e.g., tests/integration/, tests/unit/)
        - In-source module tests (e.g., src/**/tests/)

    Excludes:
        - __init__.py

    Returns:
        Sorted list of unique test file paths.
    """
    candidates: set[Path] = set()

    candidates.update(p for p in TEST_DIR.rglob("*.py") if p.name != "__init__.py")

    for test_dir in SRC_DIR.rglob("tests"):
        if test_dir.is_dir():
            candidates.update(
                p for p in test_dir.rglob("*.py") if p.name != "__init__.py"
            )

    return sorted(candidates)


# ╭────────────────────────────────────────────────────────────────────────────╮
# │ Shared AST Utilities                                                       │
# ╰────────────────────────────────────────────────────────────────────────────╯
def collect_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    """
    Identify aliases used for 'pytest' and 'pytest.mark' imports.
    Used across governance tests.
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


# def candidate_files() -> list[Path]:
#     candidates: set[Path] = set()
#
#     candidates.update(
#         p for p in TEST_DIR.rglob("*.py")
#         if p.name != "__init__.py"
#     )
#
#     for test_dir in SRC_DIR.rglob("tests"):
#         if test_dir.is_dir():
#             candidates.update(
#                 p for p in test_dir.rglob("*.py")
#                 if p.name != "__init__.py"
#             )
#
#     return sorted(candidates)
