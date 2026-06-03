const DATA_BASE = "../data/public";

const state = {
  latest: null,
  documents: [],
  filteredDocuments: [],
  meetings: [],
  meetingItems: [],
  meetingDocumentRelations: [],
  meetingItemDocumentRelations: [],
  meetingsById: new Map(),
  meetingItemsById: new Map(),
  meetingRelationsByDocumentId: new Map(),
  meetingItemRelationsByDocumentId: new Map(),
  currentPage: 1,
  pageSize: 50,
  sortMode: "date-desc",
};

const elements = {
  statusMessage: document.querySelector("#status-message"),
  municipality: document.querySelector("#municipality"),
  documentsSeen: document.querySelector("#documents-seen"),
  documentsNormalized: document.querySelector("#documents-normalized"),
  generatedAt: document.querySelector("#generated-at"),
  searchInput: document.querySelector("#search-input"),
  typeFilter: document.querySelector("#type-filter"),
  sortSelect: document.querySelector("#sort-select"),
  pageSizeSelect: document.querySelector("#page-size-select"),
  resultCount: document.querySelector("#result-count"),
  tableBody: document.querySelector("#documents-table-body"),
  previousTop: document.querySelector("#previous-page-top"),
  nextTop: document.querySelector("#next-page-top"),
  pageInfoTop: document.querySelector("#page-info-top"),
  previousBottom: document.querySelector("#previous-page-bottom"),
  nextBottom: document.querySelector("#next-page-bottom"),
  pageInfoBottom: document.querySelector("#page-info-bottom"),
};

function requireElements() {
  const missing = Object.entries(elements)
    .filter(([, element]) => !element)
    .map(([name]) => name);

  if (missing.length > 0) {
    throw new Error(`HTML mist verwachte elementen: ${missing.join(", ")}`);
  }
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Kan ${path} niet laden, status ${response.status}`);
  }
  return response.json();
}

function parseJsonObjects(text) {
  const lines = String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length > 0) {
    try {
      return lines.map((line) => JSON.parse(line));
    } catch (error) {
      console.warn("JSONL kon niet regel voor regel worden gelezen, probeer concatenated JSON objects.", error);
    }
  }

  // Fallback voor concatenated JSON objects zonder newline tussen records.
  const records = [];
  let depth = 0;
  let start = -1;
  let inString = false;
  let escaped = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];

    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (character === "\\") {
        escaped = true;
      } else if (character === '"') {
        inString = false;
      }
      continue;
    }

    if (character === '"') {
      inString = true;
      continue;
    }

    if (character === "{") {
      if (depth === 0) start = index;
      depth += 1;
    } else if (character === "}") {
      depth -= 1;
      if (depth === 0 && start >= 0) {
        records.push(JSON.parse(text.slice(start, index + 1)));
        start = -1;
      }
    }
  }

  if (records.length === 0) {
    throw new Error("JSONL-bestand bevat geen parsebare records");
  }

  return records;
}

async function fetchJsonl(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Kan ${path} niet laden, status ${response.status}`);
  }

  const text = await response.text();
  return parseJsonObjects(text);
}

