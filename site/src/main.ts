import { loadPublicData } from "./data/loaders.js";
import { buildRelationIndexes, getDocumentIdentifiers, getRecordId } from "./data/relations.js";
import type {
  AgendaItemRecord,
  DashboardDocumentTypeCount,
  DashboardSizeBucketCount,
  DashboardYearCount,
  DocumentRecord,
  DocumentVersionRecord,
  MeetingRecord,
  OrganizationGroupMembershipRecord,
  OrganizationGroupRecord,
  OrganizationPersonRecord,
  OrganizationPositionRecord,
  OrganizationRoleRecord,
  PublicDataSet,
  RelationIndexes,
  UnknownRecord,
} from "./data/types.js";
import { formatBytes, formatDate, formatDateTime, pick, safeUrl, text, timestamp } from "./ui/format.js";

interface ViewerState {
  data: PublicDataSet | null;
  indexes: RelationIndexes | null;
  filteredDocuments: DocumentRecord[];
  selectedDocumentId: string | null;
  selectedMeetingId: string | null;
  currentPage: number;
  pageSize: number;
  sortMode: string;
  meetingQuery: string;
  meetingSortMode: "date-desc" | "date-asc";
  meetingDateFilter: "all" | "past" | "future";
  meetingCurrentPage: number;
  meetingPageSize: number;
  organizationRoleFilter: string;
  organizationStatusFilter: "active" | "inactive" | "all";
  organizationGroupFilter: string;
  organizationGroupTypeFilter: string;
  activeView: "documents" | "meetings" | "organization" | "dashboard";
}

interface DerivedCaches {
  documentRelationLabelsByKey: Map<string, string[]>;
  documentSearchBlobByKey: Map<string, string>;
  meetingSearchBlobById: Map<string, string>;
  filteredMeetingsByKey: Map<string, MeetingRecord[]>;
  personGroupsByPersonId: Map<string, string[]>;
  personGroupIdsByPersonId: Map<string, string[]>;
}

type RequiredElements = {
  statusMessage: HTMLElement;
  municipality: HTMLElement;
  documentsSeen: HTMLElement;
  documentsNormalized: HTMLElement;
  generatedAt: HTMLElement;
  municipalityCopy: HTMLElement;
  generatedAtCopy: HTMLElement;
  meetingsCount: HTMLElement;
  agendaItemsCount: HTMLElement;
  linkedDocumentsCount: HTMLElement;
  organizationPositionsCount: HTMLElement;
  dataQualityNotice: HTMLElement;
  dashboardView: HTMLElement;
  documentsView: HTMLElement;
  meetingsView: HTMLElement;
  organizationView: HTMLElement;
  navDashboard: HTMLAnchorElement;
  navDocuments: HTMLAnchorElement;
  navMeetings: HTMLAnchorElement;
  navOrganization: HTMLAnchorElement;
  searchInput: HTMLInputElement;
  typeFilter: HTMLSelectElement;
  sortSelect: HTMLSelectElement;
  pageSizeSelect: HTMLSelectElement;
  resultCount: HTMLElement;
  visibleDocumentsCount: HTMLElement;
  tableBody: HTMLElement;
  previousTop: HTMLButtonElement;
  nextTop: HTMLButtonElement;
  pageInfoTop: HTMLElement;
  previousBottom: HTMLButtonElement;
  nextBottom: HTMLButtonElement;
  pageInfoBottom: HTMLElement;
  documentDetail: HTMLElement;
  documentDetailTitle: HTMLElement;
  documentDetailBody: HTMLElement;
  clearDocumentSelection: HTMLButtonElement;
  meetingSearchInput: HTMLInputElement;
  meetingSortSelect: HTMLSelectElement;
  meetingDateFilter: HTMLSelectElement;
  meetingPageSizeSelect: HTMLSelectElement;
  visibleMeetingsCount: HTMLElement;
  meetingsResultCount: HTMLElement;
  meetingsTableBody: HTMLElement;
  previousMeetingTop: HTMLButtonElement;
  nextMeetingTop: HTMLButtonElement;
  meetingPageInfoTop: HTMLElement;
  previousMeetingBottom: HTMLButtonElement;
  nextMeetingBottom: HTMLButtonElement;
  meetingPageInfoBottom: HTMLElement;
  meetingDetail: HTMLElement;
  meetingDetailTitle: HTMLElement;
  meetingDetailBody: HTMLElement;
  clearMeetingSelection: HTMLButtonElement;
  organizationSummaryCount: HTMLElement;
  organizationSummaryCards: HTMLElement;
  organizationGroupsList: HTMLElement;
  organizationRoleFilter: HTMLSelectElement;
  organizationStatusFilter: HTMLSelectElement;
  organizationGroupFilter: HTMLSelectElement;
  organizationGroupTypeFilter: HTMLSelectElement;
  organizationPositionsBody: HTMLElement;
  dashboardSummaryCards: HTMLElement;
  dashboardCharts: HTMLElement;
  dashboardFreshness: HTMLElement;
  dashboardExplanation: HTMLElement;
};

const state: ViewerState = {
  data: null,
  indexes: null,
  filteredDocuments: [],
  selectedDocumentId: null,
  selectedMeetingId: null,
  currentPage: 1,
  pageSize: 50,
  sortMode: "date-desc",
  meetingQuery: "",
  meetingSortMode: "date-desc",
  meetingDateFilter: "all",
  meetingCurrentPage: 1,
  meetingPageSize: 25,
  organizationRoleFilter: "",
  organizationStatusFilter: "active",
  organizationGroupFilter: "",
  organizationGroupTypeFilter: "fractie",
  activeView: "documents",
};

const derivedCaches: DerivedCaches = {
  documentRelationLabelsByKey: new Map<string, string[]>(),
  documentSearchBlobByKey: new Map<string, string>(),
  meetingSearchBlobById: new Map<string, string>(),
  filteredMeetingsByKey: new Map<string, MeetingRecord[]>(),
  personGroupsByPersonId: new Map<string, string[]>(),
  personGroupIdsByPersonId: new Map<string, string[]>(),
};

function clearDerivedCaches(): void {
  derivedCaches.documentRelationLabelsByKey.clear();
  derivedCaches.documentSearchBlobByKey.clear();
  derivedCaches.meetingSearchBlobById.clear();
  derivedCaches.filteredMeetingsByKey.clear();
  derivedCaches.personGroupsByPersonId.clear();
  derivedCaches.personGroupIdsByPersonId.clear();
}

function byId<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) throw new Error(`HTML mist verwacht element: #${id}`);
  return element as T;
}

const elements: RequiredElements = {
  statusMessage: byId("status-message"),
  municipality: byId("municipality"),
  documentsSeen: byId("documents-seen"),
  documentsNormalized: byId("documents-normalized"),
  generatedAt: byId("generated-at"),
  municipalityCopy: byId("municipality-copy"),
  generatedAtCopy: byId("generated-at-copy"),
  meetingsCount: byId("meetings-count"),
  agendaItemsCount: byId("agenda-items-count"),
  linkedDocumentsCount: byId("linked-documents-count"),
  organizationPositionsCount: byId("organization-positions-count"),
  dataQualityNotice: byId("data-quality-notice"),
  dashboardView: byId("dashboard-view"),
  documentsView: byId("documents-view"),
  meetingsView: byId("meetings-view"),
  organizationView: byId("organization-view"),
  navDashboard: byId("nav-dashboard"),
  navDocuments: byId("nav-documents"),
  navMeetings: byId("nav-meetings"),
  navOrganization: byId("nav-organization"),
  searchInput: byId("search-input"),
  typeFilter: byId("type-filter"),
  sortSelect: byId("sort-select"),
  pageSizeSelect: byId("page-size-select"),
  resultCount: byId("result-count"),
  visibleDocumentsCount: byId("visible-documents-count"),
  tableBody: byId("documents-table-body"),
  previousTop: byId("previous-page-top"),
  nextTop: byId("next-page-top"),
  pageInfoTop: byId("page-info-top"),
  previousBottom: byId("previous-page-bottom"),
  nextBottom: byId("next-page-bottom"),
  pageInfoBottom: byId("page-info-bottom"),
  documentDetail: byId("document-detail"),
  documentDetailTitle: byId("document-detail-title"),
  documentDetailBody: byId("document-detail-body"),
  clearDocumentSelection: byId("clear-document-selection"),
  meetingSearchInput: byId("meeting-search-input"),
  meetingSortSelect: byId("meeting-sort-select"),
  meetingDateFilter: byId("meeting-date-filter"),
  meetingPageSizeSelect: byId("meeting-page-size-select"),
  visibleMeetingsCount: byId("visible-meetings-count"),
  meetingsResultCount: byId("meetings-result-count"),
  meetingsTableBody: byId("meetings-table-body"),
  previousMeetingTop: byId("previous-meeting-page-top"),
  nextMeetingTop: byId("next-meeting-page-top"),
  meetingPageInfoTop: byId("meeting-page-info-top"),
  previousMeetingBottom: byId("previous-meeting-page-bottom"),
  nextMeetingBottom: byId("next-meeting-page-bottom"),
  meetingPageInfoBottom: byId("meeting-page-info-bottom"),
  meetingDetail: byId("meeting-detail"),
  meetingDetailTitle: byId("meeting-detail-title"),
  meetingDetailBody: byId("meeting-detail-body"),
  clearMeetingSelection: byId("clear-meeting-selection"),
  organizationSummaryCount: byId("organization-summary-count"),
  organizationSummaryCards: byId("organization-summary-cards"),
  organizationGroupsList: byId("organization-groups-list"),
  organizationRoleFilter: byId("organization-role-filter"),
  organizationStatusFilter: byId("organization-status-filter"),
  organizationGroupFilter: byId("organization-group-filter"),
  organizationGroupTypeFilter: byId("organization-group-type-filter"),
  organizationPositionsBody: byId("organization-positions-body"),
  dashboardSummaryCards: byId("dashboard-summary-cards"),
  dashboardCharts: byId("dashboard-charts"),
  dashboardFreshness: byId("dashboard-freshness"),
  dashboardExplanation: byId("dashboard-explanation"),
};

function unavailable(reason = "Niet beschikbaar in export"): string {
  return reason;
}

