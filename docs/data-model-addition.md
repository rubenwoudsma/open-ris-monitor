## Documentidentiteit

Documentidentiteit moet stabiel blijven over meerdere harvests en onafhankelijk zijn van de gekozen viewer of exportvorm.

Bronidentificatie blijft altijd behouden via:

- `source_id`
- `source_object_id`

De aanbevolen traceerbare identiteit voor documentversies is:

```text
municipality_id +
source_system_id +
source_id +
source_object_id
```

Deze combinatie maakt het mogelijk om wijzigingen in bronbestanden te volgen zonder afhankelijk te zijn van leveranciersspecifieke interne identifiers.

Canonieke identifiers volgen het patroon:

```text
{municipality_slug}-document-{source_id}
```

Voorbeeld:

```text
huizen-document-25892
```

De bronidentificatie blijft altijd beschikbaar in de public exports zodat herleidbaarheid naar het oorspronkelijke RIS behouden blijft.

## Documenttypen

Het canonieke model bewaart altijd zowel de oorspronkelijke RIS-waarde als een genormaliseerde categorie.

Velden:

```text
document_type
normalized_document_type
normalized_document_type_label
```

Ontwerpprincipe:

```text
document_type = oorspronkelijke bronwaarde
normalized_document_type = compacte analysecategorie
normalized_document_type_label = gebruikersvriendelijk label
```

De bronwaarde wordt nooit overschreven.

Voorbeeld:

| document_type | normalized_document_type |
|---|---|
| Raadsvoorstel | proposal |
| Collegevoorstel (Intern) | proposal |
| Bijlage | attachment |
| Document ter kennisname (Inkomend) | notice |