async function fetchOptionalJsonl(path) {
  if (!path) return [];

  try {
    return await fetchJsonl(path);
  } catch (error) {
    console.warn(`Optionele relationele export kon niet worden geladen: ${path}`, error);
    return [];
  }
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);

  return new Intl.DateTimeFormat("nl-NL", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);

  return new Intl.DateTimeFormat("nl-NL", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatBytes(value) {
  const bytes = Number(value);
  if (!Number.isFinite(bytes)) return "-";
  if (bytes === 0) return "0 B";

  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / Math.pow(1024, index);
  return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getDocumentDate(documentRecord) {
  return (
    documentRecord.publication_datetime ||
    documentRecord.date_published ||
    documentRecord.publication_date ||
    documentRecord.document_date ||
    documentRecord.date ||
    documentRecord.retrieved_at ||
    ""
  );
}

function getDocumentTimestamp(documentRecord) {
  const value = getDocumentDate(documentRecord);
  if (!value) return 0;

  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? timestamp : 0;
}

function getSourceIdNumber(documentRecord) {
  const value = Number(documentRecord.source_id ?? documentRecord.raw?.id ?? 0);
  return Number.isFinite(value) ? value : 0;
}

function getCompactType(documentRecord) {
  return documentRecord.normalized_document_type || "unknown";
}

function getCompactTypeLabel(documentRecord) {
  return documentRecord.normalized_document_type_label || "Onbekend";
}

function getDocumentId(documentRecord) {
  if (documentRecord.id) return documentRecord.id;
  if (documentRecord.municipality_slug && documentRecord.source_id) {
    return `${documentRecord.municipality_slug}-document-${documentRecord.source_id}`;
  }
  return null;
}

function getDocumentTitle(documentRecord) {
  return documentRecord.title || documentRecord.description || documentRecord.filename || "Geen titel";
}

function addToLookupList(map, key, value) {
  if (!key) return;
  const list = map.get(key) || [];
  list.push(value);
  map.set(key, list);
}

function buildRelationLookups() {
  state.meetingsById = new Map(state.meetings.map((meeting) => [meeting.id, meeting]));
  state.meetingItemsById = new Map(state.meetingItems.map((item) => [item.id, item]));
  state.meetingRelationsByDocumentId = new Map();
  state.meetingItemRelationsByDocumentId = new Map();

  for (const relation of state.meetingDocumentRelations) {
    addToLookupList(state.meetingRelationsByDocumentId, relation.document_id, relation);
  }

  for (const relation of state.meetingItemDocumentRelations) {
    addToLookupList(state.meetingItemRelationsByDocumentId, relation.document_id, relation);
  }
}

function getDocumentRelationContext(documentRecord) {
  const documentId = getDocumentId(documentRecord);
  if (!documentId) return [];

  const contexts = [];
  const seen = new Set();
  const itemRelations = state.meetingItemRelationsByDocumentId.get(documentId) || [];

  for (const relation of itemRelations) {
    const meeting = state.meetingsById.get(relation.meeting_id);
    const item = state.meetingItemsById.get(relation.meeting_item_id);
    const key = `item:${relation.meeting_item_id}:${relation.document_id}`;
    if (seen.has(key)) continue;
    seen.add(key);
    contexts.push({ meeting, item });
  }

  const meetingRelations = state.meetingRelationsByDocumentId.get(documentId) || [];
  for (const relation of meetingRelations) {
    const meeting = state.meetingsById.get(relation.meeting_id);
    const key = `meeting:${relation.meeting_id}:${relation.document_id}`;
    if (seen.has(key)) continue;
    seen.add(key);
    contexts.push({ meeting, item: null });
  }

  return contexts;
}

function formatMeetingLabel(meeting) {
  if (!meeting) return "Onbekende vergadering";
  return [meeting.description, meeting.date, meeting.start_time].filter(Boolean).join(", ");
}

function formatMeetingItemLabel(item) {
  if (!item) return null;
  return [item.number, item.title].filter(Boolean).join(" ");
}

function renderRelationContext(documentRecord) {
  const contexts = getDocumentRelationContext(documentRecord);
  if (contexts.length === 0) return "";

  const visible = contexts.slice(0, 2);
  const extraCount = contexts.length - visible.length;
  const rows = visible
    .map(({ meeting, item }) => {
      const meetingLabel = formatMeetingLabel(meeting);
      const itemLabel = formatMeetingItemLabel(item);
      const itemText = itemLabel ? `, agendapunt: ${itemLabel}` : "";
      return `<li>${escapeHtml(meetingLabel)}${escapeHtml(itemText)}</li>`;
    })
    .join("");
  const extraHtml = extraCount > 0 ? `<li>+ ${extraCount} extra koppeling(en)</li>` : "";

  return `<div class="relation-context" aria-label="Relationele context"><ul>${rows}${extraHtml}</ul></div>`;
}

function renderSummary() {
  const latest = state.latest || {};
  elements.municipality.textContent = latest.municipality || latest.municipality_id || "-";
  elements.documentsSeen.textContent = latest.documents_seen ?? "-";
  elements.documentsNormalized.textContent = latest.documents_normalized ?? "-";
  elements.generatedAt.textContent = formatDateTime(latest.generated_at);

  const documentsWithRelations = state.documents.filter((documentRecord) => {
    return getDocumentRelationContext(documentRecord).length > 0;
  }).length;
  const relationText = latest.relations_enabled
    ? ` Relationele context: ${latest.relations_summary?.meetings_seen ?? 0} vergaderingen, ${latest.relations_summary?.meeting_items_seen ?? 0} agendapunten. ${documentsWithRelations} getoonde documenten hebben een koppeling.`
    : "";
  elements.statusMessage.textContent = `${state.documents.length} documenten geladen.${relationText}`;
}

function renderTypeFilter() {
  const selected = elements.typeFilter.value;
  const typeMap = new Map();

  for (const item of state.documents) {
    typeMap.set(getCompactType(item), getCompactTypeLabel(item));
  }

  const types = [...typeMap.entries()].sort((a, b) => a[1].localeCompare(b[1], "nl"));
  elements.typeFilter.innerHTML = '<option value="">Alle compacte documenttypen</option>';

  for (const [value, label] of types) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    elements.typeFilter.appendChild(option);
  }

  elements.typeFilter.value = selected;
}

function compareByDate(a, b, direction) {
  const timestampDifference = getDocumentTimestamp(a) - getDocumentTimestamp(b);
  if (timestampDifference !== 0) {
    return direction === "asc" ? timestampDifference : -timestampDifference;
  }

  const sourceDifference = getSourceIdNumber(a) - getSourceIdNumber(b);
  return direction === "asc" ? sourceDifference : -sourceDifference;
}

function sortDocuments(documents) {
  return documents.slice().sort((a, b) => {
    if (state.sortMode === "date-asc") {
      return compareByDate(a, b, "asc");
    }
    if (state.sortMode === "title-asc") {
      return String(getDocumentTitle(a)).localeCompare(String(getDocumentTitle(b)), "nl");
    }
    if (state.sortMode === "type-asc") {
      return String(getCompactTypeLabel(a)).localeCompare(String(getCompactTypeLabel(b)), "nl");
    }
    if (state.sortMode === "source-type-asc") {
      return String(a.document_type || "").localeCompare(String(b.document_type || ""), "nl");
    }
    if (state.sortMode === "size-desc") {
      return Number(b.file_size_bytes || 0) - Number(a.file_size_bytes || 0);
    }
    if (state.sortMode === "size-asc") {
      return Number(a.file_size_bytes || 0) - Number(b.file_size_bytes || 0);
    }
    return compareByDate(a, b, "desc");
  });
}

function appendTextCell(row, className, value) {
  const cell = document.createElement("td");
  cell.className = className;
  cell.textContent = value;
  row.appendChild(cell);
  return cell;
}

function makeTechnicalTextWrappable(value) {
  return String(value || "-").replace(/([_./\-])/g, "$1\u200B");
}

function appendFilenameCell(row, value) {
  const cell = document.createElement("td");
  cell.className = "filename-cell";
  const span = document.createElement("span");
  span.className = "filename-text";
  span.textContent = makeTechnicalTextWrappable(value);
  cell.title = value || "";
  cell.appendChild(span);
  row.appendChild(cell);
  return cell;
}

function createRelationContextElement(documentRecord) {
  const contexts = getDocumentRelationContext(documentRecord);
  if (contexts.length === 0) return null;

  const wrapper = document.createElement("div");
  wrapper.className = "relation-context";
  wrapper.setAttribute("aria-label", "Relationele context");

  const list = document.createElement("ul");
  const visible = contexts.slice(0, 2);
  const extraCount = contexts.length - visible.length;

  for (const { meeting, item } of visible) {
    const listItem = document.createElement("li");
    const meetingLabel = formatMeetingLabel(meeting);
    const itemLabel = formatMeetingItemLabel(item);
    const itemText = itemLabel ? `, agendapunt: ${itemLabel}` : "";
    listItem.textContent = `${meetingLabel}${itemText}`;
    list.appendChild(listItem);
  }

  if (extraCount > 0) {
    const extraItem = document.createElement("li");
    extraItem.textContent = `+ ${extraCount} extra koppeling(en)`;
    list.appendChild(extraItem);
  }

  wrapper.appendChild(list);
  return wrapper;
}

function renderEmptyRow(message) {
  elements.tableBody.replaceChildren();
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.colSpan = 7;
  cell.textContent = message;
  row.appendChild(cell);
  elements.tableBody.appendChild(row);
}

function updatePagination(totalPages) {
  const pageText = `Pagina ${state.currentPage} van ${totalPages}`;
  elements.pageInfoTop.textContent = pageText;
  elements.pageInfoBottom.textContent = pageText;

  const previousDisabled = state.currentPage <= 1;
  const nextDisabled = state.currentPage >= totalPages;
  elements.previousTop.disabled = previousDisabled;
  elements.previousBottom.disabled = previousDisabled;
  elements.nextTop.disabled = nextDisabled;
  elements.nextBottom.disabled = nextDisabled;
}

function renderDocuments() {
  const sorted = sortDocuments(state.filteredDocuments);
  const totalPages = Math.max(1, Math.ceil(sorted.length / state.pageSize));
  state.currentPage = Math.min(Math.max(1, state.currentPage), totalPages);

  const start = (state.currentPage - 1) * state.pageSize;
  const pageDocuments = sorted.slice(start, start + state.pageSize);

  elements.resultCount.textContent = `${sorted.length} van ${state.documents.length} documenten, ${state.pageSize} per pagina`;
  updatePagination(totalPages);

  if (pageDocuments.length === 0) {
    renderEmptyRow("Geen documenten gevonden.");
    return;
  }

  elements.tableBody.replaceChildren();

  for (const documentRecord of pageDocuments) {
    const row = document.createElement("tr");
    const downloadUrl = documentRecord.download_url || documentRecord.source_url;

    appendTextCell(row, "date-cell", formatDate(getDocumentDate(documentRecord)));
    appendTextCell(row, "type-cell", getCompactTypeLabel(documentRecord));
    appendTextCell(row, "source-type-cell", documentRecord.document_type || "Onbekend");

    const titleCell = document.createElement("td");
    titleCell.className = "title-cell";
    const title = document.createElement("div");
    title.className = "document-title";
    title.textContent = getDocumentTitle(documentRecord);
    titleCell.appendChild(title);
    const relationContext = createRelationContextElement(documentRecord);
    if (relationContext) titleCell.appendChild(relationContext);
    row.appendChild(titleCell);

    appendFilenameCell(row, documentRecord.filename || "-");
    appendTextCell(row, "size-cell", formatBytes(documentRecord.file_size_bytes));

    const downloadCell = document.createElement("td");
    downloadCell.className = "download-cell";
    if (downloadUrl) {
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.rel = "noopener noreferrer";
      link.textContent = "PDF";
      downloadCell.appendChild(link);
    } else {
      downloadCell.textContent = "-";
    }
    row.appendChild(downloadCell);

    elements.tableBody.appendChild(row);
  }
}


function applyFilters() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const type = elements.typeFilter.value;

  state.filteredDocuments = state.documents.filter((documentRecord) => {
    const matchesType = !type || getCompactType(documentRecord) === type;
    const relationContext = getDocumentRelationContext(documentRecord)
      .map(({ meeting, item }) =>
        [meeting?.description, meeting?.date, meeting?.dmu_name, item?.number, item?.title]
          .filter(Boolean)
          .join(" "),
      )
      .join(" ");

    const haystack = [
      getDocumentTitle(documentRecord),
      documentRecord.description,
      documentRecord.filename,
      documentRecord.document_type,
      documentRecord.normalized_document_type,
      documentRecord.normalized_document_type_label,
      documentRecord.source_id,
      documentRecord.source_object_id,
      relationContext,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    const matchesQuery = !query || haystack.includes(query);
    return matchesType && matchesQuery;
  });

  state.currentPage = 1;
  renderDocuments();
}

function changePage(delta) {
  state.currentPage += delta;
  renderDocuments();
}

function bindEvents() {
  elements.searchInput.addEventListener("input", applyFilters);
  elements.typeFilter.addEventListener("change", applyFilters);
  elements.sortSelect.addEventListener("change", () => {
    state.sortMode = elements.sortSelect.value;
    state.currentPage = 1;
    renderDocuments();
  });
  elements.pageSizeSelect.addEventListener("change", () => {
    state.pageSize = Number(elements.pageSizeSelect.value);
    state.currentPage = 1;
    renderDocuments();
  });
  elements.previousTop.addEventListener("click", () => changePage(-1));
  elements.previousBottom.addEventListener("click", () => changePage(-1));
  elements.nextTop.addEventListener("click", () => changePage(1));
  elements.nextBottom.addEventListener("click", () => changePage(1));
}

async function loadRelationData(outputs) {
  const [meetings, meetingItems, meetingDocumentRelations, meetingItemDocumentRelations] = await Promise.all([
    fetchOptionalJsonl(outputs.meetings ? `${DATA_BASE}/${outputs.meetings}` : null),
    fetchOptionalJsonl(outputs.meeting_items ? `${DATA_BASE}/${outputs.meeting_items}` : null),
    fetchOptionalJsonl(outputs.meeting_documents ? `${DATA_BASE}/${outputs.meeting_documents}` : null),
    fetchOptionalJsonl(outputs.meeting_item_documents ? `${DATA_BASE}/${outputs.meeting_item_documents}` : null),
  ]);

  state.meetings = meetings;
  state.meetingItems = meetingItems;
  state.meetingDocumentRelations = meetingDocumentRelations;
  state.meetingItemDocumentRelations = meetingItemDocumentRelations;
  buildRelationLookups();
}

async function init() {
  try {
    requireElements();
    state.latest = await fetchJson(`${DATA_BASE}/latest.json`);
    const latest = state.latest;
    const outputs = latest.outputs || latest.exports || {};
    const documentsPath = outputs.documents || "documents.jsonl";
    state.documents = await fetchJsonl(`${DATA_BASE}/${documentsPath}`);
    await loadRelationData(outputs);
    state.filteredDocuments = state.documents;
    renderSummary();
    renderTypeFilter();
    renderDocuments();
    bindEvents();
  } catch (error) {
    console.error(error);
    if (elements.statusMessage) {
      elements.statusMessage.textContent = "De publieke data kon niet worden geladen.";
    }
    if (elements.tableBody) {
      renderEmptyRow(error.message);
    }
  }
}

init();
