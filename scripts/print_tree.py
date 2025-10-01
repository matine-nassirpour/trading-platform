from __future__ import annotations

import argparse
import io
import os
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pathspec

# --- constants ---------------------------------------------------------------

BOX_MID, BOX_END, BOX_PIPE, BOX_SPACE = "├── ", "└── ", "│   ", "    "

DEFAULT_IGNORES = [
    ".git/",
    ".idea/",
    ".mypy_cache/",
    ".pytest_cache/",
    "__pycache__/",
    "build/",
    "dist/",
    ".venv/",
    "venv/",
    "*.egg-info/",
    ".ruff_cache/",
    "htmlcov/",
    "test-results/",
]

# --- ignore handling ---------------------------------------------------------


@dataclass(frozen=True)
class IgnoreMatcher:
    spec: pathspec.PathSpec
    root: Path

    @staticmethod
    def from_root(root: Path, extra_ignore_file: Path | None = None) -> IgnoreMatcher:
        """
        Loads ignore patterns: default + root .gitignore + (optional) an additional ignore file.
        """
        lines: list[str] = list(DEFAULT_IGNORES)
        gi = root / ".gitignore"
        if gi.exists():
            try:
                lines.extend(
                    gi.read_text(encoding="utf-8", errors="ignore").splitlines()
                )
            except Exception as e:
                print(f"Warning: failed to read {gi}: {e}", file=sys.stderr)

        if extra_ignore_file:
            if extra_ignore_file.exists():
                try:
                    lines.extend(
                        extra_ignore_file.read_text(
                            encoding="utf-8", errors="ignore"
                        ).splitlines()
                    )
                except Exception as e:
                    print(
                        f"Warning: failed to read {extra_ignore_file}: {e}",
                        file=sys.stderr,
                    )
            else:
                print(
                    f"Warning: ignore file not found: {extra_ignore_file}",
                    file=sys.stderr,
                )

        spec = pathspec.PathSpec.from_lines("gitwildmatch", lines)
        return IgnoreMatcher(spec=spec, root=root.resolve())

    def ignored(self, p: Path, is_dir: bool | None = None) -> bool:
        rel = p.resolve().relative_to(self.root).as_posix()
        if is_dir is None:
            is_dir = p.is_dir()
        if is_dir:
            rel = rel.rstrip("/") + "/"
        return self.spec.match_file(rel)


# --- tree model --------------------------------------------------------------


@dataclass
class TreeOptions:
    max_depth: int | None = None
    dirs_only: bool = False
    prune_empty_dirs: bool = False
    follow_symlinks: bool = False
    case_sensitive: bool = True


@dataclass
class FsEntry:
    path: Path
    is_dir: bool
    is_symlink: bool
    error: str | None = None  # e.g., "permission denied"


# --- builder -----------------------------------------------------------------