function uniqueValues(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

function getDocumentId(documentRecord: DocumentRecord): string {
  return getDocumentIdentifiers(documentRecord)[0] ?? "";
}

function documentIds(documentRecord: DocumentRecord): string[] {
  return uniqueValues(getDocumentIdentifiers(documentRecord));
}

function getDocumentTitle(documentRecord: DocumentRecord): string {
  return pick(documentRecord.title, documentRecord.description, documentRecord.filename) || "Geen titel";
}

function getDocumentCacheKey(documentRecord: DocumentRecord): string {
  return documentIds(documentRecord).join("|") || getDocumentTitle(documentRecord);
}

function getDocumentDate(documentRecord: DocumentRecord): string {
  return pick(
    documentRecord.publication_datetime,
    documentRecord.date_published,
    documentRecord.publication_date,
    documentRecord.document_date,
    documentRecord.date,
    documentRecord.retrieved_at,
  );
}

function getMeetingId(meeting: MeetingRecord): string {
  return getRecordId(meeting) || pick(meeting.id, meeting.source_id, meeting.source_object_id);
}

function getMeetingTitle(meeting: MeetingRecord | undefined): string {
  return pick(meeting?.description, meeting?.title, meeting?.dmu_name) || "Vergadering zonder titel";
}

function getMeetingDate(meeting: MeetingRecord | undefined): string {
  return pick(meeting?.date, meeting?.start_time);
}

function getAgendaItemId(item: AgendaItemRecord): string {
  return getRecordId(item) || pick(item.id, item.meeting_item_id, item.source_id, item.source_object_id);
}

function getAgendaItemTitle(item: AgendaItemRecord | undefined): string {
  const number = pick(item?.number);
  const title = pick(item?.title, item?.description) || "Agendapunt zonder titel";
  return number ? `${number}. ${title}` : title;
}

function getAgendaItemMeetingId(item: AgendaItemRecord | undefined): string {
  return pick(item?.meeting_id, item?.meetingId, item?.session_id, item?.sessionId);
}

function isUnknownType(value: string): boolean {
  const normalized = value.trim().toLowerCase();
  return !normalized || normalized === "unknown" || normalized === "onbekend";
}

function pickFromRaw(record: DocumentRecord, ...keys: string[]): string {
  if (!record.raw || typeof record.raw !== "object") return "";
  for (const key of keys) {
    const picked = pick(record.raw[key]);
    if (picked) return picked;
  }
  return "";
}

function pickNestedRaw(record: DocumentRecord, objectKey: string, ...keys: string[]): string {
  const nested = record.raw?.[objectKey];
  if (!nested || typeof nested !== "object") return "";
  const nestedRecord = nested as UnknownRecord;
  for (const key of keys) {
    const picked = pick(nestedRecord[key]);
    if (picked) return picked;
  }
  return "";
}

function getCompactType(documentRecord: DocumentRecord): string {
  const normalized = pick(documentRecord.normalized_document_type, documentRecord.type);
  if (!isUnknownType(normalized)) return normalized;
  return "unknown";
}

function getCompactTypeLabel(documentRecord: DocumentRecord): string {
  const normalizedLabel = pick(documentRecord.normalized_document_type_label);
  if (!isUnknownType(normalizedLabel)) return normalizedLabel;
  const normalizedType = pick(documentRecord.normalized_document_type, documentRecord.type);
  if (!isUnknownType(normalizedType)) return normalizedType;
  return unavailable();
}

function getSourceDocumentType(documentRecord: DocumentRecord): string {
  const sourceType = pick(
    documentRecord.document_type,
    pickFromRaw(documentRecord, "document_type", "documentType", "source_document_type", "sourceDocumentType"),
  );
  const compactType = getCompactType(documentRecord);
  const compactTypeLabel = getCompactTypeLabel(documentRecord);
  let documentTypeLabel = sourceType;
  if (sourceType === compactType || sourceType === compactTypeLabel) {
    documentTypeLabel = sourceType;
  }
  return documentTypeLabel || unavailable("Geen bronmetadata");
}

function getDocumentFilename(documentRecord: DocumentRecord): string {
  return pick(
    documentRecord.filename,
    documentRecord.file_name,
    documentRecord.name,
    documentRecord.display_name,
    documentRecord.original_filename,
    pickFromRaw(documentRecord, "filename", "file_name", "fileName", "name", "displayName", "originalFilename"),
    pickNestedRaw(documentRecord, "file", "filename", "fileName", "name"),
  );
}

function getDocumentSize(documentRecord: DocumentRecord): unknown {
  return [
    documentRecord.file_size_bytes,
    documentRecord.size_bytes,
    documentRecord.file_size,
    documentRecord.filesize,
    documentRecord.size,
    documentRecord.bytes,
    documentRecord.content_length,
    pickFromRaw(documentRecord, "file_size_bytes", "size_bytes", "file_size", "fileSize", "filesize", "size", "bytes", "contentLength"),
    pickNestedRaw(documentRecord, "file", "size", "bytes", "size_bytes", "fileSize"),
  ].find((value) => pick(value));
}

function formatDocumentSize(documentRecord: DocumentRecord): string {
  const formatted = formatBytes(getDocumentSize(documentRecord));
  return formatted === "-" ? unavailable("Geen bestandsgrootte beschikbaar") : formatted;
}

function getDocumentUrl(documentRecord: DocumentRecord): string | null {
  return safeUrl(
    pick(
      documentRecord.download_url,
      documentRecord.source_url,
      documentRecord.url,
      documentRecord.file_url,
      documentRecord.document_url,
      documentRecord.web_url,
      documentRecord.external_url,
      pickFromRaw(documentRecord, "download_url", "downloadUrl", "source_url", "sourceUrl", "url", "fileUrl", "documentUrl", "webUrl"),
      pickNestedRaw(documentRecord, "file", "url", "downloadUrl", "download_url", "href"),
    ),
  );
}

function relatedMeetingIds(documentRecord: DocumentRecord): string[] {
  if (!state.indexes) return [];
  return uniqueValues(documentIds(documentRecord).flatMap((id) => state.indexes?.meetingIdsByDocumentId.get(id) ?? []));
}

function relatedAgendaItemIds(documentRecord: DocumentRecord): string[] {
  if (!state.indexes) return [];
  return uniqueValues(documentIds(documentRecord).flatMap((id) => state.indexes?.agendaItemIdsByDocumentId.get(id) ?? []));
}

function relationLabelsForDocument(documentRecord: DocumentRecord): string[] {
  if (!state.indexes) return [];
  const cacheKey = getDocumentCacheKey(documentRecord);
  const cached = derivedCaches.documentRelationLabelsByKey.get(cacheKey);
  if (cached) return cached;

  const labels: string[] = [];
  for (const meetingId of relatedMeetingIds(documentRecord)) {
    const meeting = state.indexes.meetingsById.get(meetingId);
    labels.push([getMeetingTitle(meeting), formatDate(getMeetingDate(meeting))].filter(Boolean).join(", "));
  }
  for (const itemId of relatedAgendaItemIds(documentRecord)) {
    const item = state.indexes.agendaItemsById.get(itemId);
    labels.push(getAgendaItemTitle(item));
  }
  const uniqueLabels = uniqueValues(labels);
  derivedCaches.documentRelationLabelsByKey.set(cacheKey, uniqueLabels);
  return uniqueLabels;
}

function relatedVersions(documentRecord: DocumentRecord): DocumentVersionRecord[] {
  const ids = new Set(documentIds(documentRecord));
  return (state.data?.documentVersions ?? []).filter((version) => {
    const versionDocumentId = pick(version.document_id, version.source_id);
    return versionDocumentId ? ids.has(versionDocumentId) : false;
  });
}

function agendaItemIdsForMeeting(meetingId: string): string[] {
  if (!state.indexes) return [];
  return uniqueValues(state.indexes.agendaItemIdsByMeetingId.get(meetingId) ?? []);
}

function linkedDocumentIdsForMeeting(meetingId: string): string[] {
  if (!state.indexes) return [];
  return uniqueValues(state.indexes.documentIdsByMeetingId.get(meetingId) ?? []);
}

function linkedDocumentIdsForAgendaItem(itemId: string): string[] {
  if (!state.indexes) return [];
  return uniqueValues(state.indexes.documentIdsByAgendaItemId.get(itemId) ?? []);
}

function findDocumentById(documentId: string): DocumentRecord | undefined {
  if (!documentId) return undefined;
  return state.indexes?.documentsById.get(documentId) ?? state.data?.documents.find((documentRecord) => documentIds(documentRecord).includes(documentId));
}

function primaryDocumentHashId(documentRecord: DocumentRecord): string {
  return getDocumentId(documentRecord) || documentIds(documentRecord)[0] || "";
}

function documentHashFor(documentRecord: DocumentRecord): string {
  const documentId = primaryDocumentHashId(documentRecord);
  return documentId ? `#documents/${encodeURIComponent(documentId)}` : "#documents";
}

function documentIdFromHash(): string {
  const prefix = "#documents/";
  if (!window.location.hash.startsWith(prefix)) return "";
  return decodeURIComponent(window.location.hash.slice(prefix.length));
}

function updateHash(nextHash: string): void {
  if (window.location.hash !== nextHash) history.pushState(null, "", nextHash);
}

function findMeetingById(meetingId: string): MeetingRecord | undefined {
  if (!meetingId) return undefined;
  return state.data?.meetings.find((meeting) => getMeetingId(meeting) === meetingId) ?? state.indexes?.meetingsById.get(meetingId);
}

function createCell(value: string): HTMLTableCellElement {
  const cell = document.createElement("td");
  cell.textContent = value;
  return cell;
}

function appendDefinition(list: HTMLDListElement, label: string, value: string): void {
  const wrapper = document.createElement("div");
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value;
  wrapper.append(term, description);
  list.appendChild(wrapper);
}

function createDocumentAction(documentRecord: DocumentRecord, label = "Details", fromMeetingDetail = false): HTMLButtonElement {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "secondary-button";
  button.textContent = label;
  button.addEventListener("click", () => {
    if (fromMeetingDetail) {
      focusDocumentFromMeetingDetail(documentRecord);
      return;
    }
    focusDocumentFromDocumentList(documentRecord);
  });
  return button;
}

function ensureDocumentVisible(documentRecord: DocumentRecord): void {
  const documentId = primaryDocumentHashId(documentRecord);
  let index = state.filteredDocuments.findIndex((record) => documentIds(record).includes(documentId));
  if (index < 0) {
    elements.searchInput.value = "";
    elements.typeFilter.value = "";
    state.currentPage = 1;
    applyFilters();
    index = state.filteredDocuments.findIndex((record) => documentIds(record).includes(documentId));
  }
  if (index >= 0) state.currentPage = Math.floor(index / state.pageSize) + 1;
}

function focusDocumentFromDocumentList(documentRecord: DocumentRecord): void {
  updateHash(documentHashFor(documentRecord));
  ensureDocumentVisible(documentRecord);
  selectDocument(documentRecord, true);
}

function focusDocumentFromMeetingDetail(documentRecord: DocumentRecord): void {
  setActiveView("documents", false, false);
  updateHash(documentHashFor(documentRecord));
  ensureDocumentVisible(documentRecord);
  selectDocument(documentRecord, true);
}

function createInlineDocumentLinks(documentIdsToRender: string[], emptyLabel: string): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.className = "inline-document-links";
  const documents = uniqueValues(documentIdsToRender)
    .map((id) => findDocumentById(id))
    .filter((record): record is DocumentRecord => Boolean(record));
  if (documents.length === 0) return renderEmptyRelation(emptyLabel);
  for (const documentRecord of documents) {
    const button = createDocumentAction(documentRecord, getDocumentTitle(documentRecord), true);
    button.classList.add("compact-document-link");
    wrapper.appendChild(button);
  }
  return wrapper;
}

