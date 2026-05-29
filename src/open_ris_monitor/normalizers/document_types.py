"""Document type normalization helpers.

The source RIS document type is always preserved as ``document_type``.
These helpers add a compact analytical type that is easier to filter and use
in quality reports.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedDocumentType:
    """Compact document type classification."""

    value: str
    label: str


TYPE_LABELS: dict[str, str] = {
    "agenda": "Agenda",
    "amendment": "Amendement",
    "announcement": "Mededeling",
    "answer": "Beantwoording",
    "attachment": "Bijlage",
    "commitment": "Toezegging",
    "decision": "Besluit",
    "incoming_document": "Ingekomen stuk",
    "invitation": "Uitnodiging",
    "memo_or_advice": "Memo of advies",
    "minutes_or_summary": "Notulen, verslag of resume",
    "motion": "Motie",
    "notice": "Kennisgeving of ter kennisname",
    "objection_or_response": "Bezwaar, klacht of zienswijze",
    "other": "Overig",
    "policy_or_plan": "Beleid, plan of nota",
    "proposal": "Voorstel",
    "question": "Vraag",
    "report": "Rapportage of evaluatie",
    "request": "Verzoek of aanvullende gegevens",
    "unknown": "Onbekend",
}

# Explicit mappings based on the Huizen RIS document type profile. This list is
# intentionally source-value based, so the original RIS value remains traceable.
EXPLICIT_TYPE_MAPPING: dict[str, str] = {
    "Aanvullende gegevens": "request",
    "Advies (Intern)": "memo_or_advice",
    "Agenda": "agenda",
    "Amendementen": "amendment",
    "Beantwoording door B&W (Uitgaand)": "answer",
    "Beleidsnota's Algemene dekkingsmiddelen en onvoorzien": "policy_or_plan",
    "Beleidsnota's Programma 2 Openbare orde en veiligheid": "policy_or_plan",
    "Besluit": "decision",
    "Besluitenlijst (Intern)": "decision",
    "Besluitenlijst raad": "decision",
    "Besluitenlijsten": "decision",
    "Bezwaarschrift (Inkomend)": "objection_or_response",
    "Bijlage": "attachment",
    "Collegevoorstel (BBV)": "proposal",
    "Collegevoorstel (Intern)": "proposal",
    "Conceptbesluit (Inkomend)": "decision",
    "Document ter kennisname (Inkomend)": "notice",
    "Evaluatie (Intern)": "report",
    "Financiele overzichten commissie": "report",
    "Financiële overzichten commissie": "report",
    "Ingekomen stuk": "incoming_document",
    "Kennisgeving": "notice",
    "Kennisgeving (Inkomend)": "notice",
    "Klacht (Inkomend)": "objection_or_response",
    "Mededelingen": "announcement",
    "Memo": "memo_or_advice",
    "Moties": "motion",
    "Notulen ABM": "minutes_or_summary",
    "Notulen Fysiek Domein": "minutes_or_summary",
    "Notulen Raad": "minutes_or_summary",
    "Notulen Sociaal Domein": "minutes_or_summary",
    "Notulen gecombineerde commissies": "minutes_or_summary",
    "Notulen t/m april 2021": "minutes_or_summary",
    "Omgevingswet": "policy_or_plan",
    "Onbekend": "unknown",
    "Onderzoeksstuk (Intern)": "report",
    "Overig": "other",
    "Overig stuk inkomend": "other",
    "Overig stuk intern": "other",
    "Overig stuk uitgaand": "other",
    "Overzicht mededelingen (Intern)": "announcement",
    "Overzicht stand van zaken": "report",
    "Principeverzoek bestemmingsplanwijziging (Inkomend)": "policy_or_plan",
    "Raadsbesluit": "decision",
    "Raadsvoorstel": "proposal",
    "Raadsvoorstel (Intern)": "proposal",
    "Raadsvragen": "question",
    "Rapport (Intern)": "report",
    "Rapport van bevindingen (Inkomend)": "report",
    "Rapportage (Intern)": "report",
    "Resume ABM": "minutes_or_summary",
    "Resumé ABM": "minutes_or_summary",
    "Resume Fysiek Domein": "minutes_or_summary",
    "Resumé Fysiek Domein": "minutes_or_summary",
    "Resume Sociaal Domein": "minutes_or_summary",
    "Resumé Sociaal Domein": "minutes_or_summary",
    "Resume gecombineerde commissies": "minutes_or_summary",
    "Resumé gecombineerde commissies": "minutes_or_summary",
    "Resumes": "minutes_or_summary",
    "Resumés": "minutes_or_summary",
    "Stukken ter kennisname": "notice",
    "Toezeggingen": "commitment",
    "Toezeggingenlijst (Intern)": "commitment",
    "Uitnodiging (Inkomend)": "invitation",
    "Uitnodigingen": "invitation",
    "Uitnodigingen (Intern)": "invitation",
    "Vastgesteld plan (Intern)": "policy_or_plan",
    "Verslag": "minutes_or_summary",
    "Verzoek om aanvullende gegevens ROW (Uitgaand)": "request",
    "Verzoek om informatie (Inkomend)": "request",
    "Voorjaarsnota (Intern)": "policy_or_plan",
    "Voorstel (Intern)": "proposal",
    "Vraag van raadslid (Inkomend)": "question",
    "Vragen van raadsleden": "question",
    "Zienswijze (Inkomend)": "objection_or_response",
}


def normalize_document_type(source_type: str | None) -> NormalizedDocumentType:
    """Return a compact document type for a source RIS document type."""

    if source_type is None or not str(source_type).strip():
        value = "unknown"
    else:
        cleaned = str(source_type).strip()
        value = EXPLICIT_TYPE_MAPPING.get(cleaned)
        if value is None:
            lowered = cleaned.lower()
            value = _infer_type_from_text(lowered)
    return NormalizedDocumentType(value=value, label=TYPE_LABELS[value])


def _infer_type_from_text(lowered: str) -> str:
    """Fallback rules for unseen but semantically obvious source types."""

    if "onbekend" in lowered:
        return "unknown"
    if "agenda" in lowered:
        return "agenda"
    if "bijlage" in lowered:
        return "attachment"
    if "amendement" in lowered:
        return "amendment"
    if "motie" in lowered:
        return "motion"
    if "raadsvraag" in lowered or "vragen van raadsleden" in lowered or "vraag van raadslid" in lowered:
        return "question"
    if "raadsvoorstel" in lowered or "collegevoorstel" in lowered or "voorstel" in lowered:
        return "proposal"
    if "besluit" in lowered or "besluitenlijst" in lowered:
        return "decision"
    if "mededeling" in lowered:
        return "announcement"
    if "ingekomen" in lowered and "stuk" in lowered:
        return "incoming_document"
    if "kennisgeving" in lowered or "ter kennisname" in lowered:
        return "notice"
    if "notulen" in lowered or "resum" in lowered or "verslag" in lowered:
        return "minutes_or_summary"
    if "toezegging" in lowered:
        return "commitment"
    if "uitnodiging" in lowered:
        return "invitation"
    if "bezwaar" in lowered or "zienswijze" in lowered or "klacht" in lowered:
        return "objection_or_response"
    if "verzoek" in lowered or "aanvullende gegevens" in lowered:
        return "request"
    if "rapport" in lowered or "evaluatie" in lowered or "onderzoek" in lowered:
        return "report"
    if "advies" in lowered or "memo" in lowered:
        return "memo_or_advice"
    if "beleid" in lowered or "nota" in lowered or "plan" in lowered or "omgevingswet" in lowered:
        return "policy_or_plan"
    if "overig" in lowered:
        return "other"
    return "unknown"
