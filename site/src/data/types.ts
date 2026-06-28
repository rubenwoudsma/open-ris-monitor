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


export interface DashboardValueCount extends UnknownRecord {
  count?: number;
}

export interface DashboardYearCount extends DashboardValueCount {
  year?: string;
}

export interface DashboardDocumentTypeCount extends DashboardValueCount {
  document_type?: string;
}

export interface DashboardSizeBucketCount extends DashboardValueCount {
  bucket?: string;
}

export interface DashboardExport extends UnknownRecord {
  schema_version?: number;
  municipality_id?: string;
  generated_at?: string;
  dataset_generated_at?: string;
  profile?: string;
  totals?: Record<string, number>;
  coverage?: {
    documents_with_any_meeting_context?: number;
    documents_with_any_meeting_context_ratio?: number;
    documents_without_meeting_context?: number;
  };
  freshness?: {
    generated_at?: string;
    age_days?: number | null;
    status?: string;
  };
  document_file_size?: {
    known_count?: number;
    unknown_count?: number;
    total_bytes?: number;
    average_bytes?: number;
    largest_bytes?: number;
  };
  documents_by_year?: DashboardYearCount[];
  documents_by_type?: DashboardDocumentTypeCount[];
  documents_by_size_bucket?: DashboardSizeBucketCount[];
  meetings_by_year?: DashboardYearCount[];
  meeting_items_by_year?: DashboardYearCount[];
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
  url?: string;
  file_url?: string;
  document_url?: string;
  web_url?: string;
  external_url?: string;
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
  start_date?: string;
  publication_date?: string;
  source_id?: string | number;
  start_time?: string;
  title?: string;
  description?: string;
  dmu_name?: string;
  location?: string;
  status?: string;
  items?: AgendaItemRecord[];
}

export interface AgendaItemRecord extends UnknownRecord {
  id?: string;
  schema_version?: string | number;
  meeting_id?: string;
  meetingId?: string;
  meeting_source_id?: string | number;
  meeting_date?: string;
  date?: string;
  created_at?: string;
  session_id?: string;
  sessionId?: string;
  number?: string | number;
  title?: string;
  description?: string;
}


export interface OrganizationGroupRecord extends UnknownRecord {
  id?: string;
  source_id?: string | number;
  name?: string;
  type?: string;
  sort_order?: number | string;
}

export interface OrganizationPersonRecord extends UnknownRecord {
  id?: string;
  source_id?: string | number;
  first_name?: string;
  last_name?: string;
  preposition?: string;
  display_name?: string;
  salutation?: string;
  email?: string;
  active?: boolean;
}

export interface OrganizationRoleRecord extends UnknownRecord {
  id?: string;
  source_id?: string | number;
  name?: string;
  sort_order?: number | string;
  role_category?: string;
}

export interface OrganizationPositionRecord extends UnknownRecord {
  id?: string;
  source_id?: string | number;
  person_id?: string;
  person_source_id?: string | number;
  person_display_name?: string;
  role_id?: string;
  role_source_id?: string | number;
  role_name?: string;
  role_category?: string;
  start_date?: string;
  end_date?: string;
  sort_order?: number | string;
  active?: boolean;
}

export interface OrganizationGroupMembershipRecord extends UnknownRecord {
  id?: string;
  group_id?: string;
  group_source_id?: string | number;
  group_name?: string;
  group_type?: string;
  person_id?: string;
  person_source_id?: string | number;
  person_display_name?: string;
  active?: boolean;
}

export interface RelationRecord extends UnknownRecord {
  id?: string;
  schema_version?: string | number;
  meeting_id?: string;
  meetingId?: string;
  meeting_source_id?: string | number;
  meeting_date?: string;
  date?: string;
  created_at?: string;
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
  dashboard: DashboardExport | null;
  documents: DocumentRecord[];
  documentVersions: DocumentVersionRecord[];
  meetings: MeetingRecord[];
  agendaItems: AgendaItemRecord[];
  meetingDocumentRelations: RelationRecord[];
  meetingItemDocumentRelations: RelationRecord[];
  organizationGroups: OrganizationGroupRecord[];
  organizationPersons: OrganizationPersonRecord[];
  organizationRoles: OrganizationRoleRecord[];
  organizationPositions: OrganizationPositionRecord[];
  organizationGroupMemberships: OrganizationGroupMembershipRecord[];
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