function createMeetingDocumentsTable(documentIdsToRender: string[], emptyLabel: string): HTMLElement {
  const documents = uniqueValues(documentIdsToRender)
    .map((id) => findDocumentById(id))
    .filter((record): record is DocumentRecord => Boolean(record));
  if (documents.length === 0) return renderEmptyRelation(emptyLabel);
  const wrapper = document.createElement("div");
  wrapper.className = "table-wrapper compact-detail-table-wrapper";
  const table = document.createElement("table");
  table.className = "compact-detail-table";
  table.innerHTML = "<thead><tr><th>Datum</th><th>Document</th><th>Type</th><th>Actie</th></tr></thead>";
  const body = document.createElement("tbody");
  for (const documentRecord of documents) {
    const row = document.createElement("tr");
    row.appendChild(createCell(formatDate(getDocumentDate(documentRecord))));
    row.appendChild(createCell(getDocumentTitle(documentRecord)));
    row.appendChild(createCell(getCompactTypeLabel(documentRecord)));
    const actionCell = document.createElement("td");
    actionCell.appendChild(createDocumentAction(documentRecord, "Bekijk documentdetails", true));
    row.appendChild(actionCell);
    body.appendChild(row);
  }
  table.appendChild(body);
  wrapper.appendChild(table);
  return wrapper;
}

function createAgendaItemsTable(agendaIds: string[]): HTMLElement {
  if (agendaIds.length === 0) return renderEmptyRelation("Geen agendapunten gevonden in meeting_items.jsonl voor deze vergadering.");
  const wrapper = document.createElement("div");
  wrapper.className = "table-wrapper compact-detail-table-wrapper";
  const table = document.createElement("table");
  table.className = "compact-detail-table agenda-detail-table";
  table.innerHTML = "<thead><tr><th>Agendapunt</th><th>Omschrijving</th><th>Gekoppelde documenten</th></tr></thead>";
  const body = document.createElement("tbody");
  for (const itemId of agendaIds) {
    const item = state.indexes?.agendaItemsById.get(itemId);
    const itemDocumentIds = linkedDocumentIdsForAgendaItem(itemId);
    const row = document.createElement("tr");
    row.appendChild(createCell(getAgendaItemTitle(item)));
    row.appendChild(createCell(text(item?.description, unavailable("Geen omschrijving"))));
    const documentsCell = document.createElement("td");
    documentsCell.appendChild(createInlineDocumentLinks(itemDocumentIds, "Geen gekoppelde documenten."));
    row.appendChild(documentsCell);
    body.appendChild(row);
  }
  table.appendChild(body);
  wrapper.appendChild(table);
  return wrapper;
}

function createDocumentList(documentIdsToRender: string[], emptyLabel: string): HTMLElement {
  const list = document.createElement("div");
  list.className = "linked-document-list";
  const documents = uniqueValues(documentIdsToRender)
    .map((id) => findDocumentById(id))
    .filter((record): record is DocumentRecord => Boolean(record));
  if (documents.length === 0) return renderEmptyRelation(emptyLabel);
  for (const documentRecord of documents) {
    const article = document.createElement("article");
    article.className = "relation-card relation-card--actionable";
    const heading = document.createElement("h4");
    heading.textContent = getDocumentTitle(documentRecord);
    const meta = document.createElement("p");
    meta.className = "muted";
    meta.textContent = [formatDate(getDocumentDate(documentRecord)), getCompactTypeLabel(documentRecord)].filter(Boolean).join(" · ");
    const actions = document.createElement("div");
    actions.className = "document-actions";
    actions.appendChild(createDocumentAction(documentRecord, "Bekijk documentdetails", true));
    const href = getDocumentUrl(documentRecord);
    if (href) {
      const link = document.createElement("a");
      link.href = href;
      link.rel = "noopener noreferrer";
      link.target = "_blank";
      link.textContent = "Open";
      actions.appendChild(link);
    }
    article.append(heading, meta, actions);
    list.appendChild(article);
  }
  return list;
}

function createRelationCard(title: string, meta: string, body?: string): HTMLElement {
  const article = document.createElement("article");
  article.className = "relation-card";
  const heading = document.createElement("h4");
  heading.textContent = title;
  const subtitle = document.createElement("p");
  subtitle.className = "muted";
  subtitle.textContent = meta;
  article.append(heading, subtitle);
  if (body) {
    const paragraph = document.createElement("p");
    paragraph.textContent = body;
    article.appendChild(paragraph);
  }
  return article;
}

function renderEmptyRelation(label: string): HTMLElement {
  const paragraph = document.createElement("p");
  paragraph.className = "empty-state";
  paragraph.textContent = label;
  return paragraph;
}

function appendSectionHeading(section: HTMLElement, label: string): void {
  const heading = document.createElement("h3");
  heading.textContent = label;
  section.appendChild(heading);
}

function renderSummary(): void {
  const latest = state.data?.latest ?? {};
  const municipality = pick(latest.municipality, latest.municipality_id) || "-";
  const generatedAt = formatDateTime(latest.generated_at);
  elements.municipality.textContent = municipality;
  elements.municipalityCopy.textContent = municipality;
  elements.documentsSeen.textContent = text(latest.documents_seen);
  elements.documentsNormalized.textContent = text(latest.documents_normalized);
  elements.generatedAt.textContent = generatedAt;
  elements.generatedAtCopy.textContent = generatedAt;
  elements.meetingsCount.textContent = text(state.data?.meetings.length);
  elements.agendaItemsCount.textContent = text(state.data?.agendaItems.length);
  const documents = state.data?.documents ?? [];
  const linkedDocumentCount = documents.filter((record) => relationLabelsForDocument(record).length > 0).length;
  const unknownTypeCount = documents.filter((record) => isUnknownType(pick(record.normalized_document_type, record.normalized_document_type_label, record.type))).length;
  const relationCount = (state.data?.meetingDocumentRelations.length ?? 0) + (state.data?.meetingItemDocumentRelations.length ?? 0);
  elements.linkedDocumentsCount.textContent = text(linkedDocumentCount);
  elements.organizationPositionsCount.textContent = text(state.data?.organizationPositions.length ?? 0);
  const notices: string[] = [];
  if (documents.length > 0 && linkedDocumentCount === 0 && relationCount > 0) {
    notices.push(`${relationCount} relationele records geladen, maar Geen bruikbare documentkoppelingen in deze export.`);
  }
  if (documents.length > 0 && unknownTypeCount === documents.length) notices.push("Alle documenten hebben nog een onbekend genormaliseerd documenttype.");
  elements.dataQualityNotice.textContent = notices.join(" ");
  elements.dataQualityNotice.hidden = notices.length === 0;
  const relationText = latest.relations_enabled
    ? ` Relationele context: ${latest.relations_summary?.meetings_seen ?? 0} vergaderingen, ${latest.relations_summary?.meeting_items_seen ?? 0} agendapunten. ${linkedDocumentCount} documenten hebben een koppeling.`
    : "";
  const organizationText = (state.data?.organizationPositions.length ?? 0) > 0
    ? ` Organisatie: ${state.data?.organizationPositions.length ?? 0} posities.`
    : "";
  elements.statusMessage.textContent = `${state.data?.documents.length ?? 0} documenten geladen.${relationText}${organizationText}`;
}

function populateTypeFilter(): void {
  const options = new Map<string, string>();
  for (const documentRecord of state.data?.documents ?? []) options.set(getCompactType(documentRecord), getCompactTypeLabel(documentRecord));
  for (const [value, label] of [...options.entries()].sort((a, b) => a[1].localeCompare(b[1], "nl"))) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    elements.typeFilter.appendChild(option);
  }
}

function searchBlob(documentRecord: DocumentRecord): string {
  const cacheKey = getDocumentCacheKey(documentRecord);
  const cached = derivedCaches.documentSearchBlobByKey.get(cacheKey);
  if (cached !== undefined) return cached;

  const blob = [
    getDocumentTitle(documentRecord),
    documentRecord.description,
    documentRecord.filename,
    documentRecord.document_type,
    documentRecord.normalized_document_type,
    documentRecord.normalized_document_type_label,
    documentRecord.source_id,
    documentRecord.source_object_id,
    relationLabelsForDocument(documentRecord).join(" "),
  ].filter(Boolean).join(" ").toLowerCase();
  derivedCaches.documentSearchBlobByKey.set(cacheKey, blob);
  return blob;
}

function sortDocuments(records: DocumentRecord[]): DocumentRecord[] {
  const sorted = [...records];
  const byTitle = (a: DocumentRecord, b: DocumentRecord) => getDocumentTitle(a).localeCompare(getDocumentTitle(b), "nl");
  const byType = (a: DocumentRecord, b: DocumentRecord) => getCompactTypeLabel(a).localeCompare(getCompactTypeLabel(b), "nl");
  const bySize = (a: DocumentRecord, b: DocumentRecord) => Number(getDocumentSize(a) ?? 0) - Number(getDocumentSize(b) ?? 0);
  const byDate = (a: DocumentRecord, b: DocumentRecord) => timestamp(getDocumentDate(a)) - timestamp(getDocumentDate(b));
  switch (state.sortMode) {
    case "date-asc": return sorted.sort(byDate);
    case "title-asc": return sorted.sort(byTitle);
    case "type-asc": return sorted.sort(byType);
    case "size-desc": return sorted.sort((a, b) => bySize(b, a));
    case "size-asc": return sorted.sort(bySize);
    case "date-desc":
    default: return sorted.sort((a, b) => byDate(b, a));
  }
}

function applyFilters(): void {
  const query = elements.searchInput.value.trim().toLowerCase();
  const type = elements.typeFilter.value;
  let records = (state.data?.documents ?? []).filter((documentRecord) => {
    if (type && getCompactType(documentRecord) !== type) return false;
    if (query && !searchBlob(documentRecord).includes(query)) return false;
    return true;
  });
  records = sortDocuments(records);
  state.filteredDocuments = records;
  renderDocuments();
}

function hasAnyDocumentFilenameMetadata(records: DocumentRecord[]): boolean {
  return records.some((record) => Boolean(getDocumentFilename(record)));
}

function hasAnyDocumentSizeMetadata(records: DocumentRecord[]): boolean {
  return records.some((record) => Boolean(getDocumentSize(record)));
}

function getVisibleDocumentColumnCount(showFilenameColumn: boolean, showSizeColumn: boolean): number {
  return 4 + Number(showFilenameColumn) + Number(showSizeColumn);
}

function setColumnVisibilityForTable(tableSelector: string, headerLabel: string, visible: boolean): void {
  const table = document.querySelector(tableSelector);
  const headers = Array.from(table?.querySelectorAll<HTMLTableCellElement>("thead th") ?? []);
  const header = headers.find((cell) => cell.textContent?.trim() === headerLabel);
  if (header) header.hidden = !visible;
}

function setTableColumnVisibility(headerLabel: string, visible: boolean): void {
  setColumnVisibilityForTable(".documents-table", headerLabel, visible);
}

function createDocumentTitleCell(documentRecord: DocumentRecord): HTMLTableCellElement {
  const cell = document.createElement("td");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "link-button document-title-button";
  button.textContent = getDocumentTitle(documentRecord);
  button.addEventListener("click", () => focusDocumentFromDocumentList(documentRecord));
  cell.appendChild(button);
  const labels = relationLabelsForDocument(documentRecord).slice(0, 3);
  if (labels.length > 0) {
    const list = document.createElement("ul");
    list.className = "relation-context";
    for (const label of labels) {
      const item = document.createElement("li");
      item.textContent = label;
      list.appendChild(item);
    }
    cell.appendChild(list);
  }
  return cell;
}

