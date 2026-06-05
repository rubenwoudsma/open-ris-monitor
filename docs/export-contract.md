# Open RIS Monitor: Exportcontract & Schemaversiebeleid

Dit document beschrijft de interfacegrens tussen de harvester-workflows van de gemeente en de client-side webinterfaces. Aangezien Open RIS Monitor volledig functioneert zonder gecentraliseerde database, fungeren bestanden die zijn geëxporteerd als platte JSON Lines (`.jsonl`) als ons primaire datacontract.

---

## 📈 Schemaversiestrategie

Alle structurele datacontracten maken gebruik van strikte **Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH`). Elke invoer in onze samengestelde datasets moet een tekstveld `schema_version` bevatten.

* **MAJOR**: Structurele, brekende wijzigingen. Dit vereist aanpassingen in zowel de harvesting-templates als de TypeScript UI-weergavelagen (bijv. het verwijderen van verplichte velden).
* **MINOR**: Niet-brekende functie-updates. Het toevoegen van optionele velden die oudere verwerkingsblokken veilig kunnen overslaan zonder aan stabiliteit te verliezen.
* **PATCH**: Updates gericht op beschrijvende teksten, patrooncorrecties of structurele verduidelijkingen in de JSON Schema-definities.

---

## 🤝 Compatibiliteitsgaranties

1. **Defensieve Verwerking**: De TypeScript-frontend maakt gebruik van robuuste standaard parsing-patronen. Velden die worden aangetroffen maar niet zijn gedefinieerd in de versieconfiguratie, worden overgeslagen in plaats van dat er fouten optreden die de applicatie laten vastlopen.
2. **Achterwaartse Compatibiliteit**: Kleine revisies in de lay-out (minor releases) garanderen volledige structurele ondersteuning voor data die is gegenereerd door eerdere minor updates.

---

## 🗂️ Doellocaties voor Exports

Harvesters schrijven naar de volgende voorspelbare statische relatieve paden binnen de deployment-structuur:
* `data/documents.jsonl`
* `data/meetings.jsonl`
* `data/agenda_items.jsonl`
* `data/relations.jsonl`
