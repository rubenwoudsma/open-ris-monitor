const DATA_BASE = "../data/public";

const state = {
  latest: null,
  documents: [],
  filteredDocuments: [],
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

async function fetchJsonl(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Kan ${path} niet laden, status ${response.status}`);
  }
  const text = await response.text();
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
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
    documentRecord.retrieved_at ||
    ""
  );
}

function getCompactType(documentRecord) {
  return documentRecord.normalized_document_type || "unknown";
}

function getCompactTypeLabel(documentRecord) {
  return documentRecord.normalized_document_type_label || "Onbekend";
}

function renderSummary() {
  const latest = state.latest || {};
  elements.municipality.textContent = latest.municipality || latest.municipality_id || "-";
  elements.documentsSeen.textContent = latest.documents_seen ?? "-";
  elements.documentsNormalized.textContent = latest.documents_normalized ?? "-";
  elements.generatedAt.textContent = formatDateTime(latest.generated_at);
  elements.statusMessage.textContent = `Harvest ${latest.harvest_run_id || "onbekend"} is geladen.`;
}

function renderTypeFilter() {
  const selected = elements.typeFilter.value;
  const typeMap = new Map();
  for (const item of state.documents) {
    const value = getCompactType(item);
    const label = getCompactTypeLabel(item);
    typeMap.set(value, label);
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

function sortDocuments(documents) {
  return documents.slice().sort((a, b) => {
    if (state.sortMode === "date-asc") {
      return String(getDocumentDate(a)).localeCompare(String(getDocumentDate(b)));
    }
    if (state.sortMode === "title-asc") {
      return String(a.title || a.description || "").localeCompare(String(b.title || b.description || ""), "nl");
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
    return String(getDocumentDate(b)).localeCompare(String(getDocumentDate(a)));
  });
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
    elements.tableBody.innerHTML = '<tr><td colspan="7">Geen documenten gevonden.</td></tr>';
    return;
  }

  elements.tableBody.innerHTML = pageDocuments
    .map((documentRecord) => {
      const downloadUrl = documentRecord.download_url || documentRecord.source_url;
      const downloadLink = downloadUrl
        ? `<a href="${escapeHtml(downloadUrl)}" target="_blank" rel="noopener noreferrer">PDF</a>`
        : "-";
      return `
        <tr>
          <td>${escapeHtml(formatDate(getDocumentDate(documentRecord)))}</td>
          <td>${escapeHtml(getCompactTypeLabel(documentRecord))}</td>
          <td>${escapeHtml(documentRecord.document_type || "Onbekend")}</td>
          <td class="wrap">${escapeHtml(documentRecord.title || documentRecord.description || "Geen titel")}</td>
          <td class="wrap">${escapeHtml(documentRecord.filename || "-")}</td>
          <td>${escapeHtml(formatBytes(documentRecord.file_size_bytes))}</td>
          <td>${downloadLink}</td>
        </tr>
      `;
    })
    .join("");
}

function applyFilters() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const type = elements.typeFilter.value;
  state.filteredDocuments = state.documents.filter((documentRecord) => {
    const matchesType = !type || getCompactType(documentRecord) === type;
    const haystack = [
      documentRecord.title,
      documentRecord.description,
      documentRecord.filename,
      documentRecord.document_type,
      documentRecord.normalized_document_type,
      documentRecord.normalized_document_type_label,
      documentRecord.source_id,
      documentRecord.source_object_id,
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

async function init() {
  try {
    requireElements();
    state.latest = await fetchJson(`${DATA_BASE}/latest.json`);
    const documentsPath = state.latest.outputs?.documents || "documents.jsonl";
    state.documents = await fetchJsonl(`${DATA_BASE}/${documentsPath}`);
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
      elements.tableBody.innerHTML = `<tr><td colspan="7">${escapeHtml(error.message)}</td></tr>`;
    }
  }
}

init();
