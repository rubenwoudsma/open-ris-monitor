(() => {
  const DATA_BASE = "../data/public";

  const elements = {
    status: document.querySelector("#agenda-browser-status"),
    count: document.querySelector("#agenda-browser-count"),
    list: document.querySelector("#meeting-browser-list"),
    search: document.querySelector("#meeting-search"),
    from: document.querySelector("#meeting-date-from"),
    to: document.querySelector("#meeting-date-to"),
    org: document.querySelector("#meeting-org-filter"),
  };

  const state = {
    latest: null,
    meetings: [],
    meetingItems: [],
    meetingDocuments: [],
    meetingItemDocuments: [],
    documents: [],
    filteredMeetings: [],
    meetingsById: new Map(),
    itemsById: new Map(),
    documentsByKey: new Map(),
  };

  function requireElements() {
    const missing = Object.entries(elements)
      .filter(([, element]) => !element)
      .map(([name]) => name);
    if (missing.length > 0) {
      throw new Error(`HTML mist verwachte agenda-elementen: ${missing.join(", ")}`);
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
    if (!trimmed) return [];

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

  function addIdentifier(result, value) {
    if (value === null || value === undefined) return;
    const textValue = String(value).trim();
    if (textValue) result.add(textValue);
  }

  function documentKey(documentRecord) {
    const identifiers = new Set();
    addIdentifier(identifiers, documentRecord?.id);
    addIdentifier(identifiers, documentRecord?.source_id);
    addIdentifier(identifiers, documentRecord?.source_object_id);
    addIdentifier(identifiers, documentRecord?.download_url);
    addIdentifier(identifiers, documentRecord?.source_url);
    return [...identifiers][0] || String(documentRecord?.title || documentRecord?.filename || "");
  }

  function getDocumentIdentifiers(documentRecord) {
    const identifiers = new Set();
    addIdentifier(identifiers, documentRecord?.id);
    addIdentifier(identifiers, documentRecord?.source_id);
    addIdentifier(identifiers, documentRecord?.source_object_id);
    addIdentifier(identifiers, documentRecord?.download_url);
    addIdentifier(identifiers, documentRecord?.source_url);
    if (documentRecord?.raw && typeof documentRecord.raw === "object") {
      addIdentifier(identifiers, documentRecord.raw.id);
      addIdentifier(identifiers, documentRecord.raw.objectId);
      addIdentifier(identifiers, documentRecord.raw.object_id);
      addIdentifier(identifiers, documentRecord.raw.downloadUrl);
      addIdentifier(identifiers, documentRecord.raw.download_url);
    }
    if (documentRecord?.id && documentRecord?.source_id && String(documentRecord.id).includes("-document-")) {
      const prefix = String(documentRecord.id).split("-document-")[0];
      addIdentifier(identifiers, `${prefix}-document-${documentRecord.source_id}`);
    }
    return [...identifiers];
  }

  function documentTitle(documentRecord) {
    return documentRecord?.title || documentRecord?.description || documentRecord?.filename || "Geen titel";
  }

  function formatOrg(meeting) {
    return text(
      pick(
        meeting?.dmu_name,
        meeting?.organ_name,
        meeting?.organization_name,
        meeting?.committee_name,
        meeting?.description,
        "Onbekend bestuursorgaan",
      ),
    );
  }

  function formatMeetingHeadline(meeting) {
    return text(pick(meeting?.title, meeting?.description, formatOrg(meeting)));
  }

  function formatMeetingMeta(meeting) {
    return [formatDate(pick(meeting?.date, meeting?.meeting_date, meeting?.start_date, meeting?.start_time)), pick(meeting?.start_time, meeting?.start), pick(meeting?.location), formatOrg(meeting)]
      .filter(Boolean)
      .join(" • ");
  }

  function formatItemLabel(item) {
    return [pick(item?.number, item?.item_number, item?.agenda_number), pick(item?.title, item?.description)].filter(Boolean).join(" ");
  }

  function buildSearchBlob(meeting) {
    return [
      meeting?.title,
      meeting?.description,
      meeting?.date,
      meeting?.start_time,
      meeting?.location,
      formatOrg(meeting),
      meeting.items.map((item) => [item.number, item.title, item.description].filter(Boolean).join(" ")).join(" "),
      meeting.documents.map((doc) => [documentTitle(doc), doc.filename, doc.source_id, doc.source_object_id].filter(Boolean).join(" ")).join(" "),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
  }

  function addUniqueDocument(list, documentRecord) {
    const key = documentKey(documentRecord);
    if (!key) return;
    if (list.some((existing) => documentKey(existing) === key)) return;
    list.push(documentRecord);
  }

  function buildModel() {
    state.meetingsById = new Map();
    state.itemsById = new Map();

    for (const meeting of state.meetings) {
      meeting.id = String(pick(meeting.id, meeting.meeting_id, meeting.source_id));
      meeting.items = [];
      meeting.documents = [];
      meeting.searchBlob = "";
      state.meetingsById.set(meeting.id, meeting);
    }

    for (const item of state.meetingItems) {
      item.id = String(pick(item.id, item.meeting_item_id, item.source_id));
      item.documents = [];
      state.itemsById.set(item.id, item);
      const meetingId = String(pick(item.meeting_id, item.meetingId, item.session_id, item.sessionId));
      const meeting = state.meetingsById.get(meetingId);
      if (meeting) {
        meeting.items.push(item);
      }
    }

    state.documentsByKey = new Map();
    for (const doc of state.documents) {
      for (const identifier of getDocumentIdentifiers(doc)) {
        state.documentsByKey.set(String(identifier), doc);
      }
    }

    for (const relation of state.meetingDocuments) {
      const meeting = state.meetingsById.get(String(pick(relation.meeting_id, relation.meetingId)));
      const relationIdentifiers = [
        relation.document_id,
        relation.documentId,
        relation.document_source_id,
        relation.document_object_id,
        relation.document_url,
        relation.download_url,
        relation.source_url,
      ].filter(Boolean).map(String);
      const doc = relationIdentifiers.map((identifier) => state.documentsByKey.get(identifier)).find(Boolean) || null;
      if (meeting && doc) addUniqueDocument(meeting.documents, doc);
    }

    for (const relation of state.meetingItemDocuments) {
      const itemId = String(pick(relation.meeting_item_id, relation.meetingItemId, relation.item_id));
      const item = state.itemsById.get(itemId);
      const relationIdentifiers = [
        relation.document_id,
        relation.documentId,
        relation.document_source_id,
        relation.document_object_id,
        relation.document_url,
        relation.download_url,
        relation.source_url,
      ].filter(Boolean).map(String);
      const doc = relationIdentifiers.map((identifier) => state.documentsByKey.get(identifier)).find(Boolean) || null;
      if (item && doc) addUniqueDocument(item.documents, doc);

      const meetingId = String(pick(relation.meeting_id, relation.meetingId));
      const meeting = state.meetingsById.get(meetingId) || (item ? state.meetingsById.get(String(pick(item.meeting_id, item.meetingId, item.session_id, item.sessionId))) : null);
      if (meeting && doc) addUniqueDocument(meeting.documents, doc);
    }

    state.meetings = [...state.meetingsById.values()].map((meeting) => {
      meeting.items.sort((a, b) => String(pick(a.number, a.item_number, a.agenda_number)).localeCompare(String(pick(b.number, b.item_number, b.agenda_number)), "nl", { numeric: true }));
      meeting.documents.sort((a, b) => documentTitle(a).localeCompare(documentTitle(b), "nl"));
      meeting.searchBlob = buildSearchBlob(meeting);
      return meeting;
    });

    state.meetings.sort((a, b) => {
      const aKey = `${normalizeDateKey(pick(a.date, a.meeting_date, a.start_time))} ${pick(a.start_time, a.start)}`.trim();
      const bKey = `${normalizeDateKey(pick(b.date, b.meeting_date, b.start_time))} ${pick(b.start_time, b.start)}`.trim();
      return bKey.localeCompare(aKey, "nl");
    });

    state.filteredMeetings = state.meetings;
  }

  function syncOrgFilter() {
    const selected = elements.org.value;
    const orgs = [...new Set(state.meetings.map((meeting) => formatOrg(meeting)))].sort((a, b) => a.localeCompare(b, "nl"));

    elements.org.replaceChildren();
    const allOption = document.createElement("option");
    allOption.value = "";
    allOption.textContent = "Alle bestuursorganen";
    elements.org.appendChild(allOption);

    for (const org of orgs) {
      const option = document.createElement("option");
      option.value = org;
      option.textContent = org;
      elements.org.appendChild(option);
    }

    elements.org.value = orgs.includes(selected) ? selected : "";
  }

  function makeDocLink(documentRecord) {
    const link = document.createElement("a");
    link.href = `#documents-title`;
    link.textContent = documentTitle(documentRecord);
    link.title = "Toon dit document in de documentenlijst";
    link.addEventListener("click", (event) => {
      event.preventDefault();
      if (window.OpenRISMonitor?.focusDocument) {
        window.OpenRISMonitor.focusDocument(documentRecord, { searchText: documentTitle(documentRecord) });
      } else if (window.OpenRISMonitor?.focusDocumentByText) {
        window.OpenRISMonitor.focusDocumentByText(documentTitle(documentRecord));
      }
    });
    return link;
  }

  function renderMeetingCard(meeting, expanded = false) {
    const card = document.createElement("article");
    card.className = "meeting-card";

    const details = document.createElement("details");
    details.className = "meeting-details";
    details.open = expanded;

    const summary = document.createElement("summary");
    summary.className = "meeting-summary";

    const title = document.createElement("span");
    title.className = "meeting-summary-title";
    title.textContent = formatMeetingHeadline(meeting);
    summary.appendChild(title);

    const meta = document.createElement("span");
    meta.className = "meeting-summary-meta";
    meta.textContent = formatMeetingMeta(meeting);
    summary.appendChild(meta);

    details.appendChild(summary);

    const body = document.createElement("div");
    body.className = "meeting-body";

    const counts = document.createElement("p");
    counts.className = "meeting-counts";
    const documentCount = meeting.documents.length + meeting.items.reduce((sum, item) => sum + item.documents.length, 0);
    counts.textContent = `${meeting.items.length} agendapunten, ${documentCount} documentkoppelingen`;
    body.appendChild(counts);

    if (meeting.documents.length > 0) {
      const docsTitle = document.createElement("p");
      docsTitle.className = "meeting-section-label";
      docsTitle.textContent = `Koppelingen op vergaderniveau: ${meeting.documents.length}`;
      body.appendChild(docsTitle);

      const docs = document.createElement("div");
      docs.className = "doc-chip-list";
      for (const doc of meeting.documents) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "doc-chip";
        chip.textContent = documentTitle(doc);
        chip.addEventListener("click", () => {
          if (window.OpenRISMonitor?.focusDocument) {
            window.OpenRISMonitor.focusDocument(doc, { searchText: documentTitle(doc) });
          } else if (window.OpenRISMonitor?.focusDocumentByText) {
            window.OpenRISMonitor.focusDocumentByText(documentTitle(doc));
          }
        });
        docs.appendChild(chip);
      }
      body.appendChild(docs);
    }

    if (meeting.items.length > 0) {
      const itemsTitle = document.createElement("p");
      itemsTitle.className = "meeting-section-label";
      itemsTitle.textContent = "Agendapunten";
      body.appendChild(itemsTitle);

      const list = document.createElement("ol");
      list.className = "meeting-item-list";

      for (const item of meeting.items) {
        const li = document.createElement("li");
        li.className = "meeting-item";

        const headline = document.createElement("div");
        headline.className = "meeting-item-headline";
        headline.textContent = formatItemLabel(item) || "Agendapunt zonder titel";
        li.appendChild(headline);

        const itemDocsCount = item.documents.length;
        if (itemDocsCount > 0) {
          const itemDocsLabel = document.createElement("p");
          itemDocsLabel.className = "meeting-item-docs-label";
          itemDocsLabel.textContent = `Documenten: ${itemDocsCount}`;
          li.appendChild(itemDocsLabel);

          const itemDocs = document.createElement("div");
          itemDocs.className = "doc-chip-list";
          for (const doc of item.documents) {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "doc-chip doc-chip-small";
            chip.textContent = documentTitle(doc);
            chip.addEventListener("click", () => {
              if (window.OpenRISMonitor?.focusDocument) {
                window.OpenRISMonitor.focusDocument(doc, { searchText: documentTitle(doc) });
              } else if (window.OpenRISMonitor?.focusDocumentByText) {
                window.OpenRISMonitor.focusDocumentByText(documentTitle(doc));
              }
            });
            itemDocs.appendChild(chip);
          }
          li.appendChild(itemDocs);
        }

        list.appendChild(li);
      }

      body.appendChild(list);
    }

    details.appendChild(body);
    card.appendChild(details);
    return card;
  }

  function renderMeetingList() {
    const query = elements.search.value.trim().toLowerCase();
    const from = elements.from.value;
    const to = elements.to.value;
    const org = elements.org.value;

    state.filteredMeetings = state.meetings.filter((meeting) => {
      const meetingDate = normalizeDateKey(pick(meeting.date, meeting.meeting_date, meeting.start_time));
      const matchesQuery = !query || meeting.searchBlob.includes(query);
      const matchesFrom = !from || (meetingDate && meetingDate >= from);
      const matchesTo = !to || (meetingDate && meetingDate <= to);
      const matchesOrg = !org || formatOrg(meeting) === org;
      return matchesQuery && matchesFrom && matchesTo && matchesOrg;
    });

    const totalItems = state.filteredMeetings.reduce((count, meeting) => count + meeting.items.length, 0);
    const totalDocs = state.filteredMeetings.reduce(
      (count, meeting) => count + meeting.documents.length + meeting.items.reduce((sum, item) => sum + item.documents.length, 0),
      0,
    );

    elements.count.textContent = `${state.filteredMeetings.length} vergaderingen, ${totalItems} agendapunten, ${totalDocs} documentkoppelingen`;

    elements.list.replaceChildren();
    if (state.filteredMeetings.length === 0) {
      const empty = document.createElement("p");
      empty.textContent = "Geen vergaderingen gevonden voor deze filter.";
      elements.list.appendChild(empty);
      return;
    }

    const fragment = document.createDocumentFragment();
    state.filteredMeetings.forEach((meeting, index) => {
      fragment.appendChild(renderMeetingCard(meeting, index === 0));
    });
    elements.list.appendChild(fragment);
  }

  async function loadData() {
    state.latest = await fetchJson(`${DATA_BASE}/latest.json`);
    const outputs = state.latest.outputs || state.latest.exports || {};

    const meetingsPath = outputs.meetings ? `${DATA_BASE}/${outputs.meetings}` : null;
    const meetingItemsPath = outputs.meeting_items ? `${DATA_BASE}/${outputs.meeting_items}` : null;
    const meetingDocumentsPath = outputs.meeting_documents ? `${DATA_BASE}/${outputs.meeting_documents}` : null;
    const meetingItemDocumentsPath = outputs.meeting_item_documents ? `${DATA_BASE}/${outputs.meeting_item_documents}` : null;
    const documentsPath = outputs.documents ? `${DATA_BASE}/${outputs.documents}` : null;

    state.meetings = await fetchOptionalJsonl(meetingsPath);
    state.meetingItems = await fetchOptionalJsonl(meetingItemsPath);
    state.meetingDocuments = await fetchOptionalJsonl(meetingDocumentsPath);
    state.meetingItemDocuments = await fetchOptionalJsonl(meetingItemDocumentsPath);
    state.documents = await fetchOptionalJsonl(documentsPath);
  }

  function wireEvents() {
    elements.search.addEventListener("input", renderMeetingList);
    elements.from.addEventListener("change", renderMeetingList);
    elements.to.addEventListener("change", renderMeetingList);
    elements.org.addEventListener("change", renderMeetingList);
  }

  async function init() {
    try {
      requireElements();
      await loadData();
      buildModel();
      syncOrgFilter();
      wireEvents();
      elements.status.textContent = `Vergaderbrowser geladen uit ${state.meetings.length} vergaderingen en ${state.meetingItems.length} agendapunten.`;
      renderMeetingList();
    } catch (error) {
      console.error(error);
      if (elements.status) {
        elements.status.textContent = "De vergaderbrowser kon niet worden geladen.";
      }
      if (elements.list) {
        elements.list.replaceChildren();
        const message = document.createElement("p");
        message.textContent = error.message;
        elements.list.appendChild(message);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
