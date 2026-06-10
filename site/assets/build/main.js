import { loadPublicData } from "./data/loaders.js";
import { buildRelationIndexes, getDocumentIdentifiers } from "./data/relations.js";
import { formatBytes, formatDate, formatDateTime, pick, safeUrl, text, timestamp } from "./ui/format.js";
const state = {
    data: null,
    indexes: null,
    filteredDocuments: [],
    currentPage: 1,
    pageSize: 50,
    sortMode: "date-desc",
    selectedDocumentId: null,
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
    searchInput: byId("search-input"),
    typeFilter: byId("type-filter"),
    sortSelect: byId("sort-select"),
    pageSizeSelect: byId("page-size-select"),
    resultCount: byId("result-count"),
    documentDetail: byId("document-detail"),
    documentDetailTitle: byId("document-detail-title"),
    documentDetailBody: byId("document-detail-body"),
    clearDocumentSelection: byId("clear-document-selection"),
    meetingsCount: byId("meetings-count"),
    agendaItemsCount: byId("agenda-items-count"),
    linkedDocumentsCount: byId("linked-documents-count"),
    dataQualityNotice: byId("data-quality-notice"),
    visibleDocumentsCount: byId("visible-documents-count"),
    tableBody: byId("documents-table-body"),
    documentsView: byId("documents-view"),
    meetingsView: byId("meetings-view"),
    meetingsTableBody: byId("meetings-table-body"),
    meetingsResultCount: byId("meetings-result-count"),
    navDocuments: byId("nav-documents"),
    navMeetings: byId("nav-meetings"),
    previousTop: byId("previous-page-top"),
    nextTop: byId("next-page-top"),
    pageInfoTop: byId("page-info-top"),
    previousBottom: byId("previous-page-bottom"),
    nextBottom: byId("next-page-bottom"),
    pageInfoBottom: byId("page-info-bottom"),
};
function getDocumentId(documentRecord) {
    return getDocumentIdentifiers(documentRecord)[0] ?? "";
}
function getDocumentTitle(documentRecord) {
    return pick(documentRecord.title, documentRecord.description, documentRecord.filename) || "Geen titel";
}
function getDocumentDate(documentRecord) {
    return pick(documentRecord.publication_datetime, documentRecord.date_published, documentRecord.publication_date, documentRecord.document_date, documentRecord.date, documentRecord.retrieved_at);
}
function getMeetingTitle(meeting) {
    return pick(meeting?.description, meeting?.title, meeting?.dmu_name) || "Vergadering zonder titel";
}
function getAgendaItemTitle(item) {
    const number = pick(item?.number);
    const title = pick(item?.title, item?.description) || "Agendapunt zonder titel";
    return number ? `${number}. ${title}` : title;
}
function getMeetingId(meeting) {
    return pick(meeting.id, meeting.meeting_id, meeting.source_id, meeting.source_object_id, meeting.upstream_id);
}
function getMeetingDate(meeting) {
    return pick(meeting?.date, meeting?.start_time, meeting?.startTime, meeting?.datetime, meeting?.meeting_date);
}
function agendaItemIdsForMeeting(meeting) {
    const meetingId = getMeetingId(meeting);
    const indexed = meetingId ? state.indexes?.agendaItemIdsByMeetingId.get(meetingId) ?? [] : [];
    if (indexed.length > 0)
        return uniqueValues(indexed);
    return uniqueValues((state.data?.agendaItems ?? [])
        .filter((item) => pick(item.meeting_id, item.meetingId, item.session_id, item.sessionId) === meetingId)
        .map((item) => pick(item.id, item.agenda_item_id, item.source_id, item.source_object_id)));
}
function linkedDocumentIdsForMeeting(meeting) {
    const meetingId = getMeetingId(meeting);
    const directDocumentIds = meetingId ? state.indexes?.documentIdsByMeetingId.get(meetingId) ?? [] : [];
    const agendaDocumentIds = agendaItemIdsForMeeting(meeting).flatMap((itemId) => state.indexes?.documentIdsByAgendaItemId.get(itemId) ?? []);
    return uniqueValues([...directDocumentIds, ...agendaDocumentIds]);
}
function renderMeetings() {
    const meetings = [...(state.data?.meetings ?? [])].sort((a, b) => timestamp(getMeetingDate(b)) - timestamp(getMeetingDate(a)));
    elements.meetingsResultCount.textContent = `${meetings.length} vergadering(en)`;
    elements.meetingsTableBody.replaceChildren();
    if (meetings.length === 0) {
        const row = document.createElement("tr");
        const cell = createCell("Geen vergaderingen gevonden in de huidige public export.");
        cell.colSpan = 4;
        row.appendChild(cell);
        elements.meetingsTableBody.appendChild(row);
        return;
    }
    for (const meeting of meetings) {
        const row = document.createElement("tr");
        const titleCell = document.createElement("td");
        const title = document.createElement("strong");
        title.className = "meeting-title";
        title.textContent = getMeetingTitle(meeting);
        titleCell.appendChild(title);
        row.appendChild(createCell(formatDate(getMeetingDate(meeting))));
        row.appendChild(titleCell);
        row.appendChild(createCell(text(agendaItemIdsForMeeting(meeting).length)));
        row.appendChild(createCell(text(linkedDocumentIdsForMeeting(meeting).length)));
        elements.meetingsTableBody.appendChild(row);
    }
}
function setActiveView(view, updateHash = false) {
    state.activeView = view;
    elements.documentsView.toggleAttribute("hidden", view !== "documents");
    elements.meetingsView.toggleAttribute("hidden", view !== "meetings");
    elements.navDocuments.classList.toggle("top-nav__link--active", view === "documents");
    elements.navMeetings.classList.toggle("top-nav__link--active", view === "meetings");
    for (const link of Array.from(document.querySelectorAll("[data-view-link]"))) {
        link.classList.toggle("is-active", link.dataset.viewLink === view);
    }
    if (updateHash)
        window.history.replaceState({}, "", `${window.location.pathname}${window.location.search}#${view}`);
}
function restoreView() {
    setActiveView(window.location.hash === "#meetings" ? "meetings" : "documents");
}
function isUnknownType(value) {
    const normalized = value.trim().toLowerCase();
    return !normalized || normalized === "unknown" || normalized === "onbekend";
}
function unavailable(reason = "Niet beschikbaar in export") {
    return reason;
}
function pickFromRaw(record, ...keys) {
    if (!record.raw || typeof record.raw !== "object")
        return "";
    for (const key of keys) {
        const value = record.raw[key];
        const picked = pick(value);
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
    const sourceType = pick(documentRecord.document_type, pickFromRaw(documentRecord, "document_type", "documentTypeLabel", "documentType", "category", "kind"));
    if (!sourceType)
        return "";
    const compactType = getCompactType(documentRecord);
    const compactTypeLabel = getCompactTypeLabel(documentRecord);
    if (sourceType === compactType || sourceType === compactTypeLabel)
        return "";
    return sourceType;
}
function getDocumentFilename(documentRecord) {
    return pick(documentRecord.filename, documentRecord.file_name, documentRecord.fileName, documentRecord.name, documentRecord.display_name, documentRecord.original_filename, pickFromRaw(documentRecord, "filename", "file_name", "fileName", "name", "displayName", "originalFilename"), pickNestedRaw(documentRecord, "file", "filename", "fileName", "name"));
}
function getDocumentSize(documentRecord) {
    const values = [
        documentRecord.file_size_bytes,
        documentRecord.size_bytes,
        documentRecord.file_size,
        documentRecord.filesize,
        documentRecord.size,
        documentRecord.bytes,
        documentRecord.content_length,
        pickFromRaw(recordDocumentForRaw(documentRecord), "file_size_bytes", "size_bytes", "file_size", "fileSize", "filesize", "size", "bytes", "contentLength"),
        pickNestedRaw(documentRecord, "file", "size", "bytes", "size_bytes", "fileSize"),
    ];
    return values.find((value) => pick(value));
}
function recordDocumentForRaw(documentRecord) {
    return documentRecord;
}
function formatDocumentSize(documentRecord) {
    const formatted = formatBytes(getDocumentSize(documentRecord));
    return formatted === "-" ? unavailable("Geen bestandsgrootte beschikbaar") : formatted;
}
function hasDocumentFilenameMetadata(documentRecord) {
    return Boolean(getDocumentFilename(documentRecord));
}
function hasDocumentSizeMetadata(documentRecord) {
    return Boolean(getDocumentSize(documentRecord));
}
function hasAnyDocumentFilenameMetadata(records) {
    return records.some(hasDocumentFilenameMetadata);
}
function hasAnyDocumentSizeMetadata(records) {
    return records.some(hasDocumentSizeMetadata);
}
function getVisibleDocumentColumnCount(showFilenameColumn, showSizeColumn) {
    return 4 + Number(showFilenameColumn) + Number(showSizeColumn);
}
function setTableColumnVisibility(headerLabel, visible) {
    const table = elements.tableBody.closest("table");
    const headers = Array.from(table?.querySelectorAll("thead th") ?? []);
    const header = headers.find((cell) => cell.textContent?.trim() === headerLabel);
    if (header)
        header.toggleAttribute("hidden", !visible);
}
function getDocumentUrl(documentRecord) {
    return safeUrl(pick(documentRecord.download_url, documentRecord.source_url, documentRecord.url, documentRecord.file_url, documentRecord.document_url, documentRecord.web_url, documentRecord.external_url, pickFromRaw(documentRecord, "download_url", "downloadUrl", "source_url", "sourceUrl", "url", "fileUrl", "documentUrl", "webUrl"), pickNestedRaw(documentRecord, "file", "url", "downloadUrl", "download_url", "href")));
}
function uniqueValues(values) {
    return [...new Set(values.filter(Boolean))];
}
function documentIds(documentRecord) {
    return uniqueValues(getDocumentIdentifiers(documentRecord));
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
        labels.push([getMeetingTitle(meeting), formatDate(pick(meeting?.date, meeting?.start_time))].filter(Boolean).join(", "));
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
    ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
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
    if (documents.length > 0 && unknownTypeCount === documents.length) {
        notices.push("Alle documenten hebben nog een onbekend genormaliseerd documenttype.");
    }
    elements.dataQualityNotice.textContent = notices.join(" ");
    elements.dataQualityNotice.hidden = notices.length === 0;
    const relationText = latest.relations_enabled
        ? ` Relationele context: ${latest.relations_summary?.meetings_seen ?? 0} vergaderingen, ${latest.relations_summary?.meeting_items_seen ?? 0} agendapunten. ${linkedDocumentCount} documenten hebben een koppeling.`
        : "";
    elements.statusMessage.textContent = `${state.data?.documents.length ?? 0} documenten geladen.${relationText}`;
}
function populateTypeFilter() {
    const options = new Map();
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
function sortDocuments(records) {
    const sorted = [...records];
    const byTitle = (a, b) => getDocumentTitle(a).localeCompare(getDocumentTitle(b), "nl");
    const byType = (a, b) => getCompactTypeLabel(a).localeCompare(getCompactTypeLabel(b), "nl");
    const bySize = (a, b) => Number(getDocumentSize(a) ?? 0) - Number(getDocumentSize(b) ?? 0);
    const byDate = (a, b) => timestamp(getDocumentDate(a)) - timestamp(getDocumentDate(b));
    switch (state.sortMode) {
        case "date-asc":
            return sorted.sort(byDate);
        case "title-asc":
            return sorted.sort(byTitle);
        case "type-asc":
            return sorted.sort(byType);
        case "size-desc":
            return sorted.sort((a, b) => bySize(b, a));
        case "size-asc":
            return sorted.sort(bySize);
        case "date-desc":
        default:
            return sorted.sort((a, b) => byDate(b, a));
    }
}
function applyFilters() {
    const query = elements.searchInput.value.trim().toLowerCase();
    const type = elements.typeFilter.value;
    const allDocuments = state.data?.documents ?? [];
    let records = allDocuments.filter((documentRecord) => {
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
function createDocumentTitleCell(documentRecord) {
    const cell = document.createElement("td");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "link-button document-title-button";
    button.textContent = getDocumentTitle(documentRecord);
    button.addEventListener("click", () => selectDocument(documentRecord, true));
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
    const detailButton = document.createElement("button");
    detailButton.type = "button";
    detailButton.className = "secondary-button";
    detailButton.textContent = "Details";
    detailButton.addEventListener("click", () => selectDocument(documentRecord, true));
    actionList.appendChild(detailButton);
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
function findDocumentById(documentId) {
    if (!documentId)
        return undefined;
    return state.data?.documents.find((documentRecord) => documentIds(documentRecord).includes(documentId));
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
        const fallback = document.createElement("p");
        fallback.className = "empty-state";
        fallback.textContent = "Geen veilige documentlink beschikbaar in de metadata.";
        actions.appendChild(fallback);
    }
    grid.appendChild(actions);
    elements.documentDetailBody.appendChild(grid);
    const metadataIssues = [
        isUnknownType(pick(documentRecord.normalized_document_type, documentRecord.normalized_document_type_label, documentRecord.type)) ? "compact documenttype ontbreekt" : "",
        getDocumentFilename(documentRecord) ? "" : "bestandsnaam ontbreekt",
        hasDocumentSizeMetadata(documentRecord) ? "" : "bestandsgrootte ontbreekt",
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
    if (meetingIds.length === 0) {
        meetingsSection.appendChild(renderEmptyRelation("Geen gekoppelde vergadering gevonden in de huidige public export."));
    }
    else {
        for (const meetingId of meetingIds) {
            const meeting = state.indexes?.meetingsById.get(meetingId);
            const meta = [formatDate(pick(meeting?.date, meeting?.start_time)), pick(meeting?.dmu_name), meetingId].filter(Boolean).join(" · ");
            meetingsSection.appendChild(createRelationCard(getMeetingTitle(meeting), meta || "Vergadering", text(meeting?.description, "")));
        }
    }
    relations.appendChild(meetingsSection);
    const agendaSection = document.createElement("section");
    agendaSection.className = "detail-section";
    appendSectionHeading(agendaSection, "Gekoppelde agendapunten");
    if (itemIds.length === 0) {
        agendaSection.appendChild(renderEmptyRelation("Geen gekoppeld agendapunt gevonden in de huidige public export."));
    }
    else {
        for (const itemId of itemIds) {
            const item = state.indexes?.agendaItemsById.get(itemId);
            const meeting = state.indexes?.meetingsById.get(pick(item?.meeting_id, item?.meetingId, item?.session_id, item?.sessionId));
            const meta = [getMeetingTitle(meeting), itemId].filter(Boolean).join(" · ");
            agendaSection.appendChild(createRelationCard(getAgendaItemTitle(item), meta || "Agendapunt", text(item?.description, "")));
        }
    }
    relations.appendChild(agendaSection);
    const versionsSection = document.createElement("section");
    versionsSection.className = "detail-section";
    appendSectionHeading(versionsSection, "Versies");
    if (versions.length === 0) {
        versionsSection.appendChild(renderEmptyRelation("Geen aparte versiehistorie gevonden."));
    }
    else {
        for (const version of versions.slice(0, 10)) {
            const meta = [formatDateTime(version.retrieved_at), pick(version.id, version.source_id)].filter(Boolean).join(" · ");
            versionsSection.appendChild(createRelationCard("Documentversie", meta || "Versie", ""));
        }
    }
    relations.appendChild(versionsSection);
    elements.documentDetailBody.appendChild(relations);
}
function updateUrlForDocument(documentId) {
    const url = new URL(window.location.href);
    if (documentId) {
        url.searchParams.set("doc", documentId);
    }
    else {
        url.searchParams.delete("doc");
        url.searchParams.delete("documentId");
    }
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}
function selectDocument(documentRecord, updateUrl = false) {
    const documentId = getDocumentId(documentRecord);
    state.selectedDocumentId = documentId || null;
    renderDocumentDetail(documentRecord);
    renderDocuments();
    if (updateUrl)
        updateUrlForDocument(documentId);
    elements.documentDetail.scrollIntoView({ block: "start", behavior: "smooth" });
}
function clearDocumentSelection(updateUrl = false) {
    state.selectedDocumentId = null;
    elements.documentDetail.hidden = true;
    elements.documentDetailTitle.textContent = "Documentdetails";
    elements.documentDetailBody.replaceChildren();
    renderDocuments();
    if (updateUrl)
        updateUrlForDocument(null);
}
function restoreDeepLink() {
    const params = new URLSearchParams(window.location.search);
    const query = params.get("q") ?? "";
    const documentId = params.get("documentId") ?? params.get("doc") ?? "";
    if (query)
        elements.searchInput.value = query;
    if (documentId) {
        const documentRecord = findDocumentById(documentId);
        if (documentRecord) {
            state.selectedDocumentId = getDocumentId(documentRecord);
            renderDocumentDetail(documentRecord);
        }
        else {
            elements.documentDetail.hidden = false;
            elements.documentDetailTitle.textContent = "Document niet gevonden";
            elements.documentDetailBody.textContent = `De gedeelde documentlink kon niet worden gevonden: ${documentId}`;
        }
    }
}
function attachEvents() {
    elements.searchInput.addEventListener("input", () => {
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
    elements.clearDocumentSelection.addEventListener("click", () => clearDocumentSelection(true));
    elements.navDocuments.addEventListener("click", (event) => { event.preventDefault(); setActiveView("documents", true); });
    elements.navMeetings.addEventListener("click", (event) => { event.preventDefault(); setActiveView("meetings", true); });
    for (const link of Array.from(document.querySelectorAll("[data-view-link]"))) {
        link.addEventListener("click", (event) => {
            event.preventDefault();
            setActiveView(link.dataset.viewLink === "meetings" ? "meetings" : "documents", true);
        });
    }
    window.addEventListener("hashchange", restoreView);
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
async function init() {
    attachEvents();
    state.data = await loadPublicData();
    state.indexes = buildRelationIndexes(state.data.documents, state.data.meetings, state.data.agendaItems, state.data.meetingDocumentRelations, state.data.meetingItemDocumentRelations);
    populateTypeFilter();
    renderSummary();
    renderMeetings();
    restoreDeepLink();
    restoreView();
    applyFilters();
    window.OpenRISMonitor = {
        indexes: state.indexes,
        focusDocumentById(documentId) {
            const documentRecord = findDocumentById(documentId);
            if (documentRecord)
                selectDocument(documentRecord, true);
        },
    };
}
init().catch((error) => {
    console.error(error);
    elements.statusMessage.textContent = "De viewer kon de publieke exports niet laden. Controleer data/public en de browserconsole.";
});
