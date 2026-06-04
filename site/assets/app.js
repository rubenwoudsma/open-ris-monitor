(() => {
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
    meetingDocumentsByMeetingId: new Map(),
    meetingItemDocumentsByMeetingItemId: new Map(),
    currentPage: 1,
    pageSize: 50,
    sortMode: "date-desc",
    pinnedDocumentKeys: null,
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
    const trimmed = String(text || "").trim();
    if (!trimmed) {
      return [];
    }

    const lines = trimmed.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (lines.length > 1) {
      try {
        return lines.map((line) => JSON.parse(line));
      } catch (error) {
        console.warn("JSONL kon niet regel voor regel worden gelezen, probeer concatenated JSON objects.", error);
      }
    }

    const records = [];
    let depth = 0;
    let inString = false;
    let escaped = false;
    let start = -1;

    for (let index = 0; index < trimmed.length; index += 1) {
      const char = trimmed[index];
      if (inString) {
        if (escaped) {
          escaped = false;
        } else if (char === "\\") {
          escaped = true;
        } else if (char === '"') {
          inString = false;
        }
        continue;
      }

      if (char === '"') {
        inString = true;
        continue;
      }
      if (char === "{") {
        if (depth === 0) start = index;
        depth += 1;
      } else if (char === "}") {
        depth -= 1;
        if (depth === 0 && start >= 0) {
          records.push(JSON.parse(trimmed.slice(start, index + 1)));
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

  function text(value) {
    return value === undefined || value === null || value === "" ? "-" : String(value);
  }

  function pick(...values) {
    for (const value of values) {
      if (value === undefined || value === null) continue;
      const asText = String(value).trim();
      if (asText) return value;
    }
    return "";
  }

  function normalizeSearchText(value) {
    return String(value || "").trim().toLowerCase();
  }

  function toId(record) {
    return String(
      pick(
        record?.id,
        record?.meeting_id,
        record?.meeting_item_id,
        record?.document_id,
        record?.source_id,
        record?.source_object_id,
      ),
    );
  }

  function normalizeDateKey(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);
    return date.toISOString().slice(0, 10);
  }

  function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);
    return new Intl.DateTimeFormat("nl-NL", { year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
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

  function addIdentifier(result, value) {
    if (value === null || value === undefined) return;
    const textValue = String(value).trim();
    if (textValue) result.add(textValue);
  }

  function getDocumentIdentifiers(documentRecord) {
    const identifiers = new Set();
    addIdentifier(identifiers, documentRecord.id);
    addIdentifier(identifiers, documentRecord.source_id);
    addIdentifier(identifiers, documentRecord.source_object_id);
    addIdentifier(identifiers, documentRecord.download_url);
    addIdentifier(identifiers, documentRecord.source_url);
    if (documentRecord.raw && typeof documentRecord.raw === "object") {
      addIdentifier(identifiers, documentRecord.raw.id);
      addIdentifier(identifiers, documentRecord.raw.objectId);
      addIdentifier(identifiers, documentRecord.raw.object_id);
      addIdentifier(identifiers, documentRecord.raw.downloadUrl);
      addIdentifier(identifiers, documentRecord.raw.download_url);
    }
    if (documentRecord.id && documentRecord.source_id && String(documentRecord.id).includes("-document-")) {
      const prefix = String(documentRecord.id).split("-document-")[0];
      addIdentifier(identifiers, `${prefix}-document-${documentRecord.source_id}`);
    }
    return [...identifiers];
  }

  function getRelationDocumentIdentifiers(relation) {
    const identifiers = new Set();
    addIdentifier(identifiers, relation.document_id);
    addIdentifier(identifiers, relation.document_source_id);
    addIdentifier(identifiers, relation.document_object_id);
    addIdentifier(identifiers, relation.document_url);
    addIdentifier(identifiers, relation.download_url);
    addIdentifier(identifiers, relation.source_url);
    if (relation.document && typeof relation.document === "object") {
      addIdentifier(identifiers, relation.document.id);
      addIdentifier(identifiers, relation.document.objectId);
      addIdentifier(identifiers, relation.document.object_id);
      addIdentifier(identifiers, relation.document.downloadUrl);
      addIdentifier(identifiers, relation.document.download_url);
    }
    return [...identifiers];
  }

  function getDocumentId(documentRecord) {
    return getDocumentIdentifiers(documentRecord)[0] || null;
  }

  function getDocumentTitle(documentRecord) {
    return documentRecord.title || documentRecord.description || documentRecord.filename || "Geen titel";
  }

  function updateUrlForSelection(selection = {}) {
    if (!window.history?.replaceState) return;
    const url = new URL(window.location.href);

    if (selection.documentId) {
      url.searchParams.set("documentId", String(selection.documentId));
    } else {
      url.searchParams.delete("documentId");
    }

    if (selection.meetingId) {
      url.searchParams.set("meetingId", String(selection.meetingId));
    } else {
      url.searchParams.delete("meetingId");
    }

    if (selection.agendaItemId) {
      url.searchParams.set("agendaItemId", String(selection.agendaItemId));
    } else {
      url.searchParams.delete("agendaItemId");
    }

    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  }

  function getDocumentSearchBlob(documentRecord) {
    const relationContext = getDocumentRelationContext(documentRecord)
      .map(({ meeting, item }) => [meeting?.description, meeting?.date, meeting?.dmu_name, item?.number, item?.title].filter(Boolean).join(" "))
      .join(" ");

    return [
      getDocumentTitle(documentRecord),
      documentRecord.description,
      documentRecord.filename,
      documentRecord.document_type,
      documentRecord.normalized_document_type,
      documentRecord.normalized_document_type_label,
      documentRecord.source_id,
      documentRecord.source_object_id,
      relationContext,
      getDocumentIdentifiers(documentRecord).join(" "),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
  }

  function addToLookupList(map, key, value) {
    if (!key) return;
    const list = map.get(key) || [];
    list.push(value);
    map.set(key, list);
  }

  function addUniqueDocumentToLookup(map, key, documentRecord) {
    if (!key || !documentRecord) return;
    const list = map.get(key) || [];
    const documentKeyValue = getDocumentId(documentRecord) || getDocumentTitle(documentRecord);
    if (list.some((existing) => (getDocumentId(existing) || getDocumentTitle(existing)) === documentKeyValue)) {
      return;
    }
    list.push(documentRecord);
    map.set(key, list);
  }

  function getDocumentsForMeeting(meetingId) {
    const meeting = state.meetingsById.get(String(meetingId || "").trim());
    if (!meeting) return [];
    const documents = [...(state.meetingDocumentsByMeetingId.get(meeting.id) || [])];
    for (const item of meeting.items || []) {
      for (const doc of state.meetingItemDocumentsByMeetingItemId.get(item.id) || []) {
        addUniqueDocumentToLookup(new Map([["docs", documents]]), "docs", doc);
      }
    }
    return documents;
  }

  function getDocumentsForMeetingItem(meetingItemId) {
    return [...(state.meetingItemDocumentsByMeetingItemId.get(String(meetingItemId || "").trim()) || [])];
  }

  function focusDocuments(documentRecords, options = {}) {
    const records = Array.isArray(documentRecords) ? documentRecords.filter(Boolean) : [];
    const identifiers = new Set();

    if (records.length === 0) {
      identifiers.add("__no_documents__");
    } else {
      for (const documentRecord of records) {
        for (const identifier of getDocumentIdentifiers(documentRecord)) {
          addIdentifier(identifiers, identifier);
        }
        addIdentifier(identifiers, getDocumentTitle(documentRecord));
        addIdentifier(identifiers, documentRecord.filename);
      }
    }

    state.pinnedDocumentKeys = identifiers;
    if (options.query === false) {
      elements.searchInput.value = "";
    } else {
      elements.searchInput.value = options.searchText || (records[0] ? getDocumentTitle(records[0]) : "");
    }
    updateUrlForSelection({
      documentId: options.documentId,
      meetingId: options.meetingId,
      agendaItemId: options.agendaItemId,
    });
    state.currentPage = 1;
    applyFilters();
    document.querySelector("#documents-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function focusMeetingById(meetingId, options = {}) {
    const meeting = state.meetingsById.get(String(meetingId || "").trim());
    if (!meeting) return;
    const documents = getDocumentsForMeeting(meeting.id);
    focusDocuments(documents, {
      meetingId: meeting.id,
      query: false,
    });
  }

  function focusMeetingItemById(meetingItemId, options = {}) {
    const item = state.meetingItemsById.get(String(meetingItemId || "").trim());
    if (!item) return;
    const documents = getDocumentsForMeetingItem(item.id);
    const meeting = state.meetingsById.get(String(item.meeting_id || item.meetingId || "").trim());
    focusDocuments(documents, {
      meetingId: meeting?.id,
      agendaItemId: item.id,
      query: false,
    });
  }

  function buildRelationLookups() {
    state.meetingsById = new Map(state.meetings.map((meeting) => [meeting.id, meeting]));
    state.meetingItemsById = new Map(state.meetingItems.map((item) => [item.id, item]));
    state.meetingRelationsByDocumentId = new Map();
    state.meetingItemRelationsByDocumentId = new Map();
    state.meetingDocumentsByMeetingId = new Map();
    state.meetingItemDocumentsByMeetingItemId = new Map();

    for (const meeting of state.meetings) {
      meeting.items = [];
    }
    for (const item of state.meetingItems) {
      const meetingId = String(pick(item.meeting_id, item.meetingId, item.session_id, item.sessionId)).trim();
      const meeting = state.meetingsById.get(meetingId);
      if (meeting) {
        meeting.items.push(item);
      }
    }

    const documentsById = new Map();
    for (const documentRecord of state.documents) {
      for (const identifier of getDocumentIdentifiers(documentRecord)) {
        documentsById.set(identifier, documentRecord);
      }
    }

    const resolveDocument = (relation) => {
      const identifiers = getRelationDocumentIdentifiers(relation);
      for (const identifier of identifiers) {
        const documentRecord = documentsById.get(identifier);
        if (documentRecord) return documentRecord;
      }
      return null;
    };

    for (const relation of state.meetingDocumentRelations) {
      for (const identifier of getRelationDocumentIdentifiers(relation)) {
        addToLookupList(state.meetingRelationsByDocumentId, identifier, relation);
      }
      const meetingId = String(pick(relation.meeting_id, relation.meetingId)).trim();
      const documentRecord = resolveDocument(relation);
      if (meetingId && documentRecord) {
        addUniqueDocumentToLookup(state.meetingDocumentsByMeetingId, meetingId, documentRecord);
      }
    }

    for (const relation of state.meetingItemDocumentRelations) {
      for (const identifier of getRelationDocumentIdentifiers(relation)) {
        addToLookupList(state.meetingItemRelationsByDocumentId, identifier, relation);
      }
      const itemId = String(pick(relation.meeting_item_id, relation.meetingItemId, relation.item_id)).trim();
      const meetingId = String(pick(relation.meeting_id, relation.meetingId)).trim();
      const documentRecord = resolveDocument(relation);
      if (itemId && documentRecord) {
        addUniqueDocumentToLookup(state.meetingItemDocumentsByMeetingItemId, itemId, documentRecord);
      }
      if (meetingId && documentRecord) {
        addUniqueDocumentToLookup(state.meetingDocumentsByMeetingId, meetingId, documentRecord);
      }
      if (!meetingId && itemId && documentRecord) {
        const item = state.meetingItemsById.get(itemId);
        const resolvedMeetingId = item ? String(pick(item.meeting_id, item.meetingId, item.session_id, item.sessionId)).trim() : "";
        if (resolvedMeetingId) {
          addUniqueDocumentToLookup(state.meetingDocumentsByMeetingId, resolvedMeetingId, documentRecord);
        }
      }
    }
  }

  function getLookupRelations(map, identifiers) {
    const relations = [];
    const seen = new Set();
    for (const identifier of identifiers) {
      for (const relation of map.get(identifier) || []) {
        const key = relation.id || `${relation.meeting_id}:${relation.meeting_item_id || ""}:${relation.document_id || identifier}`;
        if (seen.has(key)) continue;
        seen.add(key);
        relations.push(relation);
      }
    }
    return relations;
  }

  function getDocumentRelationContext(documentRecord) {
    const documentIds = getDocumentIdentifiers(documentRecord);
    if (documentIds.length === 0) return [];

    const contexts = [];
    const seen = new Set();

    const itemRelations = getLookupRelations(state.meetingItemRelationsByDocumentId, documentIds);
    for (const relation of itemRelations) {
      const meeting = state.meetingsById.get(relation.meeting_id);
      const item = state.meetingItemsById.get(relation.meeting_item_id);
      const key = `item:${relation.meeting_item_id}:${relation.document_id}`;
      if (seen.has(key)) continue;
      seen.add(key);
      contexts.push({ meeting, item });
    }

    const meetingRelations = getLookupRelations(state.meetingRelationsByDocumentId, documentIds);
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
        return `\n* ${meetingLabel}${itemText}\n`;
      })
      .join("");
    const extraHtml = extraCount > 0 ? `\n* + ${extraCount} extra koppeling(en)\n` : "";
    return `\n${rows}${extraHtml}`;
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

      const meetingButton = document.createElement("button");
      meetingButton.type = "button";
      meetingButton.className = "relation-link";
      meetingButton.textContent = meetingLabel;
      meetingButton.title = "Toon documenten van deze vergadering";
      meetingButton.addEventListener("click", () => {
        if (meeting?.id && window.OpenRisMonitor?.focusMeetingById) {
          window.OpenRisMonitor.focusMeetingById(meeting.id, { query: false });
        }
      });
      listItem.appendChild(meetingButton);

      if (item) {
        const separator = document.createTextNode(" • ");
        listItem.appendChild(separator);

        const itemButton = document.createElement("button");
        itemButton.type = "button";
        itemButton.className = "relation-link";
        itemButton.textContent = itemLabel || "Agendapunt";
        itemButton.title = "Toon documenten van dit agendapunt";
        itemButton.addEventListener("click", () => {
          if (item?.id && window.OpenRisMonitor?.focusMeetingItemById) {
            window.OpenRisMonitor.focusMeetingItemById(item.id, { query: false });
          }
        });
        listItem.appendChild(itemButton);
      }

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

  function renderSummary() {
    const latest = state.latest || {};
    elements.municipality.textContent = latest.municipality || latest.municipality_id || "-";
    elements.documentsSeen.textContent = latest.documents_seen ?? "-";
    elements.documentsNormalized.textContent = latest.documents_normalized ?? "-";
    elements.generatedAt.textContent = formatDateTime(latest.generated_at);

    const documentsWithRelations = state.documents.filter((documentRecord) => getDocumentRelationContext(documentRecord).length > 0).length;
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

    elements.typeFilter.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Alle compacte documenttypen";
    elements.typeFilter.appendChild(placeholder);

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

  function getPinnedDocumentIdentifiers() {
    return state.pinnedDocumentKeys ? new Set([...state.pinnedDocumentKeys].map((value) => normalizeSearchText(value))) : null;
  }

  function documentMatchesPinnedFilter(documentRecord) {
    const pinned = getPinnedDocumentIdentifiers();
    if (!pinned || pinned.size === 0) return true;
    const identifiers = getDocumentIdentifiers(documentRecord).map((value) => normalizeSearchText(value));
    const title = normalizeSearchText(getDocumentTitle(documentRecord));
    const filename = normalizeSearchText(documentRecord.filename);
    return [...identifiers, title, filename].some((value) => pinned.has(value));
  }

  function applyFilters() {
    const query = normalizeSearchText(elements.searchInput.value);
    const type = elements.typeFilter.value;

    state.filteredDocuments = state.documents.filter((documentRecord) => {
      const matchesType = !type || getCompactType(documentRecord) === type;
      const matchesPinned = documentMatchesPinnedFilter(documentRecord);
      const haystack = getDocumentSearchBlob(documentRecord);
      const matchesQuery = !query || haystack.includes(query);
      return matchesType && matchesPinned && matchesQuery;
    });

    state.currentPage = 1;
    renderDocuments();
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
      if (relationContext) {
        titleCell.appendChild(relationContext);
      }

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

  function changePage(delta) {
    state.currentPage += delta;
    renderDocuments();
  }

  function clearDocumentFocus() {
    state.pinnedDocumentKeys = null;
  }

  function focusDocument(documentRecord, options = {}) {
    if (!documentRecord) return;
    focusDocuments([documentRecord], {
      searchText: options.searchText || getDocumentTitle(documentRecord),
      documentId: getDocumentId(documentRecord),
      meetingId: options.meetingId,
      agendaItemId: options.agendaItemId,
      query: options.query,
    });
  }

  function focusDocumentById(documentId) {
    if (!documentId) return;
    const normalizedId = String(documentId).trim();
    const directMatch = state.documents.find((documentRecord) => getDocumentIdentifiers(documentRecord).some((identifier) => String(identifier).trim() === normalizedId));
    if (directMatch) {
      focusDocument(directMatch, { query: false });
      return;
    }
    state.pinnedDocumentKeys = new Set([normalizeSearchText(normalizedId)]);
    elements.searchInput.value = normalizedId;
    state.currentPage = 1;
    applyFilters();
    document.querySelector("#documents-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function focusDocumentByText(textValue) {
    const query = String(textValue || "").trim();
    if (!query) return;
    clearDocumentFocus();
    elements.searchInput.value = query;
    state.currentPage = 1;
    applyFilters();
    document.querySelector("#documents-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
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

  function bindEvents() {
    elements.searchInput.addEventListener("input", () => {
      clearDocumentFocus();
      applyFilters();
    });
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

  function readInitialNavigationTarget() {
    const params = new URLSearchParams(window.location.search);
    return {
      documentId: params.get("documentId") || params.get("document_id") || params.get("q") || "",
      meetingId: params.get("meetingId") || "",
      agendaItemId: params.get("agendaItemId") || "",
    };
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
      bindEvents();
      state.sortMode = elements.sortSelect.value;
      state.pageSize = Number(elements.pageSizeSelect.value);
      renderDocuments();

      const initialTarget = readInitialNavigationTarget();
      if (initialTarget.documentId) {
        focusDocumentById(initialTarget.documentId);
      } else if (initialTarget.agendaItemId) {
        focusMeetingItemById(initialTarget.agendaItemId);
      } else if (initialTarget.meetingId) {
        focusMeetingById(initialTarget.meetingId);
      }
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

  window.OpenRisMonitor = {
    focusDocument,
    focusDocumentById,
    focusDocumentByText,
    focusDocuments,
    focusMeetingById,
    focusMeetingItemById,
    clearDocumentFocus,
    applyDocumentFilters: applyFilters,
    getDocumentById(documentId) {
      const normalizedId = String(documentId || "").trim();
      return state.documents.find((documentRecord) => getDocumentIdentifiers(documentRecord).some((identifier) => String(identifier).trim() === normalizedId)) || null;
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