function createDocumentActionsCell(documentRecord: DocumentRecord): HTMLTableCellElement {
  const cell = document.createElement("td");
  const actionList = document.createElement("div");
  actionList.className = "document-actions";
  actionList.appendChild(createDocumentAction(documentRecord));
  const href = getDocumentUrl(documentRecord);
  if (href) {
    const link = document.createElement("a");
    link.href = href;
    link.textContent = "Open";
    link.rel = "noopener noreferrer";
    link.target = "_blank";
    actionList.appendChild(link);
  }
  cell.appendChild(actionList);
  return cell;
}

function renderDocuments(): void {
  const total = state.filteredDocuments.length;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  state.currentPage = Math.min(Math.max(state.currentPage, 1), totalPages);
  const start = (state.currentPage - 1) * state.pageSize;
  const pageRecords = state.filteredDocuments.slice(start, start + state.pageSize);
  const allDocuments = state.data?.documents ?? [];
  const showFilenameColumn = hasAnyDocumentFilenameMetadata(allDocuments);
  const showSizeColumn = hasAnyDocumentSizeMetadata(allDocuments);
  setTableColumnVisibility("Bestand", showFilenameColumn);
  setTableColumnVisibility("Grootte", showSizeColumn);
  elements.resultCount.textContent = `${total} document(en)`;
  elements.visibleDocumentsCount.textContent = `${total} zichtbaar`;
  elements.tableBody.replaceChildren();
  if (pageRecords.length === 0) {
    const row = document.createElement("tr");
    const cell = createCell("Geen documenten gevonden.");
    cell.colSpan = getVisibleDocumentColumnCount(showFilenameColumn, showSizeColumn);
    row.appendChild(cell);
    elements.tableBody.appendChild(row);
  }
  for (const documentRecord of pageRecords) {
    const row = document.createElement("tr");
    const documentId = getDocumentId(documentRecord);
    if (state.selectedDocumentId && documentIds(documentRecord).includes(state.selectedDocumentId)) row.className = "is-selected";
    row.appendChild(createCell(formatDate(getDocumentDate(documentRecord))));
    row.appendChild(createCell(getCompactTypeLabel(documentRecord)));
    row.appendChild(createDocumentTitleCell(documentRecord));
    if (showFilenameColumn) row.appendChild(createCell(text(getDocumentFilename(documentRecord), unavailable("Geen bestandsmetadata"))));
    if (showSizeColumn) row.appendChild(createCell(formatDocumentSize(documentRecord)));
    row.appendChild(createDocumentActionsCell(documentRecord));
    row.dataset.documentId = documentId;
    elements.tableBody.appendChild(row);
  }
  const pageText = `Pagina ${state.currentPage} van ${totalPages}`;
  elements.pageInfoTop.textContent = pageText;
  elements.pageInfoBottom.textContent = pageText;
  for (const button of [elements.previousTop, elements.previousBottom]) button.disabled = state.currentPage <= 1;
  for (const button of [elements.nextTop, elements.nextBottom]) button.disabled = state.currentPage >= totalPages;
}

function renderDocumentDetail(documentRecord: DocumentRecord): void {
  const ids = documentIds(documentRecord);
  const primaryId = ids[0] ?? "";
  const meetingIds = relatedMeetingIds(documentRecord);
  const itemIds = relatedAgendaItemIds(documentRecord);
  const versions = relatedVersions(documentRecord);
  const title = getDocumentTitle(documentRecord);
  elements.documentDetail.hidden = false;
  elements.documentDetailTitle.textContent = title;
  elements.documentDetailBody.replaceChildren();

  const grid = document.createElement("div");
  grid.className = "document-detail-grid";
  const meta = document.createElement("dl");
  meta.className = "summary-list document-detail-meta";
  appendDefinition(meta, "Datum", formatDate(getDocumentDate(documentRecord)));
  appendDefinition(meta, "Compact type", getCompactTypeLabel(documentRecord));
  appendDefinition(meta, "Bron documenttype", getSourceDocumentType(documentRecord));
  const filename = getDocumentFilename(documentRecord);
  if (filename) appendDefinition(meta, "Bestand", filename);
  const size = formatDocumentSize(documentRecord);
  if (size !== "Geen bestandsgrootte beschikbaar") appendDefinition(meta, "Grootte", size);
  appendDefinition(meta, "Document ID", text(primaryId, unavailable("Geen document-ID")));
  appendDefinition(meta, "Bron-ID", text(pick(documentRecord.source_id, documentRecord.source_object_id), unavailable()));
  appendDefinition(meta, "Schema", text(documentRecord.schema_version, unavailable()));
  grid.appendChild(meta);

  const actions = document.createElement("div");
  actions.className = "document-detail-actions";
  const downloadHref = getDocumentUrl(documentRecord);
  if (downloadHref) {
    const link = document.createElement("a");
    link.className = "primary-link";
    link.href = downloadHref;
    link.rel = "noopener noreferrer";
    link.target = "_blank";
    link.textContent = "Open document";
    actions.appendChild(link);
  } else {
    actions.appendChild(renderEmptyRelation("Geen veilige documentlink beschikbaar in de metadata."));
  }
  grid.appendChild(actions);
  elements.documentDetailBody.appendChild(grid);

  const metadataIssues = [
    isUnknownType(pick(documentRecord.normalized_document_type, documentRecord.normalized_document_type_label, documentRecord.type)) ? "compact documenttype ontbreekt" : "",
    getDocumentFilename(documentRecord) ? "" : "bestandsnaam ontbreekt",
    getDocumentSize(documentRecord) ? "" : "bestandsgrootte ontbreekt",
    downloadHref ? "" : "documentlink ontbreekt",
  ].filter(Boolean);
  if (metadataIssues.length > 0) {
    const notice = document.createElement("p");
    notice.className = "metadata-notice";
    notice.textContent = `Metadata beperkt in huidige export: ${metadataIssues.join(", ")}.`;
    elements.documentDetailBody.appendChild(notice);
  }

  if (pick(documentRecord.description) && pick(documentRecord.description) !== title) {
    const description = document.createElement("p");
    description.className = "document-description";
    description.textContent = text(documentRecord.description);
    elements.documentDetailBody.appendChild(description);
  }

  const relations = document.createElement("div");
  relations.className = "detail-sections";
  const meetingsSection = document.createElement("section");
  meetingsSection.className = "detail-section";
  appendSectionHeading(meetingsSection, "Gekoppelde vergaderingen");
  if (meetingIds.length === 0) meetingsSection.appendChild(renderEmptyRelation("Geen gekoppelde vergadering gevonden in de huidige public export."));
  for (const meetingId of meetingIds) {
    const meeting = state.indexes?.meetingsById.get(meetingId);
    const card = createRelationCard(getMeetingTitle(meeting), [formatDate(getMeetingDate(meeting)), pick(meeting?.dmu_name), meetingId].filter(Boolean).join(" · ") || "Vergadering", text(meeting?.description, ""));
    meetingsSection.appendChild(card);
  }
  relations.appendChild(meetingsSection);

  const agendaSection = document.createElement("section");
  agendaSection.className = "detail-section";
  appendSectionHeading(agendaSection, "Gekoppelde agendapunten");
  if (itemIds.length === 0) agendaSection.appendChild(renderEmptyRelation("Geen gekoppeld agendapunt gevonden in de huidige public export."));
  for (const itemId of itemIds) {
    const item = state.indexes?.agendaItemsById.get(itemId);
    const meeting = state.indexes?.meetingsById.get(getAgendaItemMeetingId(item));
    agendaSection.appendChild(createRelationCard(getAgendaItemTitle(item), [getMeetingTitle(meeting), itemId].filter(Boolean).join(" · ") || "Agendapunt", text(item?.description, "")));
  }
  relations.appendChild(agendaSection);

  const versionsSection = document.createElement("section");
  versionsSection.className = "detail-section";
  appendSectionHeading(versionsSection, "Versies");
  if (versions.length === 0) versionsSection.appendChild(renderEmptyRelation("Geen aparte versiehistorie gevonden."));
  for (const version of versions.slice(0, 10)) {
    versionsSection.appendChild(createRelationCard("Documentversie", [formatDateTime(version.retrieved_at), pick(version.id, version.source_id)].filter(Boolean).join(" · ") || "Versie", ""));
  }
  relations.appendChild(versionsSection);
  elements.documentDetailBody.appendChild(relations);
}

function selectDocument(documentRecord: DocumentRecord, scroll = true): void {
  state.selectedDocumentId = getDocumentId(documentRecord) || null;
  renderDocumentDetail(documentRecord);
  renderDocuments();
  if (scroll) elements.documentDetail.scrollIntoView({ block: "start", behavior: "smooth" });
}

function clearDocumentSelection(): void {
  state.selectedDocumentId = null;
  elements.documentDetail.hidden = true;
  elements.documentDetailTitle.textContent = "Documentdetails";
  elements.documentDetailBody.replaceChildren();
  renderDocuments();
}

function meetingSearchBlob(meeting: MeetingRecord): string {
  const meetingId = getMeetingId(meeting);
  const cached = derivedCaches.meetingSearchBlobById.get(meetingId);
  if (cached !== undefined) return cached;

  const agendaText = agendaItemIdsForMeeting(meetingId)
    .map((itemId) => state.indexes?.agendaItemsById.get(itemId))
    .map((item) => [getAgendaItemTitle(item), item?.description, item?.number].filter(Boolean).join(" "))
    .join(" ");
  const blob = [
    getMeetingTitle(meeting),
    getMeetingDate(meeting),
    formatDate(getMeetingDate(meeting)),
    meeting.description,
    meeting.dmu_name,
    meeting.location,
    meetingId,
    agendaText,
  ].filter(Boolean).join(" ").toLowerCase();
  derivedCaches.meetingSearchBlobById.set(meetingId, blob);
  return blob;
}

function isFutureMeeting(meeting: MeetingRecord): boolean {
  const meetingDate = parseDateValue(getMeetingDate(meeting));
  if (!meetingDate) return false;
  return meetingDate > new Date(new Date().toDateString());
}

function matchesMeetingDateFilter(meeting: MeetingRecord): boolean {
  if (state.meetingDateFilter === "all") return true;
  const future = isFutureMeeting(meeting);
  return state.meetingDateFilter === "future" ? future : !future;
}

function filteredMeetings(): MeetingRecord[] {
  const query = state.meetingQuery.trim().toLowerCase();
  const cacheKey = `${query}|${state.meetingDateFilter}|${state.meetingSortMode}`;
  const cached = derivedCaches.filteredMeetingsByKey.get(cacheKey);
  if (cached) return cached;

  const meetings = (state.data?.meetings ?? []).filter((meeting) => {
    if (!matchesMeetingDateFilter(meeting)) return false;
    if (!query) return true;
    return meetingSearchBlob(meeting).includes(query);
  });
  const byDate = (a: MeetingRecord, b: MeetingRecord) => timestamp(getMeetingDate(a)) - timestamp(getMeetingDate(b));
  const sortedMeetings = [...meetings].sort((a, b) => state.meetingSortMode === "date-asc" ? byDate(a, b) : byDate(b, a));
  derivedCaches.filteredMeetingsByKey.set(cacheKey, sortedMeetings);
  return sortedMeetings;
}

