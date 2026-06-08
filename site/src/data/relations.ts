import type { AgendaItemRecord, DocumentRecord, MeetingRecord, RelationIndexes, RelationRecord } from "./types";
import { pick } from "../ui/format";

function addValue(set: Set<string>, value: unknown): void {
  const text = pick(value);
  if (text) set.add(text);
}

function addUnique(map: Map<string, string[]>, key: string, value: string): void {
  if (!key || !value) return;
  const list = map.get(key) ?? [];
  if (!list.includes(value)) list.push(value);
  map.set(key, list);
}

export function getRecordId(record: Record<string, unknown>): string {
  return pick(record.id, record.meeting_id, record.meeting_item_id, record.document_id, record.source_id, record.source_object_id);
}

export function getDocumentIdentifiers(documentRecord: DocumentRecord): string[] {
  const identifiers = new Set<string>();
  addValue(identifiers, documentRecord.id);
  addValue(identifiers, documentRecord.source_id);
  addValue(identifiers, documentRecord.source_object_id);
  addValue(identifiers, documentRecord.download_url);
  addValue(identifiers, documentRecord.source_url);

  if (documentRecord.raw && typeof documentRecord.raw === "object") {
    addValue(identifiers, documentRecord.raw.id);
    addValue(identifiers, documentRecord.raw.objectId);
    addValue(identifiers, documentRecord.raw.object_id);
    addValue(identifiers, documentRecord.raw.downloadUrl);
    addValue(identifiers, documentRecord.raw.download_url);
  }

  if (documentRecord.id && documentRecord.source_id && String(documentRecord.id).includes("-document-")) {
    const prefix = String(documentRecord.id).split("-document-")[0];
    addValue(identifiers, `${prefix}-document-${documentRecord.source_id}`);
  }

  return [...identifiers];
}

export function getRelationDocumentIdentifiers(relation: RelationRecord): string[] {
  const identifiers = new Set<string>();
  addValue(identifiers, relation.document_id);
  addValue(identifiers, relation.document_source_id);
  addValue(identifiers, relation.document_object_id);
  addValue(identifiers, relation.document_url);
  addValue(identifiers, relation.download_url);
  addValue(identifiers, relation.source_url);

  if (relation.document && typeof relation.document === "object") {
    addValue(identifiers, relation.document.id);
    addValue(identifiers, relation.document.objectId);
    addValue(identifiers, relation.document.object_id);
    addValue(identifiers, relation.document.downloadUrl);
    addValue(identifiers, relation.document.download_url);
  }

  return [...identifiers];
}

function resolveDocumentId(indexes: RelationIndexes, relation: RelationRecord): string {
  for (const identifier of getRelationDocumentIdentifiers(relation)) {
    if (indexes.documentsById.has(identifier)) return identifier;
  }
  return pick(relation.document_id, relation.document_source_id, relation.document_object_id);
}

export function buildRelationIndexes(
  documents: DocumentRecord[],
  meetings: MeetingRecord[],
  agendaItems: AgendaItemRecord[],
  meetingDocumentRelations: RelationRecord[],
  meetingItemDocumentRelations: RelationRecord[],
): RelationIndexes {
  const indexes: RelationIndexes = {
    documentsById: new Map(),
    meetingsById: new Map(),
    agendaItemsById: new Map(),
    meetingIdsByDocumentId: new Map(),
    agendaItemIdsByDocumentId: new Map(),
    documentIdsByMeetingId: new Map(),
    documentIdsByAgendaItemId: new Map(),
    agendaItemIdsByMeetingId: new Map(),
  };

  for (const documentRecord of documents) {
    for (const identifier of getDocumentIdentifiers(documentRecord)) {
      indexes.documentsById.set(identifier, documentRecord);
    }
  }

  for (const meeting of meetings) {
    const id = getRecordId(meeting);
    if (id) indexes.meetingsById.set(id, meeting);
  }

  for (const item of agendaItems) {
    const itemId = getRecordId(item);
    const meetingId = pick(item.meeting_id, item.meetingId, item.session_id, item.sessionId);
    if (itemId) indexes.agendaItemsById.set(itemId, item);
    if (meetingId && itemId) addUnique(indexes.agendaItemIdsByMeetingId, meetingId, itemId);
  }

  for (const relation of meetingDocumentRelations) {
    const meetingId = pick(relation.meeting_id, relation.meetingId);
    const documentId = resolveDocumentId(indexes, relation);
    addUnique(indexes.meetingIdsByDocumentId, documentId, meetingId);
    addUnique(indexes.documentIdsByMeetingId, meetingId, documentId);
  }

  for (const relation of meetingItemDocumentRelations) {
    const itemId = pick(relation.meeting_item_id, relation.meetingItemId, relation.item_id);
    const relationMeetingId = pick(relation.meeting_id, relation.meetingId);
    const item = itemId ? indexes.agendaItemsById.get(itemId) : undefined;
    const meetingId = relationMeetingId || pick(item?.meeting_id, item?.meetingId, item?.session_id, item?.sessionId);
    const documentId = resolveDocumentId(indexes, relation);

    addUnique(indexes.agendaItemIdsByDocumentId, documentId, itemId);
    addUnique(indexes.documentIdsByAgendaItemId, itemId, documentId);
    addUnique(indexes.meetingIdsByDocumentId, documentId, meetingId);
    addUnique(indexes.documentIdsByMeetingId, meetingId, documentId);
    addUnique(indexes.agendaItemIdsByMeetingId, meetingId, itemId);
  }

  return indexes;
}
