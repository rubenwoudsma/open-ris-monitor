import { loadPublicData } from "./data/loaders";
import { buildRelationIndexes, getDocumentIdentifiers, getRecordId } from "./data/relations";
import type { DocumentRecord, PublicDataSet, RelationIndexes } from "./data/types";
import { formatBytes, formatDate, formatDateTime, pick, safeUrl, text, timestamp } from "./ui/format";

interface ViewerState {
  data: PublicDataSet | null;
  indexes: RelationIndexes | null;
  filteredDocuments: DocumentRecord[];
  currentPage: number;
  pageSize: number;
  sortMode: string;
  pinnedDocumentIds: Set<string> | null;
}

type RequiredElements = {
  statusMessage: HTMLElement;
  municipality: HTMLElement;
  documentsSeen: HTMLElement;
  documentsNormalized: HTMLElement;
  generatedAt: HTMLElement;
  municipalityCopy: HTMLElement;
  generatedAtCopy: HTMLElement;
  searchInput: HTMLInputElement;
  typeFilter: HTMLSelectElement;
  sortSelect: HTMLSelectElement;
  pageSizeSelect: HTMLSelectElement;
  resultCount: HTMLElement;
  documentContext: HTMLElement;
  meetingsCount: HTMLElement;
  agendaItemsCount: HTMLElement;
  linkedDocumentsCount: HTMLElement;
  visibleDocumentsCount: HTMLElement;
  tableBody: HTMLElement;
  previousTop: HTMLButtonElement;
  nextTop: HTMLButtonElement;
  pageInfoTop: HTMLElement;
  previousBottom: HTMLButtonElement;
  nextBottom: HTMLButtonElement;
  pageInfoBottom: HTMLElement;
};

const state: ViewerState = {
  data: null,
  indexes: null,
  filteredDocuments: [],
  currentPage: 1,
  pageSize: 50,
  sortMode: "date-desc",
  pinnedDocumentIds: null,
};

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
  searchInput: byId("search-input"),
  typeFilter: byId("type-filter"),
  sortSelect: byId("sort-select"),
  pageSizeSelect: byId("page-size-select"),
  resultCount: byId("result-count"),
  documentContext: byId("document-context"),
  meetingsCount: byId("meetings-count"),
  agendaItemsCount: byId("agenda-items-count"),
  linkedDocumentsCount: byId("linked-documents-count"),
  visibleDocumentsCount: byId("visible-documents-count"),
  tableBody: byId("documents-table-body"),
  previousTop: byId("previous-page-top"),
  nextTop: byId("next-page-top"),
  pageInfoTop: byId("page-info-top"),
  previousBottom: byId("previous-page-bottom"),
  nextBottom: byId("next-page-bottom"),
  pageInfoBottom: byId("page-info-bottom"),
};

function getDocumentId(documentRecord: DocumentRecord): string {
  return getDocumentIdentifiers(documentRecord)[0] ?? "";
}

