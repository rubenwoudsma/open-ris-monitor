import { loadPublicData } from "./data/loaders.js";
import { buildRelationIndexes, getDocumentIdentifiers, getRecordId } from "./data/relations.js";
import type {
  AgendaItemRecord,
  DocumentRecord,
  DocumentVersionRecord,
  MeetingRecord,
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
  meetingCurrentPage: number;
  meetingPageSize: number;
  activeView: "documents" | "meetings";
}

interface DerivedCaches {
  documentRelationLabelsByKey: Map<string, string[]>;
  documentSearchBlobByKey: Map<string, string>;
  meetingSearchBlobById: Map<string, string>;
  filteredMeetingsByKey: Map<string, MeetingRecord[]>;
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
  dataQualityNotice: HTMLElement;
  documentsView: HTMLElement;
  meetingsView: HTMLElement;
  navDocuments: HTMLAnchorElement;
  navMeetings: HTMLAnchorElement;
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
  meetingCurrentPage: 1,
  meetingPageSize: 25,
  activeView: "documents",
};

const derivedCaches: DerivedCaches = {
  documentRelationLabelsByKey: new Map<string, string[]>(),
  documentSearchBlobByKey: new Map<string, string>(),
  meetingSearchBlobById: new Map<string, string>(),
  filteredMeetingsByKey: new Map<string, MeetingRecord[]>(),
};

function clearDerivedCaches(): void {
  derivedCaches.documentRelationLabelsByKey.clear();
  derivedCaches.documentSearchBlobByKey.clear();
  derivedCaches.meetingSearchBlobById.clear();
  derivedCaches.filteredMeetingsByKey.clear();
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
  dataQualityNotice: byId("data-quality-notice"),
  documentsView: byId("documents-view"),
  meetingsView: byId("meetings-view"),
  navDocuments: byId("nav-documents"),
  navMeetings: byId("nav-meetings"),
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
  elements.statusMessage.textContent = `${state.data?.documents.length ?? 0} documenten geladen.${relationText}`;
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

function filteredMeetings(): MeetingRecord[] {
  const query = state.meetingQuery.trim().toLowerCase();
  const cacheKey = `${query}|${state.meetingSortMode}`;
  const cached = derivedCaches.filteredMeetingsByKey.get(cacheKey);
  if (cached) return cached;

  const meetings = (state.data?.meetings ?? []).filter((meeting) => {
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

function setActiveView(view: "documents" | "meetings", updateHash = false, scrollToView = false): void {
  state.activeView = view;
  elements.documentsView.hidden = view !== "documents";
  elements.meetingsView.hidden = view !== "meetings";
  document.body.dataset.view = view;
  elements.navDocuments.classList.toggle("top-nav__link--active", view === "documents");
  elements.navMeetings.classList.toggle("top-nav__link--active", view === "meetings");
  elements.navDocuments.setAttribute("aria-current", view === "documents" ? "page" : "false");
  elements.navMeetings.setAttribute("aria-current", view === "meetings" ? "page" : "false");

  if (updateHash) updateHashForView(view);
  if (scrollToView) {
    const target = view === "meetings" ? elements.meetingsView : elements.documentsView;
    target.scrollIntoView({ block: "start", behavior: "smooth" });
  }
}

function updateHashForView(view: "documents" | "meetings"): void {
  updateHash(view === "meetings" ? "#meetings" : "#documents");
}

function viewFromHash(): "documents" | "meetings" {
  return window.location.hash === "#meetings" ? "meetings" : "documents";
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
  elements.navDocuments.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView("documents", true, false);
  });
  elements.navMeetings.addEventListener("click", (event) => {
    event.preventDefault();
    setActiveView("meetings", true, false);
    renderMeetings();
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
  applyFilters();
  renderMeetings();
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