class TreeBuilder:
    def __init__(self, root: Path, ignores: IgnoreMatcher, opts: TreeOptions):
        self.root = root.resolve()
        self.ignores = ignores
        self.opts = opts

    def list_children(self, base: Path) -> list[FsEntry]:
        entries: list[FsEntry] = []
        try:
            for p in base.iterdir():
                # Resolve symlink status without resolving target (avoids costly resolution)
                is_link = p.is_symlink()
                try:
                    is_dir = (
                        p.is_dir()
                        if (self.opts.follow_symlinks or not is_link)
                        else False
                    )
                except OSError as e:
                    # Broken symlink or inaccessible target
                    entries.append(
                        FsEntry(path=p, is_dir=False, is_symlink=is_link, error=str(e))
                    )
                    continue

                # Ignore rules
                if self.ignores.ignored(p, is_dir=is_dir):
                    continue
                if self.opts.dirs_only and not is_dir:
                    continue

                entries.append(FsEntry(path=p, is_dir=is_dir, is_symlink=is_link))
        except PermissionError:
            # Mark the directory itself as inaccessible (child listing failed)
            entries.append(
                FsEntry(
                    path=base,
                    is_dir=True,
                    is_symlink=base.is_symlink(),
                    error="permission denied",
                )
            )

        # Sorting: name-only, optionally case-insensitive; dirs first for stable visual grouping
        def sort_key(entry: FsEntry):
            name = entry.path.name
            if not self.opts.case_sensitive:
                name = name.lower()
            # tuple => (is_file, name) so that directories come first
            return not entry.is_dir, name

        entries.sort(key=sort_key)
        return entries

    def has_visible_descendants(self, d: Path, current_depth: int) -> bool:
        try:
            for p in d.iterdir():
                try:
                    is_link = p.is_symlink()
                    is_dir = (
                        p.is_dir()
                        if (self.opts.follow_symlinks or not is_link)
                        else False
                    )
                    if self.ignores.ignored(p, is_dir=is_dir):
                        continue
                    if is_dir:
                        if (
                            self.opts.max_depth is None
                            or (current_depth + 1) < self.opts.max_depth
                        ):
                            return True  # the directory itself will be displayed and/or one can descend
                        else:
                            return True  # visible at least as a child (even if we don't go down)
                    else:
                        if not self.opts.dirs_only:
                            return True
                except OSError:
                    # treat broken/inaccessible child as visible (to avoid hiding surprises)
                    return True
        except PermissionError:
            return True
        return False

    def build_lines(self) -> list[str]:
        lines: list[str] = [f"{self.root.name}/"]

        def descend(base: Path, prefix_stack: list[str]) -> None:
            rel_parts = base.resolve().relative_to(self.root).parts
            current_depth = len(rel_parts)

            children = self.list_children(base)

            # Optionally, prune empty directories by skipping ones without visible content
            if self.opts.prune_empty_dirs:
                filtered: list[FsEntry] = []
                for e in children:
                    if e.is_dir:
                        if (
                            self.opts.max_depth is not None
                            and current_depth >= self.opts.max_depth
                        ):
                            # At depth limit: directory will be listed but not descended; it's still "visible"
                            filtered.append(e)
                        else:
                            if self.has_visible_descendants(e.path, current_depth):
                                filtered.append(e)
                    else:
                        filtered.append(e)
                children = filtered

            for i, entry in enumerate(children):
                last = i == len(children) - 1
                branch = BOX_END if last else BOX_MID
                label = entry.path.name + ("/" if entry.is_dir else "")
                suffix = ""
                if entry.is_symlink:
                    suffix += " -> (symlink)"
                if entry.error:
                    suffix += f" ⟂ ({entry.error})"

                lines.append("".join(prefix_stack) + branch + label + suffix)

                if entry.is_dir:
                    # respect max depth
                    depth = len(entry.path.resolve().relative_to(self.root).parts)
                    if self.opts.max_depth is not None and depth >= self.opts.max_depth:
                        continue
                    # do not descend into symlinked dirs unless allowed
                    if entry.is_symlink and not self.opts.follow_symlinks:
                        continue
                    prefix_stack.append(BOX_SPACE if last else BOX_PIPE)
                    descend(entry.path, prefix_stack)
                    prefix_stack.pop()

        descend(self.root, [])
        return lines


# --- renderer (ASCII already produced via builder) ----------------------------


def write_output(text: str, output: str) -> None:
    if output == "-" or output.strip() == "":
        print(text, end="")
    else:
        Path(output).write_text(text, encoding="utf-8")
        print(f"Wrote {output}")


# --- cli ---------------------------------------------------------------------


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Print a clean project tree (respects .gitignore)."
    )
    ap.add_argument("--root", default=".", help="Root directory (default: .)")
    ap.add_argument(
        "--max-depth", type=int, default=None, help="Limit depth (directories depth)."
    )
    ap.add_argument("--dirs-only", action="store_true", help="Show only directories.")
    ap.add_argument(
        "--prune-empty-dirs", action="store_true", help="Hide empty directories."
    )
    ap.add_argument("--output", default="-", help="Output file or - for stdout.")
    ap.add_argument(
        "--ignore-file", default=None, help="Additional ignore file (optional)."
    )
    ap.add_argument(
        "--follow-symlinks", action="store_true", help="Follow directory symlinks."
    )
    ap.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Sort case-sensitively (default: insensitive on Windows, sensitive elsewhere).",
    )
    return ap.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    # Ensure UTF-8 output for widest compatibility
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, io.UnsupportedOperation):
        pass

    args = parse_args(argv)
    root = Path(args.root).resolve()

    if not root.exists():
        print(f"Root not found: {root}", file=sys.stderr)
        return 1
    if not root.is_dir():
        print(f"Root is not a directory: {root}", file=sys.stderr)
        return 1

    # case sensitivity default heuristic
    case_sensitive = args.case_sensitive or (os.name != "nt")

    ignores = IgnoreMatcher.from_root(
        root, Path(args.ignore_file) if args.ignore_file else None
    )
    opts = TreeOptions(
        max_depth=args.max_depth,
        dirs_only=bool(args.dirs_only),
        prune_empty_dirs=bool(args.prune_empty_dirs),
        follow_symlinks=bool(args.follow_symlinks),
        case_sensitive=case_sensitive,
    )

    builder = TreeBuilder(root=root, ignores=ignores, opts=opts)
    lines = builder.build_lines()
    text = "\n".join(lines) + "\n"
    write_output(text, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