function ensureMeetingVisible(meetingId: string): void {
  const meetings = filteredMeetings();
  const index = meetings.findIndex((meeting) => getMeetingId(meeting) === meetingId);
  if (index >= 0) state.meetingCurrentPage = Math.floor(index / state.meetingPageSize) + 1;
}

function renderMeetings(): void {
  const meetings = filteredMeetings();
  const total = meetings.length;
  const totalPages = Math.max(1, Math.ceil(total / state.meetingPageSize));
  state.meetingCurrentPage = Math.min(Math.max(state.meetingCurrentPage, 1), totalPages);
  const start = (state.meetingCurrentPage - 1) * state.meetingPageSize;
  const pageMeetings = meetings.slice(start, start + state.meetingPageSize);

  elements.visibleMeetingsCount.textContent = total > 0
    ? `${start + 1}-${start + pageMeetings.length} van ${total} zichtbaar`
    : "0 zichtbaar";
  elements.meetingsResultCount.textContent = `${total} vergadering(en)`;
  elements.meetingsTableBody.replaceChildren();

  const pageText = `Pagina ${state.meetingCurrentPage} van ${totalPages}`;
  elements.meetingPageInfoTop.textContent = pageText;
  elements.meetingPageInfoBottom.textContent = pageText;
  for (const button of [elements.previousMeetingTop, elements.previousMeetingBottom]) {
    button.disabled = state.meetingCurrentPage <= 1;
  }
  for (const button of [elements.nextMeetingTop, elements.nextMeetingBottom]) {
    button.disabled = state.meetingCurrentPage >= totalPages;
  }

  if (pageMeetings.length === 0) {
    const row = document.createElement("tr");
    const emptyText = state.meetingQuery.trim()
      ? "Geen vergaderingen gevonden voor deze zoekopdracht."
      : "Geen vergaderingen gevonden in de huidige public export.";
    const cell = createCell(emptyText);
    cell.colSpan = 5;
    row.appendChild(cell);
    elements.meetingsTableBody.appendChild(row);
    return;
  }

  for (const meeting of pageMeetings) {
    const meetingId = getMeetingId(meeting);
    const agendaIds = agendaItemIdsForMeeting(meetingId);
    const documentIdsForMeeting = linkedDocumentIdsForMeeting(meetingId);
    const row = document.createElement("tr");
    if (state.selectedMeetingId === meetingId) row.className = "is-selected";
    row.appendChild(createCell(formatDate(getMeetingDate(meeting))));
    row.appendChild(createCell(getMeetingTitle(meeting)));
    row.appendChild(createCell(text(agendaIds.length)));
    row.appendChild(createCell(text(documentIdsForMeeting.length)));
    const actions = document.createElement("td");
    const detailButton = document.createElement("button");
    detailButton.type = "button";
    detailButton.className = "secondary-button";
    detailButton.textContent = "Details";
    detailButton.addEventListener("click", () => selectMeeting(meeting, true));
    actions.appendChild(detailButton);
    row.appendChild(actions);
    elements.meetingsTableBody.appendChild(row);
  }
}

function renderMeetingDetail(meeting: MeetingRecord): void {
  const meetingId = getMeetingId(meeting);
  const agendaIds = agendaItemIdsForMeeting(meetingId);
  const documentIdsForMeeting = linkedDocumentIdsForMeeting(meetingId);
  elements.meetingDetail.hidden = false;
  elements.meetingDetailTitle.textContent = getMeetingTitle(meeting);
  elements.meetingDetailBody.replaceChildren();

  const grid = document.createElement("div");
  grid.className = "document-detail-grid meeting-detail-grid";
  const meta = document.createElement("dl");
  meta.className = "summary-list document-detail-meta";
  appendDefinition(meta, "Datum", formatDate(getMeetingDate(meeting)));
  appendDefinition(meta, "Vergadering ID", text(meetingId, unavailable("Geen vergadering-ID")));
  appendDefinition(meta, "Commissie", text(pick(meeting.dmu_name), unavailable()));
  appendDefinition(meta, "Locatie", text(pick(meeting.location), unavailable()));
  appendDefinition(meta, "Agendapunten", text(agendaIds.length));
  appendDefinition(meta, "Gekoppelde documenten", text(documentIdsForMeeting.length));
  grid.appendChild(meta);

  const intro = document.createElement("div");
  intro.className = "document-detail-actions";
  intro.appendChild(renderEmptyRelation("Meetingdetails blijven compact. Technische metadata staat onderaan achter de disclosure."));
  grid.appendChild(intro);
  elements.meetingDetailBody.appendChild(grid);

  if (pick(meeting.description) && pick(meeting.description) !== getMeetingTitle(meeting)) {
    const description = document.createElement("p");
    description.className = "document-description";
    description.textContent = text(meeting.description);
    elements.meetingDetailBody.appendChild(description);
  }

  const sections = document.createElement("div");
  sections.className = "meeting-detail-sections";

  const agendaSection = document.createElement("section");
  agendaSection.className = "detail-section detail-section--wide";
  appendSectionHeading(agendaSection, "Agendapunten binnen deze vergadering");
  agendaSection.appendChild(createAgendaItemsTable(agendaIds));
  sections.appendChild(agendaSection);

  const documentsSection = document.createElement("section");
  documentsSection.className = "detail-section detail-section--wide";
  appendSectionHeading(documentsSection, "Gekoppelde documenten bij de vergadering");
  documentsSection.appendChild(createMeetingDocumentsTable(documentIdsForMeeting, "Geen gekoppelde documenten gevonden voor deze vergadering."));
  sections.appendChild(documentsSection);
  elements.meetingDetailBody.appendChild(sections);
}

function selectMeeting(meeting: MeetingRecord, scroll = true): void {
  state.selectedMeetingId = getMeetingId(meeting) || null;
  if (state.selectedMeetingId) ensureMeetingVisible(state.selectedMeetingId);
  renderMeetingDetail(meeting);
  renderMeetings();
  if (scroll) elements.meetingDetail.scrollIntoView({ block: "start", behavior: "smooth" });
}

function clearMeetingSelection(): void {
  state.selectedMeetingId = null;
  elements.meetingDetail.hidden = true;
  elements.meetingDetailTitle.textContent = "Vergaderdetails";
  elements.meetingDetailBody.replaceChildren();
  renderMeetings();
}

function getOrganizationId(record: OrganizationGroupRecord | OrganizationPersonRecord | OrganizationRoleRecord | OrganizationPositionRecord | OrganizationGroupMembershipRecord): string {
  return pick(record.id, record.source_id);
}

function roleCategory(position: OrganizationPositionRecord | OrganizationRoleRecord): string {
  return pick(position.role_category) || roleCategoryFromName(pick("role_name" in position ? position.role_name : position.name));
}

function roleCategoryFromName(roleName: string): string {
  const name = roleName.toLowerCase().trim();
  if (name.includes("burgemeester") || name === "voorzitter van de gemeenteraad") return "burgemeester";
  if (name.includes("griff")) return "griffie";
  if (name.includes("fractievoorzitter")) return "fractievoorzitter";
  if (name.includes("raadslid") || name === "fractie raadslid") return "raadslid";
  if (name.includes("commissie")) return "commissielid";
  return "overig";
}

function roleCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    burgemeester: "Burgemeester / raadvoorzitter",
    griffie: "Griffie",
    fractievoorzitter: "Fractievoorzitter",
    raadslid: "Raadslid",
    commissielid: "Commissielid",
    overig: "Overig",
  };
  return labels[category] ?? category;
}

function displayRoleName(position: OrganizationPositionRecord): string {
  const category = roleCategory(position);
  const rawName = pick(position.role_name);
  if (category === "raadslid") return "Raadslid";
  if (category === "fractievoorzitter") return "Fractievoorzitter";
  if (category === "burgemeester") return rawName === "Burgemeester" ? "Burgemeester" : "Burgemeester / raadvoorzitter";
  if (category === "griffie") return rawName || "Griffie";
  if (category === "commissielid") return rawName || "Commissielid";
  return rawName || unavailable("Geen rolnaam");
}

function matchesRoleFilter(position: OrganizationPositionRecord, filter: string): boolean {
  if (!filter) return true;
  const category = roleCategory(position);
  if (filter === "raadslid") return category === "raadslid" || category === "fractievoorzitter";
  return category === filter;
}

