"""Atomically promote validated staged harvest output into repository data paths."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def promote_staged_directories(
    *,
    staged_public_dir: Path,
    target_public_dir: Path,
    staged_raw_dir: Path,
    target_raw_dir: Path,
) -> None:
    """Promote public and raw directories as one rollback-capable transaction."""

    for path in (staged_public_dir, staged_raw_dir):
        if not path.is_dir():
            raise RuntimeError(f"Staged directory does not exist: {path}")

    target_public_dir.parent.mkdir(parents=True, exist_ok=True)
    target_raw_dir.parent.mkdir(parents=True, exist_ok=True)
    public_backup = target_public_dir.with_name(f".{target_public_dir.name}.promotion-backup")
    raw_backup = target_raw_dir.with_name(f".{target_raw_dir.name}.promotion-backup")
    for backup in (public_backup, raw_backup):
        _remove(backup)

    moved_public_target = False
    moved_raw_target = False
    promoted_public = False
    promoted_raw = False
    try:
        if target_public_dir.exists():
            os.replace(target_public_dir, public_backup)
            moved_public_target = True
        if target_raw_dir.exists():
            os.replace(target_raw_dir, raw_backup)
            moved_raw_target = True

        os.replace(staged_public_dir, target_public_dir)
        promoted_public = True
        os.replace(staged_raw_dir, target_raw_dir)
        promoted_raw = True
    except Exception:
        if promoted_public:
            _remove(target_public_dir)
        if promoted_raw:
            _remove(target_raw_dir)
        if moved_public_target and public_backup.exists():
            os.replace(public_backup, target_public_dir)
        if moved_raw_target and raw_backup.exists():
            os.replace(raw_backup, target_raw_dir)
        raise
    else:
        _remove(public_backup)
        _remove(raw_backup)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote validated staged harvest output.")
    parser.add_argument("--staged-public-dir", type=Path, required=True)
    parser.add_argument("--target-public-dir", type=Path, required=True)
    parser.add_argument("--staged-raw-dir", type=Path, required=True)
    parser.add_argument("--target-raw-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    promote_staged_directories(
        staged_public_dir=args.staged_public_dir,
        target_public_dir=args.target_public_dir,
        staged_raw_dir=args.staged_raw_dir,
        target_raw_dir=args.target_raw_dir,
    )
    print("Validated staged harvest output promoted successfully.")


if __name__ == "__main__":
    main()
