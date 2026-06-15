import { loadPublicData } from "./data/loaders.js";
import { buildRelationIndexes, getDocumentIdentifiers, getRecordId } from "./data/relations.js";
import { formatBytes, formatDate, formatDateTime, pick, safeUrl, text, timestamp } from "./ui/format.js";
const state = {
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
    activeView: "documents",
};
function byId(id) {
    const element = document.getElementById(id);
    if (!element)
        throw new Error(`HTML mist verwacht element: #${id}`);
    return element;
}
const elements = {
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
    visibleMeetingsCount: byId("visible-meetings-count"),
    meetingsResultCount: byId("meetings-result-count"),
    meetingsTableBody: byId("meetings-table-body"),
    meetingDetail: byId("meeting-detail"),
    meetingDetailTitle: byId("meeting-detail-title"),
    meetingDetailBody: byId("meeting-detail-body"),
    clearMeetingSelection: byId("clear-meeting-selection"),
};
function unavailable(reason = "Niet beschikbaar in export") {
    return reason;
}
function uniqueValues(values) {
    return [...new Set(values.filter(Boolean))];
}
function getDocumentId(documentRecord) {
    return getDocumentIdentifiers(documentRecord)[0] ?? "";
}
function documentIds(documentRecord) {
    return uniqueValues(getDocumentIdentifiers(documentRecord));
}
function getDocumentTitle(documentRecord) {
    return pick(documentRecord.title, documentRecord.description, documentRecord.filename) || "Geen titel";
}
function getDocumentDate(documentRecord) {
    return pick(documentRecord.publication_datetime, documentRecord.date_published, documentRecord.publication_date, documentRecord.document_date, documentRecord.date, documentRecord.retrieved_at);
}
function getMeetingId(meeting) {
    return getRecordId(meeting) || pick(meeting.id, meeting.source_id, meeting.source_object_id);
}
function getMeetingTitle(meeting) {
    return pick(meeting?.description, meeting?.title, meeting?.dmu_name) || "Vergadering zonder titel";
}
function getMeetingDate(meeting) {
    return pick(meeting?.date, meeting?.start_time);
}
function getAgendaItemId(item) {
    return getRecordId(item) || pick(item.id, item.meeting_item_id, item.source_id, item.source_object_id);
}
function getAgendaItemTitle(item) {
    const number = pick(item?.number);
    const title = pick(item?.title, item?.description) || "Agendapunt zonder titel";
    return number ? `${number}. ${title}` : title;
}
function getAgendaItemMeetingId(item) {
    return pick(item?.meeting_id, item?.meetingId, item?.session_id, item?.sessionId);
}
function isUnknownType(value) {
    const normalized = value.trim().toLowerCase();
    return !normalized || normalized === "unknown" || normalized === "onbekend";
}
function pickFromRaw(record, ...keys) {
    if (!record.raw || typeof record.raw !== "object")
        return "";
    for (const key of keys) {
        const picked = pick(record.raw[key]);
        if (picked)
            return picked;
    }
    return "";
}
function pickNestedRaw(record, objectKey, ...keys) {
    const nested = record.raw?.[objectKey];
    if (!nested || typeof nested !== "object")
        return "";
    const nestedRecord = nested;
    for (const key of keys) {
        const picked = pick(nestedRecord[key]);
        if (picked)
            return picked;
    }
    return "";
}
function getCompactType(documentRecord) {
    const normalized = pick(documentRecord.normalized_document_type, documentRecord.type);
    if (!isUnknownType(normalized))
        return normalized;
    return "unknown";
}
function getCompactTypeLabel(documentRecord) {
    const normalizedLabel = pick(documentRecord.normalized_document_type_label);
    if (!isUnknownType(normalizedLabel))
        return normalizedLabel;
    const normalizedType = pick(documentRecord.normalized_document_type, documentRecord.type);
    if (!isUnknownType(normalizedType))
        return normalizedType;
    return unavailable();
}
function getSourceDocumentType(documentRecord) {
    const sourceType = pick(documentRecord.document_type, pickFromRaw(documentRecord, "document_type", "documentType", "source_document_type", "sourceDocumentType"));
    const compactType = getCompactType(documentRecord);
    const compactTypeLabel = getCompactTypeLabel(documentRecord);
    let documentTypeLabel = sourceType;
    if (sourceType === compactType || sourceType === compactTypeLabel) {
        documentTypeLabel = sourceType;
    }
    return documentTypeLabel || unavailable("Geen bronmetadata");
}
function getDocumentFilename(documentRecord) {
    return pick(documentRecord.filename, documentRecord.file_name, documentRecord.name, documentRecord.display_name, documentRecord.original_filename, pickFromRaw(documentRecord, "filename", "file_name", "fileName", "name", "displayName", "originalFilename"), pickNestedRaw(documentRecord, "file", "filename", "fileName", "name"));
}
function getDocumentSize(documentRecord) {
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
function formatDocumentSize(documentRecord) {
    const formatted = formatBytes(getDocumentSize(documentRecord));
    return formatted === "-" ? unavailable("Geen bestandsgrootte beschikbaar") : formatted;
}
function getDocumentUrl(documentRecord) {
    return safeUrl(pick(documentRecord.download_url, documentRecord.source_url, documentRecord.url, documentRecord.file_url, documentRecord.document_url, documentRecord.web_url, documentRecord.external_url, pickFromRaw(documentRecord, "download_url", "downloadUrl", "source_url", "sourceUrl", "url", "fileUrl", "documentUrl", "webUrl"), pickNestedRaw(documentRecord, "file", "url", "downloadUrl", "download_url", "href")));
}
function relatedMeetingIds(documentRecord) {
    if (!state.indexes)
        return [];
    return uniqueValues(documentIds(documentRecord).flatMap((id) => state.indexes?.meetingIdsByDocumentId.get(id) ?? []));
}
function relatedAgendaItemIds(documentRecord) {
    if (!state.indexes)
        return [];
    return uniqueValues(documentIds(documentRecord).flatMap((id) => state.indexes?.agendaItemIdsByDocumentId.get(id) ?? []));
}
function relationLabelsForDocument(documentRecord) {
    if (!state.indexes)
        return [];
    const labels = [];
    for (const meetingId of relatedMeetingIds(documentRecord)) {
        const meeting = state.indexes.meetingsById.get(meetingId);
        labels.push([getMeetingTitle(meeting), formatDate(getMeetingDate(meeting))].filter(Boolean).join(", "));
    }
    for (const itemId of relatedAgendaItemIds(documentRecord)) {
        const item = state.indexes.agendaItemsById.get(itemId);
        labels.push(getAgendaItemTitle(item));
    }
    return uniqueValues(labels);
}
function relatedVersions(documentRecord) {
    const ids = new Set(documentIds(documentRecord));
    return (state.data?.documentVersions ?? []).filter((version) => {
        const versionDocumentId = pick(version.document_id, version.source_id);
        return versionDocumentId ? ids.has(versionDocumentId) : false;
    });
}
function agendaItemIdsForMeeting(meetingId) {
    if (!state.indexes)
        return [];
    return uniqueValues(state.indexes.agendaItemIdsByMeetingId.get(meetingId) ?? []);
}
function linkedDocumentIdsForMeeting(meetingId) {
    if (!state.indexes)
        return [];
    return uniqueValues(state.indexes.documentIdsByMeetingId.get(meetingId) ?? []);
}
function linkedDocumentIdsForAgendaItem(itemId) {
    if (!state.indexes)
        return [];
    return uniqueValues(state.indexes.documentIdsByAgendaItemId.get(itemId) ?? []);
}
function findDocumentById(documentId) {
    if (!documentId)
        return undefined;
    return state.indexes?.documentsById.get(documentId) ?? state.data?.documents.find((documentRecord) => documentIds(documentRecord).includes(documentId));
}
function primaryDocumentHashId(documentRecord) {
    return getDocumentId(documentRecord) || documentIds(documentRecord)[0] || "";
}
function documentHashFor(documentRecord) {
    const documentId = primaryDocumentHashId(documentRecord);
    return documentId ? `#documents/${encodeURIComponent(documentId)}` : "#documents";
}
function documentIdFromHash() {
    const prefix = "#documents/";
    if (!window.location.hash.startsWith(prefix))
        return "";
    return decodeURIComponent(window.location.hash.slice(prefix.length));
}
function updateHash(nextHash) {
    if (window.location.hash !== nextHash)
        history.pushState(null, "", nextHash);
}
function findMeetingById(meetingId) {
    if (!meetingId)
        return undefined;
    return state.data?.meetings.find((meeting) => getMeetingId(meeting) === meetingId) ?? state.indexes?.meetingsById.get(meetingId);
}
function createCell(value) {
    const cell = document.createElement("td");
    cell.textContent = value;
    return cell;
}
function appendDefinition(list, label, value) {
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = label;
    description.textContent = value;
    wrapper.append(term, description);
    list.appendChild(wrapper);
}
function createDocumentAction(documentRecord, label = "Details", fromMeetingDetail = false) {
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
function ensureDocumentVisible(documentRecord) {
    const documentId = primaryDocumentHashId(documentRecord);
    let index = state.filteredDocuments.findIndex((record) => documentIds(record).includes(documentId));
    if (index < 0) {
        elements.searchInput.value = "";
        elements.typeFilter.value = "";
        state.currentPage = 1;
        applyFilters();
        index = state.filteredDocuments.findIndex((record) => documentIds(record).includes(documentId));
    }
    if (index >= 0)
        state.currentPage = Math.floor(index / state.pageSize) + 1;
}
function focusDocumentFromDocumentList(documentRecord) {
    updateHash(documentHashFor(documentRecord));
    ensureDocumentVisible(documentRecord);
    selectDocument(documentRecord, true);
}
function focusDocumentFromMeetingDetail(documentRecord) {
    setActiveView("documents", false, false);
    updateHash(documentHashFor(documentRecord));
    ensureDocumentVisible(documentRecord);
    selectDocument(documentRecord, true);
}
function createInlineDocumentLinks(documentIdsToRender, emptyLabel) {
    const wrapper = document.createElement("div");
    wrapper.className = "inline-document-links";
    const documents = uniqueValues(documentIdsToRender)
        .map((id) => findDocumentById(id))
        .filter((record) => Boolean(record));
    if (documents.length === 0)
        return renderEmptyRelation(emptyLabel);
    for (const documentRecord of documents) {
        const button = createDocumentAction(documentRecord, getDocumentTitle(documentRecord), true);
        button.classList.add("compact-document-link");
        wrapper.appendChild(button);
    }
    return wrapper;
}
function createMeetingDocumentsTable(documentIdsToRender, emptyLabel) {
    const documents = uniqueValues(documentIdsToRender)
        .map((id) => findDocumentById(id))
        .filter((record) => Boolean(record));
    if (documents.length === 0)
        return renderEmptyRelation(emptyLabel);
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
function createAgendaItemsTable(agendaIds) {
    if (agendaIds.length === 0)
        return renderEmptyRelation("Geen agendapunten gevonden in meeting_items.jsonl voor deze vergadering.");
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
function createDocumentList(documentIdsToRender, emptyLabel) {
    const list = document.createElement("div");
    list.className = "linked-document-list";
    const documents = uniqueValues(documentIdsToRender)
        .map((id) => findDocumentById(id))
        .filter((record) => Boolean(record));
    if (documents.length === 0)
        return renderEmptyRelation(emptyLabel);
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
function createRelationCard(title, meta, body) {
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
function renderEmptyRelation(label) {
    const paragraph = document.createElement("p");
    paragraph.className = "empty-state";
    paragraph.textContent = label;
    return paragraph;
}
function appendSectionHeading(section, label) {
    const heading = document.createElement("h3");
    heading.textContent = label;
    section.appendChild(heading);
}
function renderSummary() {
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
    const notices = [];
    if (documents.length > 0 && linkedDocumentCount === 0 && relationCount > 0) {
        notices.push(`${relationCount} relationele records geladen, maar Geen bruikbare documentkoppelingen in deze export.`);
    }
    if (documents.length > 0 && unknownTypeCount === documents.length)
        notices.push("Alle documenten hebben nog een onbekend genormaliseerd documenttype.");
    elements.dataQualityNotice.textContent = notices.join(" ");
    elements.dataQualityNotice.hidden = notices.length === 0;
    const relationText = latest.relations_enabled
        ? ` Relationele context: ${latest.relations_summary?.meetings_seen ?? 0} vergaderingen, ${latest.relations_summary?.meeting_items_seen ?? 0} agendapunten. ${linkedDocumentCount} documenten hebben een koppeling.`
        : "";
    elements.statusMessage.textContent = `${state.data?.documents.length ?? 0} documenten geladen.${relationText}`;
}
function populateTypeFilter() {
    const options = new Map();
    for (const documentRecord of state.data?.documents ?? [])
        options.set(getCompactType(documentRecord), getCompactTypeLabel(documentRecord));
    for (const [value, label] of [...options.entries()].sort((a, b) => a[1].localeCompare(b[1], "nl"))) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        elements.typeFilter.appendChild(option);
    }
}
function searchBlob(documentRecord) {
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
    ].filter(Boolean).join(" ").toLowerCase();
}
function sortDocuments(records) {
    const sorted = [...records];
    const byTitle = (a, b) => getDocumentTitle(a).localeCompare(getDocumentTitle(b), "nl");
    const byType = (a, b) => getCompactTypeLabel(a).localeCompare(getCompactTypeLabel(b), "nl");
    const bySize = (a, b) => Number(getDocumentSize(a) ?? 0) - Number(getDocumentSize(b) ?? 0);
    const byDate = (a, b) => timestamp(getDocumentDate(a)) - timestamp(getDocumentDate(b));
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
function applyFilters() {
    const query = elements.searchInput.value.trim().toLowerCase();
    const type = elements.typeFilter.value;
    let records = (state.data?.documents ?? []).filter((documentRecord) => {
        if (type && getCompactType(documentRecord) !== type)
            return false;
        if (query && !searchBlob(documentRecord).includes(query))
            return false;
        return true;
    });
    records = sortDocuments(records);
    state.filteredDocuments = records;
    renderDocuments();
}
function hasAnyDocumentFilenameMetadata(records) {
    return records.some((record) => Boolean(getDocumentFilename(record)));
}
function hasAnyDocumentSizeMetadata(records) {
    return records.some((record) => Boolean(getDocumentSize(record)));
}
function getVisibleDocumentColumnCount(showFilenameColumn, showSizeColumn) {
    return 4 + Number(showFilenameColumn) + Number(showSizeColumn);
}
function setColumnVisibilityForTable(tableSelector, headerLabel, visible) {
    const table = document.querySelector(tableSelector);
    const headers = Array.from(table?.querySelectorAll("thead th") ?? []);
    const header = headers.find((cell) => cell.textContent?.trim() === headerLabel);
    if (header)
        header.hidden = !visible;
}
function setTableColumnVisibility(headerLabel, visible) {
    setColumnVisibilityForTable(".documents-table", headerLabel, visible);
}
function createDocumentTitleCell(documentRecord) {
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
function createDocumentActionsCell(documentRecord) {
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
function renderDocuments() {
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
        if (state.selectedDocumentId && documentIds(documentRecord).includes(state.selectedDocumentId))
            row.className = "is-selected";
        row.appendChild(createCell(formatDate(getDocumentDate(documentRecord))));
        row.appendChild(createCell(getCompactTypeLabel(documentRecord)));
        row.appendChild(createDocumentTitleCell(documentRecord));
        if (showFilenameColumn)
            row.appendChild(createCell(text(getDocumentFilename(documentRecord), unavailable("Geen bestandsmetadata"))));
        if (showSizeColumn)
            row.appendChild(createCell(formatDocumentSize(documentRecord)));
        row.appendChild(createDocumentActionsCell(documentRecord));
        row.dataset.documentId = documentId;
        elements.tableBody.appendChild(row);
    }
    const pageText = `Pagina ${state.currentPage} van ${totalPages}`;
    elements.pageInfoTop.textContent = pageText;
    elements.pageInfoBottom.textContent = pageText;
    for (const button of [elements.previousTop, elements.previousBottom])
        button.disabled = state.currentPage <= 1;
    for (const button of [elements.nextTop, elements.nextBottom])
        button.disabled = state.currentPage >= totalPages;
}
function renderDocumentDetail(documentRecord) {
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
    if (filename)
        appendDefinition(meta, "Bestand", filename);
    const size = formatDocumentSize(documentRecord);
    if (size !== "Geen bestandsgrootte beschikbaar")
        appendDefinition(meta, "Grootte", size);
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
    }
    else {
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
    if (meetingIds.length === 0)
        meetingsSection.appendChild(renderEmptyRelation("Geen gekoppelde vergadering gevonden in de huidige public export."));
    for (const meetingId of meetingIds) {
        const meeting = state.indexes?.meetingsById.get(meetingId);
        const card = createRelationCard(getMeetingTitle(meeting), [formatDate(getMeetingDate(meeting)), pick(meeting?.dmu_name), meetingId].filter(Boolean).join(" · ") || "Vergadering", text(meeting?.description, ""));
        meetingsSection.appendChild(card);
    }
    relations.appendChild(meetingsSection);
    const agendaSection = document.createElement("section");
    agendaSection.className = "detail-section";
    appendSectionHeading(agendaSection, "Gekoppelde agendapunten");
    if (itemIds.length === 0)
        agendaSection.appendChild(renderEmptyRelation("Geen gekoppeld agendapunt gevonden in de huidige public export."));
    for (const itemId of itemIds) {
        const item = state.indexes?.agendaItemsById.get(itemId);
        const meeting = state.indexes?.meetingsById.get(getAgendaItemMeetingId(item));
        agendaSection.appendChild(createRelationCard(getAgendaItemTitle(item), [getMeetingTitle(meeting), itemId].filter(Boolean).join(" · ") || "Agendapunt", text(item?.description, "")));
    }
    relations.appendChild(agendaSection);
    const versionsSection = document.createElement("section");
    versionsSection.className = "detail-section";
    appendSectionHeading(versionsSection, "Versies");
    if (versions.length === 0)
        versionsSection.appendChild(renderEmptyRelation("Geen aparte versiehistorie gevonden."));
    for (const version of versions.slice(0, 10)) {
        versionsSection.appendChild(createRelationCard("Documentversie", [formatDateTime(version.retrieved_at), pick(version.id, version.source_id)].filter(Boolean).join(" · ") || "Versie", ""));
    }
    relations.appendChild(versionsSection);
    elements.documentDetailBody.appendChild(relations);
}
function selectDocument(documentRecord, scroll = true) {
    state.selectedDocumentId = getDocumentId(documentRecord) || null;
    renderDocumentDetail(documentRecord);
    renderDocuments();
    if (scroll)
        elements.documentDetail.scrollIntoView({ block: "start", behavior: "smooth" });
}
function clearDocumentSelection() {
    state.selectedDocumentId = null;
    elements.documentDetail.hidden = true;
    elements.documentDetailTitle.textContent = "Documentdetails";
    elements.documentDetailBody.replaceChildren();
    renderDocuments();
}
function meetingSearchBlob(meeting) {
    const meetingId = getMeetingId(meeting);
    const agendaText = agendaItemIdsForMeeting(meetingId)
        .map((itemId) => state.indexes?.agendaItemsById.get(itemId))
        .map((item) => [getAgendaItemTitle(item), item?.description, item?.number].filter(Boolean).join(" "))
        .join(" ");
    return [
        getMeetingTitle(meeting),
        getMeetingDate(meeting),
        formatDate(getMeetingDate(meeting)),
        meeting.description,
        meeting.dmu_name,
        meeting.location,
        meetingId,
        agendaText,
    ].filter(Boolean).join(" ").toLowerCase();
}
function filteredMeetings() {
    const query = state.meetingQuery.trim().toLowerCase();
    const meetings = (state.data?.meetings ?? []).filter((meeting) => {
        if (!query)
            return true;
        return meetingSearchBlob(meeting).includes(query);
    });
    const byDate = (a, b) => timestamp(getMeetingDate(a)) - timestamp(getMeetingDate(b));
    return [...meetings].sort((a, b) => state.meetingSortMode === "date-asc" ? byDate(a, b) : byDate(b, a));
}
function renderMeetings() {
    const meetings = filteredMeetings();
    elements.visibleMeetingsCount.textContent = `${meetings.length} zichtbaar`;
    elements.meetingsResultCount.textContent = `${meetings.length} vergadering(en)`;
    elements.meetingsTableBody.replaceChildren();
    if (meetings.length === 0) {
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
    for (const meeting of meetings) {
        const meetingId = getMeetingId(meeting);
        const agendaIds = agendaItemIdsForMeeting(meetingId);
        const documentIdsForMeeting = linkedDocumentIdsForMeeting(meetingId);
        const row = document.createElement("tr");
        if (state.selectedMeetingId === meetingId)
            row.className = "is-selected";
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
function renderMeetingDetail(meeting) {
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
function selectMeeting(meeting, scroll = true) {
    state.selectedMeetingId = getMeetingId(meeting) || null;
    renderMeetingDetail(meeting);
    renderMeetings();
    if (scroll)
        elements.meetingDetail.scrollIntoView({ block: "start", behavior: "smooth" });
}
function clearMeetingSelection() {
    state.selectedMeetingId = null;
    elements.meetingDetail.hidden = true;
    elements.meetingDetailTitle.textContent = "Vergaderdetails";
    elements.meetingDetailBody.replaceChildren();
    renderMeetings();
}
function setActiveView(view, updateHash = false, scrollToView = false) {
    state.activeView = view;
    elements.documentsView.hidden = view !== "documents";
    elements.meetingsView.hidden = view !== "meetings";
    document.body.dataset.view = view;
    elements.navDocuments.classList.toggle("top-nav__link--active", view === "documents");
    elements.navMeetings.classList.toggle("top-nav__link--active", view === "meetings");
    elements.navDocuments.setAttribute("aria-current", view === "documents" ? "page" : "false");
    elements.navMeetings.setAttribute("aria-current", view === "meetings" ? "page" : "false");
    if (updateHash)
        updateHashForView(view);
    if (scrollToView) {
        const target = view === "meetings" ? elements.meetingsView : elements.documentsView;
        target.scrollIntoView({ block: "start", behavior: "smooth" });
    }
}
function updateHashForView(view) {
    updateHash(view === "meetings" ? "#meetings" : "#documents");
}
function viewFromHash() {
    return window.location.hash === "#meetings" ? "meetings" : "documents";
}
function applyHashState(scrollDocumentDetail = false) {
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
function attachEvents() {
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
    elements.meetingSearchInput.addEventListener("input", () => { state.meetingQuery = elements.meetingSearchInput.value; renderMeetings(); });
    elements.meetingSortSelect.addEventListener("change", () => { state.meetingSortMode = elements.meetingSortSelect.value; renderMeetings(); });
    for (const button of [elements.previousTop, elements.previousBottom])
        button.addEventListener("click", () => { state.currentPage -= 1; renderDocuments(); });
    for (const button of [elements.nextTop, elements.nextBottom])
        button.addEventListener("click", () => { state.currentPage += 1; renderDocuments(); });
}
async function init() {
    attachEvents();
    state.data = await loadPublicData();
    state.indexes = buildRelationIndexes(state.data.documents, state.data.meetings, state.data.agendaItems, state.data.meetingDocumentRelations, state.data.meetingItemDocumentRelations);
    populateTypeFilter();
    renderSummary();
    applyFilters();
    renderMeetings();
    applyHashState(false);
    window.OpenRISMonitor = {
        indexes: state.indexes,
        focusDocumentById(documentId) {
            const documentRecord = findDocumentById(documentId);
            if (documentRecord) {
                setActiveView("documents", false, false);
                updateHash(documentHashFor(documentRecord));
                ensureDocumentVisible(documentRecord);
                selectDocument(documentRecord, true);
            }
        },
        focusMeetingById(meetingId) {
            const meeting = findMeetingById(meetingId);
            if (meeting) {
                setActiveView("meetings", true, false);
                selectMeeting(meeting, true);
            }
        },
    };
}
init().catch((error) => {
    console.error(error);
    elements.statusMessage.textContent = "De viewer kon de publieke exports niet laden. Controleer data/public en de browserconsole.";
});
//# sourceMappingURL=module.js.map