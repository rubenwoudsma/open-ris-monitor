const DATA_BASE = "../data/public";

const state = {
  latest: null,
  documents: [],
  filteredDocuments: [],
};

const elements = {
  statusMessage: document.querySelector("#status-message"),
  municipality: document.querySelector("#municipality"),
  documentsSeen: document.querySelector("#documents-seen"),
  documentsNormalized: document.querySelector("#documents-normalized"),
  generatedAt: document.querySelector("#generated-at"),
  searchInput: document.querySelector("#search-input"),
  typeFilter: document.querySelector("#type-filter"),
  resultCount: document.querySelector("#result-count"),
  tableBody: document.querySelector("#documents-table-body"),
};

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

function renderSummary() {
  const latest = state.latest;
  elements.municipality.textContent = latest.municipality || latest.municipality_id || "-";
  elements.documentsSeen.textContent = latest.documents_seen ?? "-";
  elements.documentsNormalized.textContent = latest.documents_normalized ?? "-";
  elements.generatedAt.textContent = formatDateTime(latest.generated_at);
  elements.statusMessage.textContent = `Harvest ${latest.harvest_run_id || "onbekend"} is geladen.`;
}

function renderTypeFilter() {
  const types = [...new Set(state.documents.map((item) => item.document_type).filter(Boolean))].sort();
  for (const type of types) {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    elements.typeFilter.appendChild(option);
  }
}

function applyFilters() {
  const query = elements.searchInput.value.trim().toLowerCase();
  const type = elements.typeFilter.value;

  state.filteredDocuments = state.documents.filter((documentRecord) => {
    const matchesType = !type || documentRecord.document_type === type;
    const haystack = [
      documentRecord.title,
      documentRecord.description,
      documentRecord.filename,
      documentRecord.document_type,
      documentRecord.source_id,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const matchesQuery = !query || haystack.includes(query);
    return matchesType && matchesQuery;
  });

  renderDocuments();
}

function renderDocuments() {
  elements.resultCount.textContent = `${state.filteredDocuments.length} van ${state.documents.length} documenten`;

  if (state.filteredDocuments.length === 0) {
    elements.tableBody.innerHTML = '<tr><td colspan="6">Geen documenten gevonden.</td></tr>';
    return;
  }

  const rows = state.filteredDocuments
    .slice()
    .sort((a, b) => String(getDocumentDate(b)).localeCompare(String(getDocumentDate(a))))
    .map((documentRecord) => {
      const downloadUrl = documentRecord.download_url || documentRecord.source_url;
      const downloadLink = downloadUrl
        ? `<a href="${escapeHtml(downloadUrl)}" target="_blank" rel="noopener">PDF</a>`
        : "-";

      return `
        <tr>
          <td>${escapeHtml(formatDate(getDocumentDate(documentRecord)))}</td>
          <td><span class="tag">${escapeHtml(documentRecord.document_type || "Onbekend")}</span></td>
          <td>${escapeHtml(documentRecord.title || documentRecord.description || "Geen titel")}</td>
          <td>${escapeHtml(documentRecord.filename || "-")}</td>
          <td>${escapeHtml(formatBytes(documentRecord.file_size_bytes))}</td>
          <td>${downloadLink}</td>
        </tr>
      `;
    })
    .join("");

  elements.tableBody.innerHTML = rows;
}

async function init() {
  try {
    state.latest = await fetchJson(`${DATA_BASE}/latest.json`);
    const documentsPath = state.latest.outputs?.documents || "documents.jsonl";
    state.documents = await fetchJsonl(`${DATA_BASE}/${documentsPath}`);
    state.filteredDocuments = state.documents;

    renderSummary();
    renderTypeFilter();
    renderDocuments();

    elements.searchInput.addEventListener("input", applyFilters);
    elements.typeFilter.addEventListener("change", applyFilters);
  } catch (error) {
    console.error(error);
    elements.statusMessage.textContent = "De publieke data kon niet worden geladen.";
    elements.tableBody.innerHTML = `<tr><td colspan="6">${escapeHtml(error.message)}</td></tr>`;
  }
}

init();
