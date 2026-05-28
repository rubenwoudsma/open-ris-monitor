const DATA_PATHS = {
  latest: "../data/public/latest.json",
  documents: "../data/public/documents.jsonl",
};

const state = {
  latest: null,
  documents: [],
  filtered: [],
  search: "",
  type: "",
  sort: "date_desc",
  pageSize: 50,
  page: 1,
};

const elements = {
  status: document.getElementById("status-message"),
  metrics: document.getElementById("metric-grid"),
  search: document.getElementById("search-input"),
  typeFilter: document.getElementById("type-filter"),
  sort: document.getElementById("sort-select"),
  pageSize: document.getElementById("page-size-select"),
  resultSummary: document.getElementById("result-summary"),
  pageSummary: document.getElementById("page-summary"),
  pageIndicator: document.getElementById("page-indicator"),
  previous: document.getElementById("prev-page"),
  next: document.getElementById("next-page"),
  reset: document.getElementById("reset-button"),
  reload: document.getElementById("reload-button"),
  tbody: document.getElementById("documents-body"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function parseJsonLines(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Kon ${path} niet laden: ${response.status}`);
  }
  return response.json();
}

async function fetchJsonl(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Kon ${path} niet laden: ${response.status}`);
  }
  return parseJsonLines(await response.text());
}

function getTitle(documentRecord) {
  return documentRecord.title || documentRecord.description || documentRecord.filename || "Zonder titel";
}

function getDateValue(documentRecord) {
  return documentRecord.date_published || documentRecord.publication_datetime || documentRecord.publication_date || "";
}

function formatDate(value) {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return String(value).slice(0, 10);
  }
  return parsed.toLocaleDateString("nl-NL", { year: "numeric", month: "2-digit", day: "2-digit" });
}

