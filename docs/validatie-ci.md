# Open RIS Monitor: Export Validatie in CI

Dit document beschrijft de geautomatiseerde integriteitscontroles binnen de GitHub Actions pipeline.

## 🛡️ Doel van de validatie
De frontend vertrouwt volledig op de integriteit van de statische `.jsonl` bestanden in `data/public/`. Deze stap beschermt de productieomgeving tegen:
1. **HTTP 200 met lege payloads** van upstream gemeentelijke RIS-systemen.
2. **Per ongeluk overschrijven** van gezonde historische data met corrupte exports.
3. **Schema-afwijkingen** voordat ze de live site bereiken.
