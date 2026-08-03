"""Validate generated public JSONL exports and minimum record counts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator


def validate_jsonl_file(
    file_path: str | Path,
    schema_path: str | Path,
    min_records: int = 1,
) -> bool:
    """Validate JSON syntax, minimum volume and report schema deviations."""
    file_path = Path(file_path)
    schema_path = Path(schema_path)
    if not file_path.exists():
        print(f"Fout: Bestand {file_path} bestaat niet.")
        return False
    if file_path.stat().st_size == 0:
        print(f"Fout: Bestand {file_path} is leeg (0 bytes).")
        return False

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = Draft7Validator(schema)
    except Exception as exc:
        print(f"Fout: Kon schema {schema_path} niet laden: {exc}")
        return False

    record_count = 0
    schema_errors_found = 0
    with file_path.open("r", encoding="utf-8") as data_file:
        for line_num, line in enumerate(data_file, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Fout: Ongeldige JSON op regel {line_num} in {file_path}")
                return False
            record_count += 1
            errors = list(validator.iter_errors(data))
            if errors:
                schema_errors_found += len(errors)
                if schema_errors_found <= 5:
                    for error in errors:
                        if "schema_version" in str(error.message):
                            print(
                                f"Waarschuwing: Regel {line_num} in {file_path} mist "
                                "'schema_version' (legacy data)."
                            )
                        else:
                            print(
                                "Waarschuwing [Contract Afwijking] op regel "
                                f"{line_num} in {file_path}: {error.message}"
                            )

    if record_count < min_records:
        print(
            f"Fout: Record-aantal ({record_count}) is lager dan het minimum "
            f"({min_records}) voor {file_path}."
        )
        return False
    if schema_errors_found > 0:
        print(
            f"Opmerking: {file_path} succesvol ingelezen ({record_count} records). "
            f"Er zijn {schema_errors_found} contract-afwijkingen geconstateerd."
        )
    else:
        print(
            f"Succes: {file_path} is volledig geldig conform het contract, "
            f"{record_count} records gecontroleerd."
        )
    return True


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Open RIS Monitor exports.")
    parser.add_argument("--public-dir", type=Path, default=Path("data/public"))
    parser.add_argument("--schema-dir", type=Path, default=Path("schemas"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    targets = [
        ("documents.jsonl", "document.schema.json"),
        ("meetings.jsonl", "meeting.schema.json"),
        ("meeting_items.jsonl", "agenda_item.schema.json"),
        ("meeting_documents.jsonl", "relation.schema.json"),
        ("meeting_item_documents.jsonl", "relation.schema.json"),
        ("organization_groups.jsonl", "organization_group.schema.json"),
        ("organization_persons.jsonl", "organization_person.schema.json"),
        ("organization_roles.jsonl", "organization_role.schema.json"),
        ("organization_positions.jsonl", "organization_position.schema.json"),
        (
            "organization_group_memberships.jsonl",
            "organization_group_membership.schema.json",
        ),
    ]
    if not args.public_dir.exists():
        print(f"Opmerking: Geen public map gevonden: {args.public_dir}")
        return

    success = True
    for filename, schema_filename in targets:
        file_path = args.public_dir / filename
        if file_path.exists():
            if not validate_jsonl_file(file_path, args.schema_dir / schema_filename):
                success = False
        else:
            print(f"Opmerking: Optioneel bestand overgeslagen: {file_path}")
    if not success:
        print("Fout: Een of meerdere exportbestanden zijn corrupt of leeg.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