function parseDateValue(value: unknown): Date | null {
  const dateText = pick(value);
  if (!dateText) return null;
  const date = new Date(`${dateText.slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function isCurrentOrganizationPosition(position: OrganizationPositionRecord): boolean {
  if (position.active === false) return false;
  const endDate = parseDateValue(position.end_date);
  if (endDate && endDate < new Date(new Date().toDateString())) return false;
  return true;
}

function normalizedGroupType(group: OrganizationGroupRecord | OrganizationGroupMembershipRecord): string {
  const type = pick("type" in group ? group.type : group.group_type).toLowerCase();
  if (type === "fractie" || type === "commissie" || type === "orgaan") return type;
  return "overig";
}

function groupTypeLabel(type: string): string {
  const labels: Record<string, string> = { fractie: "Fracties", commissie: "Commissies", orgaan: "Organen", overig: "Overig of onbekend" };
  return labels[type] ?? type;
}

function personName(person: OrganizationPersonRecord | OrganizationPositionRecord | OrganizationGroupMembershipRecord | undefined): string {
  if (!person) return "-";
  return pick(
    "display_name" in person ? person.display_name : "",
    "person_display_name" in person ? person.person_display_name : "",
    ["first_name" in person ? person.first_name : "", "preposition" in person ? person.preposition : "", "last_name" in person ? person.last_name : ""].filter(Boolean).join(" "),
  ) || "-";
}

function personByPosition(position: OrganizationPositionRecord): OrganizationPersonRecord | undefined {
  const personId = pick(position.person_id);
  const personSourceId = pick(position.person_source_id);
  return state.data?.organizationPersons.find((person) => pick(person.id) === personId || pick(person.source_id) === personSourceId);
}

function ensurePersonGroupCaches(): void {
  if (derivedCaches.personGroupsByPersonId.size || derivedCaches.personGroupIdsByPersonId.size) return;
  for (const membership of state.data?.organizationGroupMemberships ?? []) {
    const keys = [pick(membership.person_id), pick(membership.person_source_id)].filter(Boolean);
    const groupName = pick(membership.group_name, membership.group_id);
    const groupIds = [pick(membership.group_id), pick(membership.group_source_id)].filter(Boolean);
    for (const key of keys) {
      const names = derivedCaches.personGroupsByPersonId.get(key) ?? [];
      if (groupName && !names.includes(groupName)) names.push(groupName);
      derivedCaches.personGroupsByPersonId.set(key, names);

      const ids = derivedCaches.personGroupIdsByPersonId.get(key) ?? [];
      for (const groupId of groupIds) if (groupId && !ids.includes(groupId)) ids.push(groupId);
      derivedCaches.personGroupIdsByPersonId.set(key, ids);
    }
  }
}

function groupNamesForPersonKeys(personId: string, personSourceId: string): string[] {
  ensurePersonGroupCaches();
  return uniqueValues([
    ...(personId ? derivedCaches.personGroupsByPersonId.get(personId) ?? [] : []),
    ...(personSourceId ? derivedCaches.personGroupsByPersonId.get(personSourceId) ?? [] : []),
  ]);
}

function groupIdsForPersonKeys(personId: string, personSourceId: string): string[] {
  ensurePersonGroupCaches();
  return uniqueValues([
    ...(personId ? derivedCaches.personGroupIdsByPersonId.get(personId) ?? [] : []),
    ...(personSourceId ? derivedCaches.personGroupIdsByPersonId.get(personSourceId) ?? [] : []),
  ]);
}

function groupNamesForPerson(position: OrganizationPositionRecord): string[] {
  return groupNamesForPersonKeys(pick(position.person_id), pick(position.person_source_id));
}

function formatNumber(value: unknown): string {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return new Intl.NumberFormat("nl-NL").format(number);
}

function formatRatioPercent(value: unknown): string {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  const ratio = number <= 1 ? number : number / 100;
  return new Intl.NumberFormat("nl-NL", { style: "percent", maximumFractionDigits: 1 }).format(ratio);
}

function dashboardTotal(key: string, fallback = 0): number {
  const value = state.data?.dashboard?.totals?.[key];
  return Number.isFinite(Number(value)) ? Number(value) : fallback;
}

function dashboardLinkedDocuments(): number {
  const documents = state.data?.documents ?? [];
  const fallback = documents.filter((record) => relationLabelsForDocument(record).length > 0).length;
  return dashboardTotal("linked_documents", fallback);
}

function dashboardCoverageRatio(): number {
  const value = state.data?.dashboard?.coverage?.documents_with_any_meeting_context_ratio;
  if (Number.isFinite(Number(value))) return Number(value);
  const documents = state.data?.documents.length ?? 0;
  return documents ? dashboardLinkedDocuments() / documents : 0;
}

function statusLabelForFreshness(status: string): string {
  switch (status) {
    case "fresh": return "Vers";
    case "aging": return "Veroudert";
    case "stale": return "Verouderd";
    default: return "Onbekend";
  }
}

function dashboardYearData(source: DashboardYearCount[] | undefined, records: UnknownRecord[], ...dateKeys: string[]): DashboardYearCount[] {
  if (source && source.length > 0) return source;
  const counts = new Map<string, number>();
  for (const record of records) {
    let year = "";
    for (const key of dateKeys) {
      const value = pick(record[key]);
      if (value.length >= 4 && /^\d{4}/.test(value)) {
        year = value.slice(0, 4);
        break;
      }
    }
    if (year) counts.set(year, (counts.get(year) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0])).map(([year, count]) => ({ year, count }));
}

function dashboardDocumentTypeData(source: DashboardDocumentTypeCount[] | undefined): DashboardDocumentTypeCount[] {
  if (source && source.length > 0) return source;
  const counts = new Map<string, number>();
  for (const documentRecord of state.data?.documents ?? []) {
    const label = pick(documentRecord.normalized_document_type_label, documentRecord.document_type, documentRecord.normalized_document_type, "Onbekend");
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "nl"))
    .slice(0, 12)
    .map(([document_type, count]) => ({ document_type, count }));
}

function dashboardSizeBucketData(source: DashboardSizeBucketCount[] | undefined): DashboardSizeBucketCount[] {
  if (source && source.length > 0) return source;
  const counts = new Map<string, number>([["Onbekend", 0], ["0-100 KB", 0], ["100 KB-1 MB", 0], ["1-5 MB", 0], ["> 5 MB", 0]]);
  for (const documentRecord of state.data?.documents ?? []) {
    const size = getDocumentSize(documentRecord);
    if (!Number.isFinite(Number(size))) {
      counts.set("Onbekend", (counts.get("Onbekend") ?? 0) + 1);
    } else if (Number(size) < 100 * 1024) {
      counts.set("0-100 KB", (counts.get("0-100 KB") ?? 0) + 1);
    } else if (Number(size) < 1024 * 1024) {
      counts.set("100 KB-1 MB", (counts.get("100 KB-1 MB") ?? 0) + 1);
    } else if (Number(size) < 5 * 1024 * 1024) {
      counts.set("1-5 MB", (counts.get("1-5 MB") ?? 0) + 1);
    } else {
      counts.set("> 5 MB", (counts.get("> 5 MB") ?? 0) + 1);
    }
  }
  return [...counts.entries()].map(([bucket, count]) => ({ bucket, count }));
}

function documentSizeSummaryFallback(): { knownCount: number; unknownCount: number; averageBytes: number } {
  const documents = state.data?.documents ?? [];
  const sizes = documents
    .map((record) => Number(getDocumentSize(record)))
    .filter((value) => Number.isFinite(value) && value >= 0);
  const total = sizes.reduce((sum, value) => sum + value, 0);
  return {
    knownCount: sizes.length,
    unknownCount: Math.max(documents.length - sizes.length, 0),
    averageBytes: sizes.length > 0 ? Math.round(total / sizes.length) : 0,
  };
}

function dashboardDocumentSizeSummary(): { knownCount: number; unknownCount: number; averageBytes: number } {
  const fallback = documentSizeSummaryFallback();
  const summary = state.data?.dashboard?.document_file_size;
  const knownCount = Number(summary?.known_count);
  const unknownCount = Number(summary?.unknown_count);
  const averageBytes = Number(summary?.average_bytes);
  return {
    knownCount: Number.isFinite(knownCount) && (knownCount > 0 || fallback.knownCount === 0) ? knownCount : fallback.knownCount,
    unknownCount: Number.isFinite(unknownCount) && (knownCount > 0 || fallback.knownCount === 0) ? unknownCount : fallback.unknownCount,
    averageBytes: Number.isFinite(averageBytes) && averageBytes > 0 ? averageBytes : fallback.averageBytes,
  };
}

function relationRecordCount(): number {
  return (state.data?.meetingDocumentRelations.length ?? 0) + (state.data?.meetingItemDocumentRelations.length ?? 0);
}

function meetingYearLookup(): Map<string, string> {
  const lookup = new Map<string, string>();
  for (const meeting of state.data?.meetings ?? []) {
    const dateValue = pick(meeting.date, meeting.start_date, meeting.publication_date);
    const year = dateValue.length >= 4 && /^\d{4}/.test(dateValue) ? dateValue.slice(0, 4) : "";
    if (!year) continue;
    for (const identifier of [pick(meeting.id), pick(meeting.source_id)]) {
      if (identifier) lookup.set(identifier, year);
    }
  }
  return lookup;
}

function dashboardMeetingItemsByYear(source: DashboardYearCount[] | undefined): DashboardYearCount[] {
  if (source && source.length > 0) return source;
  const lookup = meetingYearLookup();
  const counts = new Map<string, number>();
  for (const item of state.data?.agendaItems ?? []) {
    const direct = pick(item.meeting_date, item.date, item.created_at);
    let year = direct.length >= 4 && /^\d{4}/.test(direct) ? direct.slice(0, 4) : "";
    if (!year) year = lookup.get(pick(item.meeting_id)) ?? lookup.get(pick(item.meeting_source_id)) ?? "";
    if (year) counts.set(year, (counts.get(year) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0])).map(([year, count]) => ({ year, count }));
}

function clearElement(element: HTMLElement): void {
  element.replaceChildren();
}

function appendDashboardCard(label: string, value: string, description: string): void {
  const card = document.createElement("article");
  card.className = "summary-card dashboard-card";
  const heading = document.createElement("h3");
  heading.textContent = label;
  const number = document.createElement("p");
  number.className = "summary-card__number";
  number.textContent = value;
  const textElement = document.createElement("p");
  textElement.className = "muted";
  textElement.textContent = description;
  card.append(heading, number, textElement);
  elements.dashboardSummaryCards.appendChild(card);
}

function renderBarChart(
  title: string,
  description: string,
  items: { label: string; value: number }[],
): HTMLElement {
  const section = document.createElement("section");
  section.className = "dashboard-chart";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const descriptionElement = document.createElement("p");
  descriptionElement.className = "muted";
  descriptionElement.textContent = description;
  const list = document.createElement("div");
  list.className = "dashboard-bars";
  list.setAttribute("role", "list");
  list.setAttribute("aria-label", title);
  const maxValue = Math.max(...items.map((item) => item.value), 0);
  if (items.length === 0 || maxValue === 0) {
    list.appendChild(renderEmptyRelation("Geen dashboarddata beschikbaar voor deze grafiek."));
  } else {
    for (const item of items) {
      const row = document.createElement("div");
      row.className = "dashboard-bar-row";
      row.setAttribute("role", "listitem");
      const meta = document.createElement("div");
      meta.className = "dashboard-bar-meta";
      const label = document.createElement("span");
      label.textContent = item.label;
      const value = document.createElement("strong");
      value.textContent = formatNumber(item.value);
      meta.append(label, value);
      const track = document.createElement("div");
      track.className = "dashboard-bar-track";
      const fill = document.createElement("span");
      fill.className = "dashboard-bar-fill";
      fill.style.width = `${Math.max((item.value / maxValue) * 100, 2)}%`;
      track.appendChild(fill);
      row.append(meta, track);
      list.appendChild(row);
    }
  }
  section.append(heading, descriptionElement, list);
  return section;
}

function renderLineChart(
  title: string,
  description: string,
  items: { label: string; value: number }[],
): HTMLElement {
  const section = document.createElement("section");
  section.className = "dashboard-chart dashboard-chart--line";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const descriptionElement = document.createElement("p");
  descriptionElement.className = "muted";
  descriptionElement.textContent = description;
  const maxValue = Math.max(...items.map((item) => item.value), 0);
  if (items.length === 0 || maxValue === 0) {
    section.append(heading, descriptionElement, renderEmptyRelation("Geen dashboarddata beschikbaar voor deze grafiek."));
    return section;
  }

  const width = 640;
  const height = 220;
  const padding = 28;
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;
  const points = items.map((item, index) => {
    const x = items.length === 1 ? width / 2 : padding + (index / (items.length - 1)) * plotWidth;
    const y = height - padding - (item.value / maxValue) * plotHeight;
    return { ...item, x, y };
  });
  const pointString = points.map((point) => `${point.x},${point.y}`).join(" ");
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${title}: ${items.map((item) => `${item.label} ${formatNumber(item.value)}`).join(", ")}`);

  const axis = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  axis.setAttribute("points", `${padding},${padding} ${padding},${height - padding} ${width - padding},${height - padding}`);
  axis.setAttribute("class", "dashboard-line-axis");
  svg.appendChild(axis);

  const line = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  line.setAttribute("points", pointString);
  line.setAttribute("class", "dashboard-line-path");
  svg.appendChild(line);

  for (const point of points) {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", String(point.x));
    circle.setAttribute("cy", String(point.y));
    circle.setAttribute("r", "4");
    circle.setAttribute("class", "dashboard-line-point");
    const titleElement = document.createElementNS("http://www.w3.org/2000/svg", "title");
    titleElement.textContent = `${point.label}: ${formatNumber(point.value)}`;
    circle.appendChild(titleElement);
    svg.appendChild(circle);
  }

  const summary = document.createElement("p");
  summary.className = "muted dashboard-chart-summary";
  summary.textContent = items.map((item) => `${item.label}: ${formatNumber(item.value)}`).join(" | ");
  section.append(heading, descriptionElement, svg, summary);
  return section;
}

