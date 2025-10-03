"""
tree_exporter.py — Clean and deterministic export of project’s directory tree to a .txt file

Key features:
- Deterministic ordering: directories first, then files; case-insensitive sorting.
- Exclusions: multiple --exclude (glob) patterns; --respect-gitignore option (via pathspec if available).
- Symbolic links: not followed by default; displayed as " -> target". Safe --follow-symlinks option available.
- Maximum depth (--max-depth), hidden files/directories (--include-hidden).
- UTF-8 encoding, LF line endings, stable and reproducible output.
- Error handling (permissions, encoding issues, symlink loops) with clear messages.
- No mandatory dependencies. pathspec is optional for .gitignore support.
"""

from __future__ import annotations

import argparse
import ctypes
import fnmatch
import logging
import os
from collections.abc import Callable, Sequence
from ctypes import wintypes
from functools import lru_cache
from pathlib import Path

try:
    # Optional: high-quality .gitignore matching
    import pathspec  # type: ignore
except ImportError:  # pragma: no cover - absence tolerated
    pathspec = None


FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_SYSTEM = 0x4
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF

DEFAULT_EXCLUDES = (
    ".git",
    ".hg",
    ".svn",
    "**/__pycache__",
    "**/.mypy_cache",
    "**/.pytest_cache",
    "**/.ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    ".DS_Store",
    "htmlcov",
    "test-results",
    "_logs",
    "_audit",
)


# ------- Configuration & Utilities ------------------------------------------


@lru_cache(maxsize=1)
def _get_file_attributes_w() -> Callable[[str], int]:
    k32 = ctypes.windll.kernel32
    func = k32.GetFileAttributesW  # type: ignore[attr-defined]
    func.argtypes = [wintypes.LPCWSTR]
    func.restype = wintypes.DWORD
    return func


def _is_hidden(path: Path) -> bool:
    """
    Determine whether a path is considered 'hidden'.

    POSIX: a path is hidden if its name starts with '.'.
    Windows: attempt to check the FILE_ATTRIBUTE_HIDDEN flag if available,
    otherwise fall back to the '.' prefix convention.
    """
    name_hidden = path.name.startswith(".")
    if os.name != "nt":
        return name_hidden

    try:
        get_file_attributes_w = _get_file_attributes_w()
        attrs = get_file_attributes_w(str(path))
        if attrs == INVALID_FILE_ATTRIBUTES:
            # Windows API returned failure (e.g., path does not exist or is inaccessible)
            return name_hidden

        return (
            bool(attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)) or name_hidden
        )

    except AttributeError:
        # Very old/odd environments where the symbol isn't exposed – fall back gracefully.
        return name_hidden


def _case_insensitive_key(p: Path) -> tuple[str, str]:
    return p.name.lower(), p.name


class ExcludeMatcher:
    """
    Combines multiple exclusion strategies for project tree traversal.

    Features:
    - Supports custom glob-style exclusion patterns.
      * Simple names without '/' or wildcards (e.g. "__pycache__", ".venv")
        are matched against any path component.
      * Full glob patterns (e.g. "**/__pycache__", "build/*", "*.log")
        are matched against the full relative POSIX path.
    - Optional .gitignore support (via the 'pathspec' library if installed).
    - Callable interface: returns True if the given path should be excluded.

    Attributes:
        root (Path): Root directory of the project.
        patterns (list[str]): Exclusion patterns provided by the user and/or defaults.
        _gitignore_spec (Optional[pathspec.PathSpec]): Compiled .gitignore matcher if available.

    Example:
        matcher = ExcludeMatcher(root=Path("."), patterns=["__pycache__", "*.log"], respect_gitignore=True)
        if matcher(Path("src/__pycache__")):
            print("Excluded")
    """

    def __init__(self, root: Path, patterns: Sequence[str], respect_gitignore: bool):
        self.root = root
        self.patterns = list(patterns)
        self._gitignore_spec = None

        if respect_gitignore:
            if pathspec is None:
                logging.warning(
                    "--respect-gitignore was enabled but 'pathspec' is not installed. "
                    ".gitignore will be ignored. (pip install pathspec)"
                )
            else:
                gitignore = root / ".gitignore"
                if gitignore.exists():
                    try:
                        spec = pathspec.PathSpec.from_lines(
                            pathspec.patterns.GitWildMatchPattern,
                            gitignore.read_text(encoding="utf-8").splitlines(),
                        )
                        self._gitignore_spec = spec
                    except Exception as e:
                        logging.warning(
                            f"Failed to parse .gitignore ({gitignore}): {e}"
                        )

    def __call__(self, path: Path) -> bool:
        """Return True if the given path should be excluded."""
        rel = path.relative_to(self.root) if path != self.root else Path(".")
        rel_posix = rel.as_posix()

        for pat in self.patterns:
            if ("/" not in pat) and not any(ch in pat for ch in "*?[]"):
                if pat in rel.parts:
                    return True

            if fnmatch.fnmatch(rel_posix, pat):
                return True

        if self._gitignore_spec is not None:
            if self._gitignore_spec.match_file(rel_posix):
                return True

        return False


# ------- Rendering the tree structure ------------------------------------------


def _is_dir_follow(p: Path, follow: bool) -> bool:
    if follow:
        return p.is_dir()

    return p.is_dir() and not p.is_symlink()


def _is_file_follow(p: Path, follow: bool) -> bool:
    if follow:
        return p.is_file()

    return p.is_file() and not p.is_symlink()