function getDocumentTitle(documentRecord: DocumentRecord): string {
  return pick(documentRecord.title, documentRecord.description, documentRecord.filename) || "Geen titel";
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

function getCompactType(documentRecord: DocumentRecord): string {
  return pick(documentRecord.normalized_document_type) || "unknown";
}

function getCompactTypeLabel(documentRecord: DocumentRecord): string {
  return pick(documentRecord.normalized_document_type_label, documentRecord.normalized_document_type) || "Onbekend";
}

function relationLabelsForDocument(documentRecord: DocumentRecord): string[] {
  if (!state.indexes) return [];
  const labels: string[] = [];
  const identifiers = getDocumentIdentifiers(documentRecord);

  for (const id of identifiers) {
    for (const meetingId of state.indexes.meetingIdsByDocumentId.get(id) ?? []) {
      const meeting = state.indexes.meetingsById.get(meetingId);
      labels.push([pick(meeting?.description, meeting?.title), meeting?.date].filter(Boolean).join(", "));
    }

    for (const itemId of state.indexes.agendaItemIdsByDocumentId.get(id) ?? []) {
      const item = state.indexes.agendaItemsById.get(itemId);
      labels.push([item?.number, item?.title].filter(Boolean).join(" "));
    }
  }

  return [...new Set(labels.filter(Boolean))];
}

function searchBlob(documentRecord: DocumentRecord): string {
  return [
    getDocumentTitle(documentRecord),
    documentRecord.description,
    documentRecord.filename,
    documentRecord.document_type,
    documentRecord.normalized_document_type,
    documentRecord.normalized_document_type_label,
    documentRecord.source_id,
    documentRecord.source_object_id,
    relationLabelsForDocument(documentRecord).join(" "),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
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

  const linkedDocumentCount = (state.data?.documents ?? []).filter((record) => relationLabelsForDocument(record).length > 0).length;
  elements.linkedDocumentsCount.textContent = text(linkedDocumentCount);

  const relationText = latest.relations_enabled
    ? ` Relationele context: ${latest.relations_summary?.meetings_seen ?? 0} vergaderingen, ${latest.relations_summary?.meeting_items_seen ?? 0} agendapunten. ${linkedDocumentCount} documenten hebben een koppeling.`
    : "";
  elements.statusMessage.textContent = `${state.data?.documents.length ?? 0} documenten geladen.${relationText}`;
}

function populateTypeFilter(): void {
  const options = new Map<string, string>();
  for (const documentRecord of state.data?.documents ?? []) {
    options.set(getCompactType(documentRecord), getCompactTypeLabel(documentRecord));
  }

  for (const [value, label] of [...options.entries()].sort((a, b) => a[1].localeCompare(b[1], "nl"))) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    elements.typeFilter.appendChild(option);
  }
}

function sortDocuments(records: DocumentRecord[]): DocumentRecord[] {
  const sorted = [...records];
  const byTitle = (a: DocumentRecord, b: DocumentRecord) => getDocumentTitle(a).localeCompare(getDocumentTitle(b), "nl");
  const byType = (a: DocumentRecord, b: DocumentRecord) => getCompactTypeLabel(a).localeCompare(getCompactTypeLabel(b), "nl");
  const bySourceType = (a: DocumentRecord, b: DocumentRecord) => text(a.document_type).localeCompare(text(b.document_type), "nl");
  const bySize = (a: DocumentRecord, b: DocumentRecord) => Number(a.size_bytes ?? 0) - Number(b.size_bytes ?? 0);
  const byDate = (a: DocumentRecord, b: DocumentRecord) => timestamp(getDocumentDate(a)) - timestamp(getDocumentDate(b));

  switch (state.sortMode) {
    case "date-asc":
      return sorted.sort(byDate);
    case "title-asc":
      return sorted.sort(byTitle);
    case "type-asc":
      return sorted.sort(byType);
    case "source-type-asc":
      return sorted.sort(bySourceType);
    case "size-desc":
      return sorted.sort((a, b) => bySize(b, a));
    case "size-asc":
      return sorted.sort(bySize);
    case "date-desc":
    default:
      return sorted.sort((a, b) => byDate(b, a));
  }
}

function applyFilters(): void {
  const query = elements.searchInput.value.trim().toLowerCase();
  const type = elements.typeFilter.value;
  const allDocuments = state.data?.documents ?? [];

  let records = allDocuments.filter((documentRecord) => {
    const documentId = getDocumentId(documentRecord);
    if (state.pinnedDocumentIds && !state.pinnedDocumentIds.has(documentId)) return false;
    if (type && getCompactType(documentRecord) !== type) return false;
    if (query && !searchBlob(documentRecord).includes(query)) return false;
    return true;
  });

  records = sortDocuments(records);
  state.filteredDocuments = records;
  renderDocuments();
}

function createCell(value: string): HTMLTableCellElement {
  const cell = document.createElement("td");
  cell.textContent = value;
  return cell;
}

function createTitleCell(documentRecord: DocumentRecord): HTMLTableCellElement {
  const cell = document.createElement("td");
  const title = document.createElement("strong");
  title.textContent = getDocumentTitle(documentRecord);
  cell.appendChild(title);

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

function renderDocuments(): void {
  const total = state.filteredDocuments.length;
  const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
  state.currentPage = Math.min(Math.max(state.currentPage, 1), totalPages);
  const start = (state.currentPage - 1) * state.pageSize;
  const pageRecords = state.filteredDocuments.slice(start, start + state.pageSize);

  elements.resultCount.textContent = `${total} document(en)`;
  elements.visibleDocumentsCount.textContent = `${total} zichtbaar`;
  elements.tableBody.replaceChildren();

  if (pageRecords.length === 0) {
    const row = document.createElement("tr");
    const cell = createCell("Geen documenten gevonden.");
    cell.colSpan = 7;
    row.appendChild(cell);
    elements.tableBody.appendChild(row);
  }

  for (const documentRecord of pageRecords) {
    const row = document.createElement("tr");
    row.appendChild(createCell(formatDate(getDocumentDate(documentRecord))));
    row.appendChild(createCell(getCompactTypeLabel(documentRecord)));
    row.appendChild(createCell(text(documentRecord.document_type)));
    row.appendChild(createTitleCell(documentRecord));
    row.appendChild(createCell(text(documentRecord.filename)));
    row.appendChild(createCell(formatBytes(documentRecord.size_bytes)));

    const linkCell = document.createElement("td");
    const href = safeUrl(pick(documentRecord.download_url, documentRecord.source_url));
    if (href) {
      const link = document.createElement("a");
      link.href = href;
      link.textContent = "Open";
      link.rel = "noopener noreferrer";
      link.target = "_blank";
      linkCell.appendChild(link);
    } else {
      linkCell.textContent = "-";
    }
    row.appendChild(linkCell);
    elements.tableBody.appendChild(row);
  }

  const pageText = `Pagina ${state.currentPage} van ${totalPages}`;
  elements.pageInfoTop.textContent = pageText;
  elements.pageInfoBottom.textContent = pageText;
  for (const button of [elements.previousTop, elements.previousBottom]) button.disabled = state.currentPage <= 1;
  for (const button of [elements.nextTop, elements.nextBottom]) button.disabled = state.currentPage >= totalPages;
}

function restoreDeepLink(): void {
  const params = new URLSearchParams(window.location.search);
  const query = params.get("q") ?? "";
  const documentId = params.get("documentId") ?? params.get("doc") ?? "";

  if (query) elements.searchInput.value = query;
  if (documentId) {
    state.pinnedDocumentIds = new Set([documentId]);
    elements.documentContext.hidden = false;
    elements.documentContext.textContent = `Gedeelde documentselectie: ${documentId}`;
  }
}

function attachEvents(): void {
  elements.searchInput.addEventListener("input", () => {
    state.pinnedDocumentIds = null;
    state.currentPage = 1;
    applyFilters();
  });
  elements.typeFilter.addEventListener("change", () => {
    state.currentPage = 1;
    applyFilters();
  });
  elements.sortSelect.addEventListener("change", () => {
    state.sortMode = elements.sortSelect.value;
    applyFilters();
  });
  elements.pageSizeSelect.addEventListener("change", () => {
    state.pageSize = Number(elements.pageSizeSelect.value) || 50;
    state.currentPage = 1;
    applyFilters();
  });

  for (const button of [elements.previousTop, elements.previousBottom]) {
    button.addEventListener("click", () => {
      state.currentPage -= 1;
      renderDocuments();
    });
  }
  for (const button of [elements.nextTop, elements.nextBottom]) {
    button.addEventListener("click", () => {
      state.currentPage += 1;
      renderDocuments();
    });
  }
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

  restoreDeepLink();
  populateTypeFilter();
  renderSummary();
  applyFilters();

  window.OpenRISMonitor = {
    indexes: state.indexes,
    focusDocumentById(documentId: string) {
      state.pinnedDocumentIds = new Set([documentId]);
      state.currentPage = 1;
      applyFilters();
    },
  };
}

declare global {
  interface Window {
    OpenRISMonitor?: {
      indexes: RelationIndexes;
      focusDocumentById: (documentId: string) => void;
    };
  }
}

init().catch((error: unknown) => {
  console.error(error);
  elements.statusMessage.textContent = "De viewer kon de publieke exports niet laden. Controleer data/public en de browserconsole.";
});
