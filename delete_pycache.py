#!/usr/bin/env python3

import argparse
import os
import shutil
from pathlib import Path


DEFAULT_DIR_NAMES = (
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    ".hypothesis",
    ".tox",
)


def _iter_candidate_dirs(root: Path, names: set[str], follow_symlinks: bool) -> list[Path]:
    candidates: list[Path] = []

    for dirpath, dirnames, _filenames in os.walk(root, followlinks=follow_symlinks):
        current = Path(dirpath)
        keep: list[str] = []

        for d in dirnames:
            p = current / d

            if not follow_symlinks and p.is_symlink():
                keep.append(d)
                continue

            if d in names:
                candidates.append(p)
            else:
                keep.append(d)

        dirnames[:] = keep

    return candidates


def _delete_path(p: Path) -> None:
    if not p.exists():
        return

    if p.is_symlink() or p.is_file():
        p.unlink()
        return

    shutil.rmtree(p)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete common Python cache directories (e.g. __pycache__, .pytest_cache) under a root directory."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted, but do not delete anything",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Do not prompt for confirmation",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symlinks while scanning",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Additional directory name to delete (can be provided multiple times)",
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root path does not exist or is not a directory: {root}")

    names = set(DEFAULT_DIR_NAMES)
    names.update(args.include)

    candidates = _iter_candidate_dirs(root, names=names, follow_symlinks=args.follow_symlinks)
    candidates = sorted({p.resolve() for p in candidates}, key=lambda p: str(p))

    if not candidates:
        print("No matching cache directories found.")
        return 0

    for p in candidates:
        print(p)

    if args.dry_run:
        print(f"\nDry run: would delete {len(candidates)} path(s).")
        return 0

    if not args.yes:
        resp = input(f"\nDelete {len(candidates)} path(s)? [y/N] ").strip().lower()
        if resp not in {"y", "yes"}:
            print("Aborted.")
            return 1

    deleted = 0
    for p in candidates:
        try:
            _delete_path(p)
            deleted += 1
        except Exception as e:
            print(f"Failed to delete {p}: {e}")

    print(f"\nDeleted {deleted} path(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