function renderDashboard(): void {
  const data = state.data;
  if (!data) return;
  const dashboard = data.dashboard;
  const totals = dashboard?.totals ?? {};
  const documents = dashboardTotal("documents", data.documents.length);
  const linkedDocuments = dashboardLinkedDocuments();
  const coverageRatio = dashboardCoverageRatio();
  const freshnessStatus = dashboard?.freshness?.status ?? "unknown";
  const ageDays = dashboard?.freshness?.age_days;
  elements.dashboardFreshness.textContent = `${statusLabelForFreshness(freshnessStatus)}${typeof ageDays === "number" ? `, ${ageDays} dagen oud` : ""}`;
  elements.dashboardExplanation.textContent = "Het dashboard is gebaseerd op gegenereerde statische JSON en JSONL exports. Het telt publieke metadata, relaties en organisatie-aantallen, zonder PDF-inhoud, persoonsranking of politieke analyse.";

  clearElement(elements.dashboardSummaryCards);
  appendDashboardCard("Documenten", formatNumber(documents), "Alle gepubliceerde documentmetadata in documents.jsonl.");
  appendDashboardCard("Gekoppelde documenten", formatNumber(linkedDocuments), `${formatRatioPercent(coverageRatio)} van alle documenten heeft een match met de huidige relatie-export.`);
  appendDashboardCard("Vergaderingen", formatNumber(dashboardTotal("meetings", data.meetings.length)), "Publieke vergaderingen in de huidige export.");
  appendDashboardCard("Agendapunten", formatNumber(dashboardTotal("meeting_items", data.agendaItems.length)), "Agenda-items die aan vergaderingen zijn gekoppeld.");
  const sizeSummary = dashboardDocumentSizeSummary();
  appendDashboardCard("Documentgrootte bekend", formatNumber(sizeSummary.knownCount), `Gemiddeld ${formatBytes(sizeSummary.averageBytes)} per bekend bestand, ${formatNumber(sizeSummary.unknownCount)} onbekend.`);
  appendDashboardCard("Relatierecords", formatNumber(relationRecordCount()), "Aantal document-koppelingen vanuit vergaderingen en agendapunten.");
  appendDashboardCard("Organisatie", formatNumber(totals.organization_positions ?? data.organizationPositions.length), "Alleen aggregate aantallen voor personen, rollen, groepen en posities.");

  const documentsByYear = dashboardYearData(dashboard?.documents_by_year, data.documents, "publication_datetime", "date_published", "publication_date", "document_date", "date", "retrieved_at");
  const meetingsByYear = dashboardYearData(dashboard?.meetings_by_year, data.meetings, "date", "start_date", "publication_date");
  const itemsByYear = dashboardMeetingItemsByYear(dashboard?.meeting_items_by_year);
  const documentsByType = dashboardDocumentTypeData(dashboard?.documents_by_type);
  const documentsBySize = dashboardSizeBucketData(dashboard?.documents_by_size_bucket);

  clearElement(elements.dashboardCharts);
  elements.dashboardCharts.append(
    renderBarChart("Documenten per jaar", "Verdeling van documentmetadata over publicatie- of documentjaar.", documentsByYear.map((item) => ({ label: text(item.year), value: Number(item.count) || 0 }))),
    renderLineChart("Trend documenten per jaar", "Zelfde data als de staafgrafiek, maar als eenvoudige trendlijn.", documentsByYear.map((item) => ({ label: text(item.year), value: Number(item.count) || 0 }))),
    renderBarChart("Top documenttypen", "Meest voorkomende typen in de publieke documentexport.", documentsByType.map((item) => ({ label: text(item.document_type), value: Number(item.count) || 0 }))),
    renderBarChart("Vergaderingen per jaar", "Jaarverdeling van de vergaderexport.", meetingsByYear.map((item) => ({ label: text(item.year), value: Number(item.count) || 0 }))),
    renderBarChart("Agendapunten per jaar", "Jaarverdeling van de agenda-item export.", itemsByYear.map((item) => ({ label: text(item.year), value: Number(item.count) || 0 }))),
    renderBarChart("Documentgrootte", "Verdeling op basis van bekende file-size metadata, onbekend blijft zichtbaar.", documentsBySize.map((item) => ({ label: text(item.bucket), value: Number(item.count) || 0 }))),
  );
}

function renderSummaryCard(label: string, value: number, description: string): HTMLElement {
  const card = document.createElement("article");
  card.className = "summary-card";
  const heading = document.createElement("h3");
  heading.textContent = label;
  const number = document.createElement("p");
  number.className = "summary-card__number";
  number.textContent = text(value);
  const body = document.createElement("p");
  body.className = "muted";
  body.textContent = description;
  card.append(heading, number, body);
  return card;
}

interface OrganizationPersonRow {
  personKey: string;
  displayName: string;
  email: string;
  groupNames: string[];
  groupIds: string[];
  positions: OrganizationPositionRecord[];
  currentPositions: OrganizationPositionRecord[];
  active: boolean;
}

function syncOrganizationFilterOptions(groups: OrganizationGroupRecord[]): void {
  const groupTypeOptions: [string, string][] = [
    ["fractie", "Fracties"],
    ["commissie", "Commissies"],
    ["orgaan", "Organen"],
    ["overig", "Overig"],
    ["", "Alle typen"],
  ];
  const currentGroupType = state.organizationGroupTypeFilter;
  elements.organizationGroupTypeFilter.replaceChildren(...groupTypeOptions.map(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    return option;
  }));
  elements.organizationGroupTypeFilter.value = groupTypeOptions.some(([value]) => value === currentGroupType) ? currentGroupType : "fractie";
  state.organizationGroupTypeFilter = elements.organizationGroupTypeFilter.value;

  const currentGroup = state.organizationGroupFilter;
  const options = groups
    .slice()
    .sort((a, b) => [normalizedGroupType(a), pick(a.name)].join(" ").localeCompare([normalizedGroupType(b), pick(b.name)].join(" "), "nl"));
  elements.organizationGroupFilter.replaceChildren();
  const allOption = document.createElement("option");
  allOption.value = "";
  allOption.textContent = "Alle groepen";
  elements.organizationGroupFilter.appendChild(allOption);
  for (const group of options) {
    const option = document.createElement("option");
    option.value = pick(group.id, group.source_id);
    option.textContent = `${pick(group.name, getOrganizationId(group))} (${groupTypeLabel(normalizedGroupType(group)).toLowerCase()})`;
    elements.organizationGroupFilter.appendChild(option);
  }
  elements.organizationGroupFilter.value = options.some((group) => [pick(group.id), pick(group.source_id)].includes(currentGroup)) ? currentGroup : "";
  state.organizationGroupFilter = elements.organizationGroupFilter.value;
}

function renderOrganization(): void {
  const groups = state.data?.organizationGroups ?? [];
  const persons = state.data?.organizationPersons ?? [];
  const roles = state.data?.organizationRoles ?? [];
  const positions = state.data?.organizationPositions ?? [];
  const memberships = state.data?.organizationGroupMemberships ?? [];
  syncOrganizationFilterOptions(groups);

  const currentPositions = positions.filter(isCurrentOrganizationPosition);
  const activePersonKeys = new Set(currentPositions.map((position) => pick(position.person_id, position.person_source_id, position.person_display_name)).filter(Boolean));
  elements.organizationSummaryCount.textContent = `${currentPositions.length} actuele positie(s)`;
  elements.organizationSummaryCards.replaceChildren(
    renderSummaryCard("Fracties", groups.filter((group) => normalizedGroupType(group) === "fractie").length, "Primaire politieke groepen in de raad."),
    renderSummaryCard("Actieve personen", activePersonKeys.size, "Personen met minimaal een actuele positie."),
    renderSummaryCard("Rollen", roles.length, "Rollen uit de RIS API, samengevoegd tot leesbare categorieen."),
    renderSummaryCard("Historische posities", positions.length - currentPositions.length, "Niet-actuele positieperioden blijven opvraagbaar via het statusfilter."),
  );

  renderOrganizationGroups(groups, memberships);
  renderOrganizationPositions(positions);
}

function renderOrganizationGroups(groups: OrganizationGroupRecord[], memberships: OrganizationGroupMembershipRecord[]): void {
  elements.organizationGroupsList.replaceChildren();
  if (groups.length === 0) {
    elements.organizationGroupsList.appendChild(renderEmptyRelation("Geen organisatiegroepen gevonden. De maandelijkse organisatie-export is mogelijk nog niet uitgevoerd."));
    return;
  }
  const typeFilter = state.organizationGroupTypeFilter;
  const visibleGroups = groups
    .filter((group) => !typeFilter || normalizedGroupType(group) === typeFilter)
    .sort((a, b) => [normalizedGroupType(a), pick(a.name)].join(" ").localeCompare([normalizedGroupType(b), pick(b.name)].join(" "), "nl"));
  if (visibleGroups.length === 0) {
    elements.organizationGroupsList.appendChild(renderEmptyRelation("Geen groepen gevonden voor dit typefilter."));
    return;
  }
  const list = document.createElement("ul");
  list.className = "organization-compact-list";
  for (const group of visibleGroups) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = pick(group.name) || getOrganizationId(group);
    const memberCount = memberships.filter((membership) => pick(membership.group_id) === pick(group.id) || pick(membership.group_source_id) === pick(group.source_id)).length;
    const meta = document.createElement("span");
    meta.className = "muted";
    meta.textContent = ` ${groupTypeLabel(normalizedGroupType(group)).replace(/s$/, "").toLowerCase()} · ${memberCount} gekoppelde persoon/personen`;
    item.append(title, meta);
    list.appendChild(item);
  }
  elements.organizationGroupsList.appendChild(list);
}

function buildOrganizationPersonRows(positions: OrganizationPositionRecord[]): OrganizationPersonRow[] {
  const rows = new Map<string, OrganizationPersonRow>();
  for (const position of positions) {
    const person = personByPosition(position);
    const personKey = pick(position.person_id, position.person_source_id, position.person_display_name);
    if (!personKey) continue;
    const personId = pick(position.person_id, person?.id);
    const personSourceId = pick(position.person_source_id, person?.source_id);
    const existing = rows.get(personKey);
    const row = existing ?? {
      personKey,
      displayName: personName(position) || personName(person),
      email: pick(person?.email),
      groupNames: groupNamesForPersonKeys(personId, personSourceId),
      groupIds: groupIdsForPersonKeys(personId, personSourceId),
      positions: [],
      currentPositions: [],
      active: false,
    };
    row.positions.push(position);
    if (isCurrentOrganizationPosition(position)) row.currentPositions.push(position);
    row.active = row.currentPositions.length > 0 || person?.active === true;
    if (!row.email) row.email = pick(person?.email);
    rows.set(personKey, row);
  }
  return [...rows.values()];
}

