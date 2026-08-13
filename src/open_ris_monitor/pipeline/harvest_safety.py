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

from open_ris_monitor.pipeline.record_identity import public_record_key

INCREMENTAL_PROFILES = frozenset({"quick", "latest", "public"})
SHRINK_OVERRIDE_PROFILES = frozenset({"backfill", "full"})
PUBLIC_JSONL_FILES = (
    "documents.jsonl",
    "document_versions.jsonl",
    "harvest_runs.jsonl",
    "meetings.jsonl",
    "meeting_items.jsonl",
    "meeting_documents.jsonl",
    "meeting_item_documents.jsonl",
    "organization_groups.jsonl",
    "organization_persons.jsonl",
    "organization_roles.jsonl",
    "organization_positions.jsonl",
    "organization_group_memberships.jsonl",
)


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
        merged[public_record_key(record, filename=generated_path.name)] = record
    for record in generated_records:
        merged[public_record_key(record, filename=generated_path.name)] = record

    write_jsonl(generated_path, merged.values())
    return len(merged)


def merge_incremental_public_outputs(
    existing_public_dir: Path,
    generated_public_dir: Path,
) -> dict[str, int]:
    """Merge generated latest/incremental public exports with the current baseline."""

    merged_counts: dict[str, int] = {}
    for filename in PUBLIC_JSONL_FILES:
        existing_path = existing_public_dir / filename
        generated_path = generated_public_dir / filename
        if existing_path.exists() or generated_path.exists():
            merged_counts[filename] = merge_jsonl_file(existing_path, generated_path)
    return merged_counts


def _stable_identity_set(records: list[dict[str, Any]], *, filename: str) -> set[str]:
    return {public_record_key(record, filename=filename) for record in records}


def _sample_identities(identities: set[str], *, limit: int = 10) -> str:
    sample = sorted(identities)[:limit]
    suffix = " ..." if len(identities) > limit else ""
    return ", ".join(sample) + suffix


def guard_against_output_shrink(
    existing_public_dir: Path,
    generated_public_dir: Path,
    *,
    allow_output_shrink: bool = False,
) -> dict[str, tuple[int, int]]:
    """Fail when staged output loses stable identities from the public baseline.

    A raw row-count drop is safe when it is fully explained by duplicate compaction.
    This keeps the fail-closed protection for real removals while allowing a newer
    merge implementation to clean up duplicate rows without a manual override.
    """

    counts: dict[str, tuple[int, int]] = {}
    failures: list[str] = []
    for filename in PUBLIC_JSONL_FILES:
        existing_records = read_jsonl(existing_public_dir / filename)
        generated_records = read_jsonl(generated_public_dir / filename)
        existing_count = len(existing_records)
        generated_count = len(generated_records)
        counts[filename] = (existing_count, generated_count)

        if existing_count <= 0:
            continue

        existing_identities = _stable_identity_set(existing_records, filename=filename)
        generated_identities = _stable_identity_set(generated_records, filename=filename)
        missing_identities = existing_identities - generated_identities

        if missing_identities:
            detail = (
                f"{filename}: {existing_count} -> {generated_count} rows; "
                f"unique identities {len(existing_identities)} -> {len(generated_identities)}; "
                f"missing identities={len(missing_identities)} "
                f"[{_sample_identities(missing_identities)}]"
            )
            if allow_output_shrink:
                print(f"Output shrink override accepted: {detail}")
            else:
                failures.append(detail)
            continue

        if generated_count < existing_count:
            existing_duplicates = existing_count - len(existing_identities)
            generated_duplicates = generated_count - len(generated_identities)
            print(
                f"Safe duplicate compaction for {filename}: rows {existing_count} -> "
                f"{generated_count}; unique identities {len(existing_identities)} -> "
                f"{len(generated_identities)}; duplicate rows {existing_duplicates} -> "
                f"{generated_duplicates}."
            )

    if failures:
        formatted = "; ".join(failures)
        raise RuntimeError(
            "Generated public output would lose stable identities from the current baseline. "
            "Refusing to publish without allow_output_shrink=true. "
            f"Changes: {formatted}"
        )

    return counts


def validate_required_public_outputs(generated_public_dir: Path) -> None:
    """Reject empty or internally inconsistent staged public output."""

    documents_path = generated_public_dir / "documents.jsonl"
    document_count = count_jsonl(documents_path)
    if document_count <= 0:
        raise RuntimeError("Refusing to publish a zero-record documents.jsonl export.")

    latest_path = generated_public_dir / "latest.json"
    if not latest_path.exists():
        raise RuntimeError("Refusing to publish without latest.json metadata.")
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("latest.json must contain a JSON object.")
    if int(payload.get("dataset_documents_total", -1)) not in {-1, document_count}:
        raise RuntimeError(
            "latest.json dataset_documents_total does not match documents.jsonl."
        )


def refresh_latest_dataset_totals(public_dir: Path) -> dict[str, int]:
    """Refresh latest.json totals after profile-aware staging merges."""

    latest_path = public_dir / "latest.json"
    if not latest_path.exists():
        raise RuntimeError("Cannot refresh dataset totals because latest.json is missing.")
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("latest.json must contain a JSON object.")

    totals = {
        "dataset_documents_total": count_jsonl(public_dir / "documents.jsonl"),
        "dataset_meetings_total": count_jsonl(public_dir / "meetings.jsonl"),
        "dataset_agenda_items_total": count_jsonl(public_dir / "meeting_items.jsonl"),
        "dataset_document_relations_total": count_jsonl(public_dir / "meeting_documents.jsonl")
        + count_jsonl(public_dir / "meeting_item_documents.jsonl"),
    }
    payload.update(totals)
    payload["documents_seen"] = totals["dataset_documents_total"]
    payload["documents_normalized"] = totals["dataset_documents_total"]
    latest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return totals


def protect_public_outputs(
    existing_public_dir: Path,
    generated_public_dir: Path,
    *,
    profile: str,
    allow_output_shrink: bool = False,
) -> dict[str, tuple[int, int]]:
    """Apply profile-aware merge and shrink protection."""

    if allow_output_shrink and profile not in SHRINK_OVERRIDE_PROFILES:
        raise RuntimeError(
            "allow_output_shrink=true is only valid for backfill/full profiles. "
            "Incremental public harvests must preserve the existing dataset."
        )

    if profile in INCREMENTAL_PROFILES:
        merge_incremental_public_outputs(existing_public_dir, generated_public_dir)

    counts = guard_against_output_shrink(
        existing_public_dir,
        generated_public_dir,
        allow_output_shrink=allow_output_shrink,
    )
    refresh_latest_dataset_totals(generated_public_dir)
    validate_required_public_outputs(generated_public_dir)
    return counts


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
