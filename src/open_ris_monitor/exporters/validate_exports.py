import os
import json
import sys
from jsonschema import validate, ValidationError

def validate_jsonl_file(file_path, schema_path, min_records=1):
    """
    Valideert een JSONL-bestand tegen een gegeven JSON-schema en controleert integriteitsregels.
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
    except Exception as e:
        print(f"Fout: Kon schema {schema_path} niet laden: {e}")
        return False

    record_count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                validate(instance=data, schema=schema)
                record_count += 1
            except json.JSONDecodeError:
                print(f"Fout: Ongeldige JSON op regel {line_num} in {file_path}")
                return False
            except ValidationError as e:
                print(f"Fout: Schema-validatie mislukt op regel {line_num} in {file_path}: {e.message}")
                return False

    if record_count < min_records:
        print(f"Fout: Record-aantal ({record_count}) is lager dan het minimum ({min_records}) voor {file_path}.")
        return False

    print(f"Succes: {file_path} is geldig. {record_count} records succesvol gecontroleerd.")
    return True

def main():
    # Gecorrigeerde paden op basis van de werkelijke data/public/ structuur van de repo
    targets = [
        ("data/public/documents.jsonl", "schemas/document.schema.json"),
        ("data/public/meetings.jsonl", "schemas/meeting.schema.json"),
        ("data/public/meeting_items.jsonl", "schemas/agenda_item.schema.json"),
        ("data/public/meeting_documents.jsonl", "schemas/relation.schema.json")
    ]

    # Als de public data-map er niet is (bijv. bij een schone code-only PR), skippen we de check
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
        print("Fout: Een of meerdere exportbestanden voldoen niet aan de integriteitseisen.")
        sys.exit(1)

if __name__ == "__main__":
    main()
