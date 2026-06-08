import type { AgendaItemRecord, DocumentRecord, DocumentVersionRecord, LatestExport, MeetingRecord, PublicDataSet, RelationRecord } from "./types";
import { loadJson, loadJsonl, loadOptionalJsonl } from "./jsonl";

export const DATA_BASE = "../data/public";

export async function loadPublicData(basePath = DATA_BASE): Promise<PublicDataSet> {
  const [latest, documents, documentVersions, meetings, agendaItems, meetingDocumentRelations, meetingItemDocumentRelations] = await Promise.all([
    loadJson<LatestExport>(`${basePath}/latest.json`),
    loadJsonl<DocumentRecord>(`${basePath}/documents.jsonl`),
    loadOptionalJsonl<DocumentVersionRecord>(`${basePath}/document_versions.jsonl`),
    loadOptionalJsonl<MeetingRecord>(`${basePath}/meetings.jsonl`),
    loadOptionalJsonl<AgendaItemRecord>(`${basePath}/meeting_items.jsonl`),
    loadOptionalJsonl<RelationRecord>(`${basePath}/meeting_documents.jsonl`),
    loadOptionalJsonl<RelationRecord>(`${basePath}/meeting_item_documents.jsonl`),
  ]);

  return {
    latest,
    documents,
    documentVersions,
    meetings,
    agendaItems,
    meetingDocumentRelations,
    meetingItemDocumentRelations,
  };
}
