"""Safety helpers for publishing harvested public exports.

Daily latest/incremental harvests should enrich the existing public dataset, not
replace a broad backfill with a narrow window. Broad backfill/full runs may replace
canonical exports, but only when the operator explicitly allows an output shrink.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Iterable

INCREMENTAL_PROFILES = frozenset({"quick", "latest", "public"})
PUBLIC_JSONL_FILES = (
    "documents.jsonl",
    "document_versions.jsonl",
    "harvest_runs.jsonl",
    "meetings.jsonl",
    "meeting_items.jsonl",
    "meeting_documents.jsonl",
    "meeting_item_documents.jsonl",
)


def _json_key(record: dict[str, Any]) -> str:
    """Return a deterministic fallback key for records without a stable id."""

    return json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def record_key(record: dict[str, Any]) -> str:
    """Return the stable merge key for a public JSONL record."""

    for key in (
        "id",
        "source_id",
        "document_id",
        "meeting_item_id",
        "meeting_id",
        "harvest_run_id",
    ):
        value = record.get(key)
        if value is not None and str(value).strip():
            return f"{key}:{value}"
    return f"json:{_json_key(record)}"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read JSONL records from path. Missing files are treated as empty."""

    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected object in {path} line {line_number}")
        records.append(payload)
    return records


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    """Write compact, deterministic JSONL records."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            file.write("\n")


def count_jsonl(path: Path) -> int:
    """Return the number of non-empty JSONL records."""

    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def merge_jsonl_file(existing_path: Path, generated_path: Path) -> int:
    """Merge generated JSONL records into an existing public JSONL file.

    Existing rows are preserved and generated rows replace rows with the same stable
    key. This keeps daily latest harvests from shrinking historical backfill output.
    """

    existing_records = read_jsonl(existing_path)
    generated_records = read_jsonl(generated_path)

    if not existing_records:
        return len(generated_records)
    if not generated_records:
        if existing_path.exists():
            generated_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(existing_path, generated_path)
        return len(existing_records)

    merged: dict[str, dict[str, Any]] = {}
    for record in existing_records:
        merged[record_key(record)] = record
    for record in generated_records:
        merged[record_key(record)] = record

    write_jsonl(generated_path, merged.values())
    return len(merged)


def merge_incremental_public_outputs(existing_public_dir: Path, generated_public_dir: Path) -> dict[str, int]:
    """Merge generated latest/incremental public exports with the current baseline."""

    merged_counts: dict[str, int] = {}
    for filename in PUBLIC_JSONL_FILES:
        existing_path = existing_public_dir / filename
        generated_path = generated_public_dir / filename
        if existing_path.exists() or generated_path.exists():
            merged_counts[filename] = merge_jsonl_file(existing_path, generated_path)
    return merged_counts


def guard_against_output_shrink(
    existing_public_dir: Path,
    generated_public_dir: Path,
    *,
    allow_output_shrink: bool = False,
) -> dict[str, tuple[int, int]]:
    """Fail if generated public JSONL exports shrink versus the existing baseline."""

    counts: dict[str, tuple[int, int]] = {}
    failures: list[str] = []
    for filename in PUBLIC_JSONL_FILES:
        existing_count = count_jsonl(existing_public_dir / filename)
        generated_count = count_jsonl(generated_public_dir / filename)
        counts[filename] = (existing_count, generated_count)
        if existing_count > 0 and generated_count < existing_count:
            failures.append(f"{filename}: {existing_count} -> {generated_count}")

    if failures and not allow_output_shrink:
        formatted = "; ".join(failures)
        raise RuntimeError(
            "Generated public output is smaller than the current baseline. "
            "Refusing to publish without allow_output_shrink=true. "
            f"Drops: {formatted}"
        )

    return counts


def protect_public_outputs(
    existing_public_dir: Path,
    generated_public_dir: Path,
    *,
    profile: str,
    allow_output_shrink: bool = False,
) -> dict[str, tuple[int, int]]:
    """Apply profile-aware merge and shrink protection."""

    if profile in INCREMENTAL_PROFILES:
        merge_incremental_public_outputs(existing_public_dir, generated_public_dir)

    return guard_against_output_shrink(
        existing_public_dir,
        generated_public_dir,
        allow_output_shrink=allow_output_shrink,
    )


def _parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Protect Open RIS Monitor public exports.")
    parser.add_argument("--existing-public-dir", type=Path, required=True)
    parser.add_argument("--generated-public-dir", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--allow-output-shrink", default="false")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    counts = protect_public_outputs(
        args.existing_public_dir,
        args.generated_public_dir,
        profile=args.profile,
        allow_output_shrink=_parse_bool(args.allow_output_shrink),
    )
    for filename, (existing_count, generated_count) in counts.items():
        print(f"{filename}: existing={existing_count} generated={generated_count}")


if __name__ == "__main__":
    main()
