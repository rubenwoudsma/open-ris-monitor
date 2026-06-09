export type UnknownRecord = Record<string, unknown>;

export interface LatestExport extends UnknownRecord {
  municipality?: string;
  municipality_id?: string;
  documents_seen?: number;
  documents_normalized?: number;
  generated_at?: string;
  relations_enabled?: boolean;
  relations_summary?: {
    meetings_seen?: number;
    meeting_items_seen?: number;
  };
}

export interface DocumentRecord extends UnknownRecord {
  id?: string;
  schema_version?: string | number;
  source_id?: string | number;
  source_object_id?: string | number;
  title?: string;
  description?: string;
  filename?: string;
  document_type?: string;
  normalized_document_type?: string;
  normalized_document_type_label?: string;
  download_url?: string;
  source_url?: string;
  publication_datetime?: string;
  publication_date?: string;
  date_published?: string;
  document_date?: string;
  date?: string;
  retrieved_at?: string;
  size_bytes?: number | string;
  file_size_bytes?: number | string;
  file_size?: number | string;
  file_name?: string;
  raw?: UnknownRecord;
}

export interface DocumentVersionRecord extends UnknownRecord {
  id?: string;
  document_id?: string;
  source_id?: string | number;
  retrieved_at?: string;
}

export interface MeetingRecord extends UnknownRecord {
  id?: string;
  schema_version?: string | number;
  date?: string;
  start_time?: string;
  title?: string;
  description?: string;
  dmu_name?: string;
  items?: AgendaItemRecord[];
}

export interface AgendaItemRecord extends UnknownRecord {
  id?: string;
  schema_version?: string | number;
  meeting_id?: string;
  meetingId?: string;
  session_id?: string;
  sessionId?: string;
  number?: string | number;
  title?: string;
  description?: string;
}

export interface RelationRecord extends UnknownRecord {
  id?: string;
  schema_version?: string | number;
  meeting_id?: string;
  meetingId?: string;
  meeting_item_id?: string;
  meetingItemId?: string;
  item_id?: string;
  document_id?: string;
  document_source_id?: string | number;
  document_object_id?: string | number;
  document_url?: string;
  download_url?: string;
  source_url?: string;
  document?: UnknownRecord;
}

export interface PublicDataSet {
  latest: LatestExport;
  documents: DocumentRecord[];
  documentVersions: DocumentVersionRecord[];
  meetings: MeetingRecord[];
  agendaItems: AgendaItemRecord[];
  meetingDocumentRelations: RelationRecord[];
  meetingItemDocumentRelations: RelationRecord[];
}

export interface RelationIndexes {
  documentsById: Map<string, DocumentRecord>;
  meetingsById: Map<string, MeetingRecord>;
  agendaItemsById: Map<string, AgendaItemRecord>;
  meetingIdsByDocumentId: Map<string, string[]>;
  agendaItemIdsByDocumentId: Map<string, string[]>;
  documentIdsByMeetingId: Map<string, string[]>;
  documentIdsByAgendaItemId: Map<string, string[]>;
  agendaItemIdsByMeetingId: Map<string, string[]>;
}