def iter_children(
    directory: Path,
    *,
    exclude: ExcludeMatcher,
    include_hidden: bool,
    follow_symlinks: bool,
) -> list[Path]:
    """
    Return a sorted and filtered list of immediate children of a directory.

    - Applies exclusion rules (glob patterns, .gitignore if enabled).
    - Skips hidden entries unless `include_hidden=True`.
    - Returns entries in deterministic order: directories first, then files, then others.
    - Sorting is case-insensitive.
    """
    try:
        entries = list(directory.iterdir())
    except PermissionError:
        logging.warning(f"Permission denied: {directory}")
        return []
    except FileNotFoundError:
        logging.warning(f"Directory not found: {directory}")
        return []
    except OSError as e:
        logging.warning(f"Error accessing {directory}: {e}")
        return []

    # Initial filtering
    filtered: list[Path] = []
    for p in entries:
        if not include_hidden and _is_hidden(p):
            if p.is_dir():
                continue
        if exclude(p):
            continue
        # If symlinks are not followed, we still include them but do not recurse into them
        filtered.append(p)

    # Deterministic ordering: directories first, then files, then others
    dirs = sorted(
        [p for p in filtered if _is_dir_follow(p, follow_symlinks)],
        key=_case_insensitive_key,
    )
    files = sorted(
        [p for p in filtered if _is_file_follow(p, follow_symlinks)],
        key=_case_insensitive_key,
    )
    others = sorted(
        [p for p in filtered if p not in dirs + files], key=_case_insensitive_key
    )  # fifos, devices, etc.

    return dirs + files + others


def render_tree(
    root: Path,
    *,
    exclude: ExcludeMatcher,
    include_hidden: bool,
    follow_symlinks: bool,
    max_depth: int | None,
    stream,
) -> None:
    """
    Render the project directory tree in a 'tree'-like format using Unicode characters.

    - Adds a '/' suffix to directory names (including the root).
    - Annotates symbolic links after the entry name (after '/' if it is a directory).
    - Does not follow symlinks by default (can be enabled with `follow_symlinks=True`).
    - Traversal can be limited with `max_depth`.
    """

    root_display = (root.resolve().name or str(root.resolve())) + "/"
    stream.write(f"{root_display}\n")

    def _walk(dir_path: Path, prefix: str, depth: int) -> None:
        if max_depth is not None and depth > max_depth:
            return

        children = iter_children(
            dir_path,
            exclude=exclude,
            include_hidden=include_hidden,
            follow_symlinks=follow_symlinks,
        )

        for idx, child in enumerate(children):
            is_last = idx == len(children) - 1
            branch = "└── " if is_last else "├── "

            # Déterminer si c'est un dossier (compat: sans follow_symlinks arg)
            try:
                is_dir = (
                    child.is_dir()
                    if follow_symlinks
                    else (child.is_dir() and not child.is_symlink())
                )
            except OSError as e:
                logging.warning(f"Failed to check directory status for {child}: {e}")
                is_dir = False

            # Display name (+ '/' if directory)
            display_name = child.name + ("/" if is_dir else "")

            # Build the tree line
            line = prefix + branch + display_name

            # Symlink annotation (after the name, after '/' if directory)
            try:
                if child.is_symlink():
                    target = os.readlink(child)
                    line += f" -> {target}"
            except OSError as e:
                logging.warning(f"Failed to resolve symlink for {child}: {e}")
                line += " -> <unreadable>"

            stream.write(line + "\n")

            # Recurse into subdirectoriess
            if is_dir:
                # Avoid symlink loops when following symlinks
                if follow_symlinks and child.is_symlink():
                    continue
                next_prefix = prefix + ("    " if is_last else "│   ")
                _walk(child, next_prefix, depth + 1)

    _walk(root, prefix="", depth=1)


# ------- CLI -------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tree-exporter",
        description="Export a project's directory tree to a .txt file (deterministic and clean output).",
    )
    parser.add_argument(
        "root",
        type=Path,
        help="Root directory of the project to export",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Destination .txt file",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum depth (default: unlimited)",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links (use with caution)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude (can be repeated). "
        "Example: --exclude 'build/*' --exclude '*.log'",
    )
    parser.add_argument(
        "--respect-gitignore",
        action="store_true",
        help="Respect .gitignore rules (requires 'pathspec' if installed)",
    )
    parser.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Do not apply default exclusions (.git, __pycache__, .venv, etc.)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v: info, -vv: debug)",
    )
    return parser.parse_args(argv)


def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    root: Path = args.root.resolve()
    if not root.exists() or not root.is_dir():
        logging.error(f"Invalid root: {root}")
        return 2

    patterns: list[str] = []
    if not args.no_default_excludes:
        patterns.extend(DEFAULT_EXCLUDES)
    patterns.extend(args.exclude or [])

    matcher = ExcludeMatcher(
        root=root, patterns=patterns, respect_gitignore=args.respect_gitignore
    )

    # Writing in UTF-8 + LF for reproducibility (including under Windows)
    try:
        with args.output.open("w", encoding="utf-8", newline="\n") as f:
            render_tree(
                root=root,
                exclude=matcher,
                include_hidden=args.include_hidden,
                follow_symlinks=args.follow_symlinks,
                max_depth=args.max_depth,
                stream=f,
            )
    except Exception as e:
        logging.error(f"Failed to write output file '{args.output}': {e}")
        return 1

    logging.info(f"Tree exported to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
