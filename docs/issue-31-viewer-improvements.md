# Issue 31, viewer verbeteren na relationele exports

Deze PR houdt de viewerwijziging bewust klein. De relationele public exports worden al geladen, maar de hoofdweergave was nog te technisch en de documenttabel werd gedomineerd door lange bestandsnamen.

## Scope

- De exportmetadata is verplaatst naar een inklapbaar blok in de footer.
- De JSON en JSONL links blijven beschikbaar voor controle en debugging, maar staan niet meer dominant bovenaan.
- Het filterblok is over de volledige breedte uitgelijnd.
- De documenttabel gebruikt vaste kolombreedtes.
- De datum, grootte en downloadkolommen blijven compact.
- De titelkolom krijgt meer ruimte.
- Lange bestandsnamen breken af binnen hun kolom.
- Relationele context wordt compacter onder de documenttitel getoond.
- De datumsortering gebruikt echte datums en valt terug op source_id wanneer meerdere documenten dezelfde datum hebben.

## Bewust buiten scope

- Agenda- en vergaderingbrowser, issue 34.
- Verdere documenttype-normalisatie, issue 21.
- Kwaliteitsrapportage, issue 13.
- Aanpassing aan de harveststrategie of public exports.


## Follow-up fix in v3

Long technical filenames from source systems can contain underscores and other separators without spaces. The viewer now inserts safe soft break opportunities in the rendered filename and applies defensive wrapping to the file column so filenames cannot force the other table columns to shrink.

The observation that the current public harvest mostly shows 2018 documents is not changed here. That is likely caused by bounded harvesting using the source system's default document order and should be handled in a separate harvest/data selection issue.