function dedupePositions(positions: OrganizationPositionRecord[]): OrganizationPositionRecord[] {
  const seen = new Set<string>();
  const result: OrganizationPositionRecord[] = [];
  for (const position of positions) {
    const key = [displayRoleName(position), roleCategory(position), pick(position.start_date), pick(position.end_date), isCurrentOrganizationPosition(position) ? "active" : "inactive"].join("|");
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(position);
  }
  return result;
}

function roleSummaryForRow(row: OrganizationPersonRow): string {
  const positions = dedupePositions(row.currentPositions.length > 0 ? row.currentPositions : row.positions);
  const labels = uniqueValues(positions.map(displayRoleName));
  return labels.length > 0 ? labels.join(", ") : "-";
}

function dateRangeForRow(row: OrganizationPersonRow): string {
  const positions = dedupePositions(row.currentPositions.length > 0 ? row.currentPositions : row.positions);
  const starts = positions.map((position) => pick(position.start_date)).filter(Boolean).sort();
  const ends = positions.map((position) => pick(position.end_date)).filter(Boolean).sort();
  const start = starts[0] ? formatDate(starts[0]) : "-";
  const end = row.currentPositions.length > 0 ? "-" : (ends[ends.length - 1] ? formatDate(ends[ends.length - 1]) : "-");
  return `${start} tot ${end}`;
}

function rowPositionsForRoleFilter(row: OrganizationPersonRow, statusFilter: ViewerState["organizationStatusFilter"]): OrganizationPositionRecord[] {
  if (statusFilter === "active") return row.currentPositions;
  if (statusFilter === "inactive") return row.positions.filter((position) => !isCurrentOrganizationPosition(position));
  return row.positions;
}

function rowMatchesRoleFilter(row: OrganizationPersonRow, roleFilter: string, statusFilter: ViewerState["organizationStatusFilter"]): boolean {
  if (!roleFilter) return true;
  return rowPositionsForRoleFilter(row, statusFilter).some((position) => matchesRoleFilter(position, roleFilter));
}

function renderOrganizationPositions(positions: OrganizationPositionRecord[]): void {
  const roleFilter = state.organizationRoleFilter;
  const statusFilter = state.organizationStatusFilter;
  const groupFilter = state.organizationGroupFilter;
  const visibleRows = buildOrganizationPersonRows(positions)
    .filter((row) => statusFilter === "all" || (statusFilter === "active" ? row.currentPositions.length > 0 : row.currentPositions.length === 0))
    .filter((row) => rowMatchesRoleFilter(row, roleFilter, statusFilter))
    .filter((row) => !groupFilter || row.groupIds.includes(groupFilter))
    .sort((a, b) => a.displayName.localeCompare(b.displayName, "nl"));
  elements.organizationPositionsBody.replaceChildren();
  if (visibleRows.length === 0) {
    const row = document.createElement("tr");
    const cell = createCell(positions.length === 0 ? "Geen organisatieposities gevonden in de huidige export." : "Geen personen gevonden voor deze filters.");
    cell.colSpan = 6;
    row.appendChild(cell);
    elements.organizationPositionsBody.appendChild(row);
    return;
  }
  for (const personRow of visibleRows) {
    const row = document.createElement("tr");
    row.appendChild(createCell(personRow.displayName));
    row.appendChild(createCell(roleSummaryForRow(personRow)));
    row.appendChild(createCell(personRow.groupNames.length > 0 ? personRow.groupNames.join(", ") : "-"));
    row.appendChild(createCell(dateRangeForRow(personRow)));
    row.appendChild(createCell(personRow.currentPositions.length > 0 ? "Actief" : "Niet actief"));
    row.appendChild(createCell(text(personRow.email, "-")));
    elements.organizationPositionsBody.appendChild(row);
  }
}

function setActiveView(view: "documents" | "meetings" | "organization" | "dashboard", updateHash = false, scrollToView = false): void {
  state.activeView = view;
  elements.dashboardView.hidden = view !== "dashboard";
  elements.documentsView.hidden = view !== "documents";
  elements.meetingsView.hidden = view !== "meetings";
  elements.organizationView.hidden = view !== "organization";
  document.body.dataset.view = view;
  elements.navDashboard.classList.toggle("top-nav__link--active", view === "dashboard");
  elements.navDocuments.classList.toggle("top-nav__link--active", view === "documents");
  elements.navMeetings.classList.toggle("top-nav__link--active", view === "meetings");
  elements.navOrganization.classList.toggle("top-nav__link--active", view === "organization");
  elements.navDashboard.setAttribute("aria-current", view === "dashboard" ? "page" : "false");
  elements.navDocuments.setAttribute("aria-current", view === "documents" ? "page" : "false");
  elements.navMeetings.setAttribute("aria-current", view === "meetings" ? "page" : "false");
  elements.navOrganization.setAttribute("aria-current", view === "organization" ? "page" : "false");

  if (updateHash) updateHashForView(view);
  if (scrollToView) {
    const target = view === "meetings" ? elements.meetingsView : view === "organization" ? elements.organizationView : view === "dashboard" ? elements.dashboardView : elements.documentsView;
    target.scrollIntoView({ block: "start", behavior: "smooth" });
  }
}

function updateHashForView(view: "documents" | "meetings" | "organization" | "dashboard"): void {
  updateHash(view === "meetings" ? "#meetings" : view === "organization" ? "#organization" : view === "documents" ? "#documents" : "#dashboard");
}

function viewFromHash(): "documents" | "meetings" | "organization" | "dashboard" {
  if (window.location.hash === "#dashboard") return "dashboard";
  if (window.location.hash === "#meetings") return "meetings";
  if (window.location.hash === "#organization") return "organization";
  return "documents";
}

function applyHashState(scrollDocumentDetail = false): void {
  const documentId = documentIdFromHash();
  if (documentId) {
    const documentRecord = findDocumentById(documentId);
    setActiveView("documents", false, false);
    if (documentRecord) {
      ensureDocumentVisible(documentRecord);
      selectDocument(documentRecord, scrollDocumentDetail);
    }
    return;
  }
  setActiveView(viewFromHash(), false, false);
}

function attachEvents(): void {
  elements.navDashboard.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView("dashboard", true, false);
    renderDashboard();
  });
  elements.navDocuments.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView("documents", true, false);
  });
  elements.navMeetings.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView("meetings", true, false);
    renderMeetings();
  });
  elements.navOrganization.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView("organization", true, false);
    renderOrganization();
  });
  window.addEventListener("hashchange", () => applyHashState(true));
  elements.searchInput.addEventListener("input", () => { state.currentPage = 1; applyFilters(); });
  elements.typeFilter.addEventListener("change", () => { state.currentPage = 1; applyFilters(); });
  elements.sortSelect.addEventListener("change", () => { state.sortMode = elements.sortSelect.value; applyFilters(); });
  elements.pageSizeSelect.addEventListener("change", () => { state.pageSize = Number(elements.pageSizeSelect.value) || 50; state.currentPage = 1; applyFilters(); });
  elements.clearDocumentSelection.addEventListener("click", () => clearDocumentSelection());
  elements.clearMeetingSelection.addEventListener("click", () => clearMeetingSelection());
  elements.meetingSearchInput.addEventListener("input", () => {
    state.meetingQuery = elements.meetingSearchInput.value;
    state.meetingCurrentPage = 1;
    renderMeetings();
  });
  elements.meetingDateFilter.addEventListener("change", () => {
    state.meetingDateFilter = elements.meetingDateFilter.value as ViewerState["meetingDateFilter"];
    state.meetingCurrentPage = 1;
    renderMeetings();
  });
  elements.meetingSortSelect.addEventListener("change", () => {
    state.meetingSortMode = elements.meetingSortSelect.value as ViewerState["meetingSortMode"];
    state.meetingCurrentPage = 1;
    renderMeetings();
  });
  elements.meetingPageSizeSelect.addEventListener("change", () => {
    state.meetingPageSize = Number(elements.meetingPageSizeSelect.value) || 25;
    state.meetingCurrentPage = 1;
    renderMeetings();
  });
  elements.organizationRoleFilter.addEventListener("change", () => {
    state.organizationRoleFilter = elements.organizationRoleFilter.value;
    renderOrganization();
  });
  elements.organizationStatusFilter.addEventListener("change", () => {
    state.organizationStatusFilter = elements.organizationStatusFilter.value as "active" | "inactive" | "all";
    renderOrganization();
  });
  elements.organizationGroupFilter.addEventListener("change", () => {
    state.organizationGroupFilter = elements.organizationGroupFilter.value;
    renderOrganization();
  });
  elements.organizationGroupTypeFilter.addEventListener("change", () => {
    state.organizationGroupTypeFilter = elements.organizationGroupTypeFilter.value;
    renderOrganization();
  });
  for (const button of [elements.previousTop, elements.previousBottom]) button.addEventListener("click", () => { state.currentPage -= 1; renderDocuments(); });
  for (const button of [elements.nextTop, elements.nextBottom]) button.addEventListener("click", () => { state.currentPage += 1; renderDocuments(); });
  for (const button of [elements.previousMeetingTop, elements.previousMeetingBottom]) button.addEventListener("click", () => { state.meetingCurrentPage -= 1; renderMeetings(); });
  for (const button of [elements.nextMeetingTop, elements.nextMeetingBottom]) button.addEventListener("click", () => { state.meetingCurrentPage += 1; renderMeetings(); });
}

async function init(): Promise<void> {
  attachEvents();
  state.data = await loadPublicData();
  state.indexes = buildRelationIndexes(
    state.data.documents,
    state.data.meetings,
    state.data.agendaItems,
    state.data.meetingDocumentRelations,
    state.data.meetingItemDocumentRelations,
  );
  clearDerivedCaches();
  populateTypeFilter();
  renderSummary();
  renderDashboard();
  applyFilters();
  renderMeetings();
  renderOrganization();
  applyHashState(false);
  window.OpenRISMonitor = {
    indexes: state.indexes,
    focusDocumentById(documentId: string) {
      const documentRecord = findDocumentById(documentId);
      if (documentRecord) {
        setActiveView("documents", false, false);
        updateHash(documentHashFor(documentRecord));
        ensureDocumentVisible(documentRecord);
        selectDocument(documentRecord, true);
      }
    },
    focusMeetingById(meetingId: string) {
      const meeting = findMeetingById(meetingId);
      if (meeting) {
        setActiveView("meetings", true, false);
        selectMeeting(meeting, true);
      }
    },
  };
}

declare global {
  interface Window {
    OpenRISMonitor?: {
      indexes: RelationIndexes;
      focusDocumentById: (documentId: string) => void;
      focusMeetingById: (meetingId: string) => void;
    };
  }
}

init().catch((error: unknown) => {
  console.error(error);
  elements.statusMessage.textContent = "De viewer kon de publieke exports niet laden. Controleer data/public en de browserconsole.";
});