function formatDateTime(value) {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString("nl-NL", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatBytes(bytes) {
  const numeric = Number(bytes || 0);
  if (!numeric) return "-";
  if (numeric < 1024) return `${numeric} B`;
  if (numeric < 1024 * 1024) return `${(numeric / 1024).toFixed(1)} KB`;
  return `${(numeric / (1024 * 1024)).toFixed(1)} MB`;
}

function renderMetrics() {
  const latest = state.latest || {};
  const metrics = [
    ["Gemeente", latest.municipality || latest.municipality_id || "-"],
    ["Documenten gezien", latest.documents_seen ?? state.documents.length],
    ["Genormaliseerd", latest.documents_normalized ?? state.documents.length],
    ["Gegenereerd", formatDateTime(latest.generated_at)],
  ];

  elements.metrics.innerHTML = metrics
    .map(([label, value]) => `<article class="metric-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`)
    .join("");
}

function populateTypeFilter() {
  const currentValue = elements.typeFilter.value;
  const types = [...new Set(state.documents.map((doc) => doc.document_type || doc.documentTypeLabel || "Onbekend"))].sort((a, b) => a.localeCompare(b, "nl"));
  elements.typeFilter.innerHTML = '<option value="">Alle documenttypen</option>' +
    types.map((type) => `<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`).join("");
  elements.typeFilter.value = currentValue;
}

function applyFilters() {
  const search = state.search.trim().toLowerCase();
  let filtered = [...state.documents];

  if (state.type) {
    filtered = filtered.filter((doc) => (doc.document_type || doc.documentTypeLabel || "Onbekend") === state.type);
  }

  if (search) {
    filtered = filtered.filter((doc) => {
      const haystack = [
        getTitle(doc),
        doc.filename,
        doc.document_type,
        doc.source_id,
        doc.source_object_id,
      ].join(" ").toLowerCase();
      return haystack.includes(search);
    });
  }

  filtered.sort(compareDocuments);
  state.filtered = filtered;
  state.page = Math.min(state.page, getPageCount()) || 1;
}

function compareDocuments(a, b) {
  switch (state.sort) {
    case "date_asc":
      return getDateValue(a).localeCompare(getDateValue(b));
    case "type_asc":
      return String(a.document_type || "").localeCompare(String(b.document_type || ""), "nl") || getTitle(a).localeCompare(getTitle(b), "nl");
    case "title_asc":
      return getTitle(a).localeCompare(getTitle(b), "nl");
    case "size_desc":
      return Number(b.file_size_bytes || 0) - Number(a.file_size_bytes || 0);
    case "size_asc":
      return Number(a.file_size_bytes || 0) - Number(b.file_size_bytes || 0);
    case "date_desc":
    default:
      return getDateValue(b).localeCompare(getDateValue(a));
  }
}

function getPageCount() {
  return Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
}

function getVisibleDocuments() {
  const start = (state.page - 1) * state.pageSize;
  return state.filtered.slice(start, start + state.pageSize);
}

function renderTable() {
  const visible = getVisibleDocuments();
  const pageCount = getPageCount();
  const start = state.filtered.length === 0 ? 0 : (state.page - 1) * state.pageSize + 1;
  const end = Math.min(state.page * state.pageSize, state.filtered.length);

  elements.resultSummary.textContent = `${state.filtered.length} van ${state.documents.length} documenten`;
  elements.pageSummary.textContent = state.filtered.length === 0
    ? "Geen resultaten"
    : `Toont ${start}-${end} van ${state.filtered.length} resultaten`;
  elements.pageIndicator.textContent = `Pagina ${state.page} van ${pageCount}`;
  elements.previous.disabled = state.page <= 1;
  elements.next.disabled = state.page >= pageCount;

  if (!visible.length) {
    elements.tbody.innerHTML = '<tr><td colspan="6">Geen documenten gevonden.</td></tr>';
    return;
  }

  elements.tbody.innerHTML = visible.map((doc) => {
    const title = getTitle(doc);
    const filename = doc.filename || "-";
    const type = doc.document_type || "Onbekend";
    const downloadUrl = doc.download_url || doc.source_url || "";
    const downloadCell = downloadUrl
      ? `<a href="${escapeHtml(downloadUrl)}" target="_blank" rel="noopener">PDF</a>`
      : "-";

    return `<tr>
      <td class="date-cell">${escapeHtml(formatDate(getDateValue(doc)))}</td>
      <td class="type-cell"><span class="type-badge">${escapeHtml(type)}</span></td>
      <td class="title-cell" title="${escapeHtml(title)}">${escapeHtml(title)}</td>
      <td class="filename-cell" title="${escapeHtml(filename)}">${escapeHtml(filename)}</td>
      <td class="size-cell">${escapeHtml(formatBytes(doc.file_size_bytes))}</td>
      <td class="download-cell">${downloadCell}</td>
    </tr>`;
  }).join("");
}

function render() {
  applyFilters();
  renderMetrics();
  renderTable();
}

function attachEvents() {
  elements.search.addEventListener("input", (event) => {
    state.search = event.target.value;
    state.page = 1;
    render();
  });

  elements.typeFilter.addEventListener("change", (event) => {
    state.type = event.target.value;
    state.page = 1;
    render();
  });

  elements.sort.addEventListener("change", (event) => {
    state.sort = event.target.value;
    state.page = 1;
    render();
  });

  elements.pageSize.addEventListener("change", (event) => {
    state.pageSize = Number(event.target.value);
    state.page = 1;
    render();
  });

  elements.previous.addEventListener("click", () => {
    if (state.page > 1) {
      state.page -= 1;
      renderTable();
      document.getElementById("documents-title").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  elements.next.addEventListener("click", () => {
    if (state.page < getPageCount()) {
      state.page += 1;
      renderTable();
      document.getElementById("documents-title").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  elements.reset.addEventListener("click", () => {
    state.search = "";
    state.type = "";
    state.sort = "date_desc";
    state.pageSize = 50;
    state.page = 1;
    elements.search.value = "";
    elements.typeFilter.value = "";
    elements.sort.value = "date_desc";
    elements.pageSize.value = "50";
    render();
  });

  elements.reload.addEventListener("click", loadData);
}

async function loadData() {
  elements.status.textContent = "Data wordt geladen...";
  elements.tbody.innerHTML = '<tr><td colspan="6">Documenten worden geladen...</td></tr>';

  try {
    const [latest, documents] = await Promise.all([
      fetchJson(DATA_PATHS.latest),
      fetchJsonl(DATA_PATHS.documents),
    ]);
    state.latest = latest;
    state.documents = documents;
    state.page = 1;
    populateTypeFilter();
    render();
    elements.status.textContent = `Geladen: ${documents.length} documenten.`;
  } catch (error) {
    console.error(error);
    elements.status.textContent = error.message;
    elements.tbody.innerHTML = `<tr><td colspan="6">${escapeHtml(error.message)}</td></tr>`;
  }
}

attachEvents();
loadData();
