"""Generate JSON schemas from canonical Pydantic models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic.json_schema import models_json_schema

from open_ris_monitor.models import Document, Meeting, MeetingItem
from open_ris_monitor.models.organization import (
    OrganizationGroup,
    OrganizationGroupMembership,
    OrganizationPerson,
    OrganizationPosition,
    OrganizationRole,
)
from open_ris_monitor.analysis.reports import (
    MeetingsWithoutDocumentsReport,
    UnlinkedDocumentsReport,
)
from open_ris_monitor.models.relations import (
    MeetingDocumentRelation,
    MeetingItemDocumentRelation,
)

# The file names are based on `validate_exports.py`
SCHEMA_MAPPING = {
    "document.schema.json": [Document],
    "meeting.schema.json": [Meeting],
    "agenda_item.schema.json": [MeetingItem],
    "relation.schema.json": [MeetingDocumentRelation, MeetingItemDocumentRelation],
    "organization_group.schema.json": [OrganizationGroup],
    "organization_person.schema.json": [OrganizationPerson],
    "organization_role.schema.json": [OrganizationRole],
    "organization_position.schema.json": [OrganizationPosition],
    "organization_group_membership.schema.json": [OrganizationGroupMembership],
    "meetings_without_documents.schema.json": [MeetingsWithoutDocumentsReport],
    "unlinked_documents.schema.json": [UnlinkedDocumentsReport],
}


def generate_schemas(schema_dir: Path):
    """Generate JSON schemas for all canonical Pydantic models."""
    schema_dir.mkdir(parents=True, exist_ok=True)

    for filename, models in SCHEMA_MAPPING.items():
        output_path = schema_dir / filename
        print(f"Generating {output_path}...")

        # The `models_json_schema` function from Pydantic can create a schema
        # that validates against any of the provided models using `anyOf`.
        # This is perfect for our generic `relation.schema.json`.
        _, schema = models_json_schema(
            models,
            ref_template="#/definitions/{model}",
            title="Open RIS Monitor Canonical Model",
            description="JSON schema for Open RIS Monitor canonical data models.",
        )

        # For schemas with only one model, we can simplify the output a bit
        # by removing the top-level `anyOf` wrapper and inlining the definition.
        if len(models) == 1 and "anyOf" in schema:
            ref = schema["anyOf"][0].get("$ref")
            if ref:
                ref_name = ref.split("/")[-1]
                if "definitions" in schema and ref_name in schema["definitions"]:
                    schema = schema["definitions"][ref_name]
                    schema["title"] = models[0].__name__

        output_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Generate JSON schemas for Pydantic models.")
    parser.add_argument("--schema-dir", type=Path, default=Path("schemas"))
    args = parser.parse_args()
    generate_schemas(args.schema_dir)
    print("\nAll schemas generated successfully.")


if __name__ == "__main__":
    main()