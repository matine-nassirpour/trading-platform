"""
tree_exporter.py — Export propre et déterministe de l'arborescence d'un projet vers un .txt

Points clés:
- Tri déterministe: dossiers puis fichiers, tri case-insensitive.
- Exclusions: --exclude (glob) multiples; option --respect-gitignore (via pathspec si dispo).
- Liens symboliques: non suivis par défaut; marqués " -> cible". Option --follow-symlinks sûre.
- Profondeur max (--max-depth), fichiers/dossiers cachés (--include-hidden).
- Encodage UTF-8, fins de ligne LF, sortie stable et reproductible.
- Gestion d'erreurs (permissions, encodage, boucles de symlinks) avec messages utiles.
- Aucune dépendance obligatoire. pathspec est optionnelle pour .gitignore.
"""

from __future__ import annotations

import argparse
import fnmatch
import logging
import os
from collections.abc import Sequence
from pathlib import Path

try:
    # Optionnel: correspondance .gitignore de qualité
    import pathspec  # type: ignore
except Exception:  # pragma: no cover - absence tolérée
    pathspec = None


# ---------- Configuration & utilitaires ----------


def _is_hidden(path: Path) -> bool:
    """
    Détermine si un chemin est 'caché'.
    POSIX: préfixe '.'.
    Windows: on essaie l'attribut FILE_ATTRIBUTE_HIDDEN si dispo, sinon '.'.
    """
    name_hidden = path.name.startswith(".")
    if os.name != "nt":
        return name_hidden
    try:
        import ctypes  # lazy import (Windows only)

        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return name_hidden
        FILE_ATTRIBUTE_HIDDEN = 0x2
        FILE_ATTRIBUTE_SYSTEM = 0x4
        return (
            bool(attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)) or name_hidden
        )
    except Exception:
        return name_hidden


def _case_insensitive_key(p: Path) -> tuple[str, str]:
    return (p.name.lower(), p.name)


class ExcludeMatcher:
    """Compose plusieurs stratégies d'exclusion (glob + .gitignore optionnel)."""

    def __init__(self, root: Path, patterns: Sequence[str], respect_gitignore: bool):
        self.root = root
        self.patterns = list(patterns)
        self._gitignore_spec = None

        if respect_gitignore:
            if pathspec is None:
                logging.warning(
                    "Option --respect-gitignore activée mais 'pathspec' n'est pas installée. "
                    "Ignorer .gitignore. (pip install pathspec)"
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
                            "Impossible de parser .gitignore (%s): %s", gitignore, e
                        )

    def __call__(self, path: Path) -> bool:
        """Retourne True si le chemin doit être EXCLU."""
        # Chemin relatif à la racine (POSIX)
        rel = path.relative_to(self.root) if path != self.root else Path(".")
        rel_posix = rel.as_posix()

        # 1) Motifs utilisateur
        for pat in self.patterns:
            # 1.1 — motif 'nu' (pas de slash, pas de wildcard) => match sur les composants
            if ("/" not in pat) and not any(ch in pat for ch in "*?[]"):
                # rel.parts est un tuple des composants ('src', 'pkg', '__pycache__', ...)
                if pat in rel.parts:
                    return True

            # 1.2 — motif glob standard sur le chemin relatif posix
            if fnmatch.fnmatch(rel_posix, pat):
                return True

        # 2) Règles .gitignore si dispo
        if self._gitignore_spec is not None:
            if self._gitignore_spec.match_file(rel_posix):
                return True

        return False


# ---------- Rendu de l'arborescence ----------
def _is_dir_follow(p: Path, follow: bool) -> bool:
    if follow:
        return p.is_dir()
    # sans suivre les symlinks : un répertoire "réel" seulement
    return p.is_dir() and not p.is_symlink()


def _is_file_follow(p: Path, follow: bool) -> bool:
    if follow:
        return p.is_file()
    # sans suivre les symlinks : un fichier "réel" seulement
    return p.is_file() and not p.is_symlink()


def iter_children(
    directory: Path,
    *,
    exclude: ExcludeMatcher,
    include_hidden: bool,
    follow_symlinks: bool,
) -> list[Path]:
    """Liste triée et filtrée des enfants immédiats."""
    try:
        entries = list(directory.iterdir())
    except PermissionError:
        logging.warning("Permission refusée: %s", directory)
        return []
    except FileNotFoundError:
        logging.warning("Chemin introuvable: %s", directory)
        return []
    except OSError as e:
        logging.warning("Erreur d'accès %s: %s", directory, e)
        return []

    # Filtrage initial
    filtered: list[Path] = []
    for p in entries:
        if not include_hidden and _is_hidden(p):
            if p.is_dir():
                continue
        if exclude(p):
            continue
        # Si on ne suit pas les symlinks, on autorise l'entrée mais on ne la traverse pas
        filtered.append(p)

    # Tri déterministe: dossiers puis fichiers, tri insensible à la casse
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
    Écrit l'arborescence sous forme 'tree' avec caractères unicode.
    - Ajoute un '/' après les noms de dossiers.
    - Annote les liens symboliques après le nom (après le '/' si dossier).
    - Ne suit pas les symlinks par défaut (option follow_symlinks).
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
            except OSError:
                is_dir = False

            # Nom à afficher (+ '/' si dossier)
            display_name = child.name + ("/" if is_dir else "")

            # Construction de la ligne
            line = prefix + branch + display_name

            # Marquage symlink (après le nom, et donc après le '/' si dossier)
            try:
                if child.is_symlink():
                    target = os.readlink(child)
                    line += f" -> {target}"
            except OSError:
                line += " -> <unreadable>"

            stream.write(line + "\n")

            # Descente dans les dossiers
            if is_dir:
                # Si on suit les symlinks, éviter les boucles : ne pas re-descendre dans un répertoire symlinké
                if follow_symlinks and child.is_symlink():
                    continue
                next_prefix = prefix + ("    " if is_last else "│   ")
                _walk(child, next_prefix, depth + 1)

    _walk(root, prefix="", depth=1)


# ---------- CLI ----------

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
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="tree-exporter",
        description="Exporte l'arborescence d'un projet vers un fichier .txt (sortie déterministe & propre).",
    )
    p.add_argument("root", type=Path, help="Répertoire racine du projet à exporter")
    p.add_argument(
        "-o", "--output", type=Path, required=True, help="Fichier .txt de destination"
    )
    p.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Profondeur maximale (par défaut illimitée)",
    )
    p.add_argument(
        "--include-hidden",
        action="store_true",
        help="Inclure les fichiers/dossiers cachés",
    )
    p.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Suivre les liens symboliques (prudent)",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Motif glob à exclure (peut être répété). Ex: --exclude 'build/*' --exclude '*.log'",
    )
    p.add_argument(
        "--respect-gitignore",
        action="store_true",
        help="Respecter .gitignore (via 'pathspec' si installé)",
    )
    p.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Ne pas appliquer les exclusions par défaut (.git, __pycache__, .venv, etc.)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosité (-v: info, -vv: debug)",
    )
    return p.parse_args(argv)


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
        logging.error("Racine invalide: %s", root)
        return 2

    patterns: list[str] = []
    if not args.no_default_excludes:
        patterns.extend(DEFAULT_EXCLUDES)
    patterns.extend(args.exclude or [])

    matcher = ExcludeMatcher(
        root=root, patterns=patterns, respect_gitignore=args.respect_gitignore
    )

    # Écriture en UTF-8 + LF pour reproductibilité (y compris sous Windows)
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
        logging.error("Échec d'écriture du fichier de sortie '%s': %s", args.output, e)
        return 1

    logging.info("Arborescence exportée vers: %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
