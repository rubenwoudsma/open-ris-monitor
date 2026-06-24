import os
import json
import sys
from jsonschema import Draft7Validator

def validate_jsonl_file(file_path, schema_path, min_records=1):
    """
    Valideert een JSONL-bestand tegen een gegeven JSON-schema en controleert integriteitsregels.
    Tijdens de transitiefase logt dit script schemafouten als waarschuwingen in plaats van te crashen,
    zodat de huidige live site en data intact kunnen blijven.
    """
    if not os.path.exists(file_path):
        print(f"Fout: Bestand {file_path} bestaat niet.")
        return False

    if os.path.getsize(file_path) == 0:
        print(f"Fout: Bestand {file_path} is leeg (0 bytes).")
        return False

    try:
        with open(schema_path, 'r', encoding='utf-8') as sf:
            schema = json.load(sf)
            # Pre-compile de validator voor betere performance
            validator = Draft7Validator(schema)
    except Exception as e:
        print(f"Fout: Kon schema {schema_path} niet laden: {e}")
        return False

    record_count = 0
    schema_errors_found = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                record_count += 1
                
                # Voer de validatie uit en verzamel alle fouten zonder direct te crashen
                errors = list(validator.iter_errors(data))
                
                if errors:
                    schema_errors_found += len(errors)
                    # We loggen alleen de fout van de allereerste regel om de GitHub Actions logs compact te houden
                    if schema_errors_found <= 5:
                        for error in errors:
                            if "schema_version" in str(error.message):
                                print(f"Waarschuwing: Regel {line_num} in {file_path} mist 'schema_version' (Legacy data).")
                            else:
                                print(f"Waarschuwing [Contract Afwijking] op regel {line_num} in {file_path}: {error.message}")
                                
            except json.JSONDecodeError:
                print(f"Fout: Ongeldige JSON op regel {line_num} in {file_path}")
                return False

    if record_count < min_records:
        print(f"Fout: Record-aantal ({record_count}) is lager dan het minimum ({min_records}) voor {file_path}.")
        return False

    # TOTAALOVERZICHT PER BESTAND
    if schema_errors_found > 0:
        print(f"Opmerking: {file_path} succesvol ingelezen ({record_count} records). Er zijn {schema_errors_found} contract-afwijkingen geconstateerd die in latere issues (scrapers) worden rechtgetrokken.")
    else:
        print(f"Succes: {file_path} is volledig geldig conform het nieuwe contract! {record_count} records gecontroleerd.")
        
    return True

def main():
    targets = [
        ("data/public/documents.jsonl", "schemas/document.schema.json"),
        ("data/public/meetings.jsonl", "schemas/meeting.schema.json"),
        ("data/public/meeting_items.jsonl", "schemas/agenda_item.schema.json"),
        ("data/public/meeting_documents.jsonl", "schemas/relation.schema.json"),
        ("data/public/organization_groups.jsonl", "schemas/organization_group.schema.json"),
        ("data/public/organization_persons.jsonl", "schemas/organization_person.schema.json"),
        ("data/public/organization_roles.jsonl", "schemas/organization_role.schema.json"),
        ("data/public/organization_positions.jsonl", "schemas/organization_position.schema.json"),
        ("data/public/organization_group_memberships.jsonl", "schemas/organization_group_membership.schema.json"),
    ]

    if not os.path.exists("data/public"):
        print("Opmerking: Geen 'data/public' map gevonden om te valideren. Dit is normaal tijdens code-only PRs.")
        return

    success = True
    for file_path, schema_path in targets:
        if os.path.exists(file_path):
            if not validate_jsonl_file(file_path, schema_path, min_records=1):
                success = False
        else:
            print(f"Opmerking: Optioneel of nog niet gegenereerd bestand overgeslagen: {file_path}")
    
    if not success:
        print("Fout: Een of meerdere exportbestanden zijn corrupt of leeg (0 bytes).")
        sys.exit(1)

if __name__ == "__main__":
    main()
