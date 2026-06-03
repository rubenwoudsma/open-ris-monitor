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

  function toId(record) {
    return String(pick(record?.id, record?.meeting_id, record?.meeting_item_id, record?.document_id, record?.source_id, record?.source_object_id));
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

  function formatOrg(meeting) {
    return text(pick(
      meeting?.dmu_name,
      meeting?.organ_name,
      meeting?.organization_name,
      meeting?.committee_name,
      meeting?.description,
      "Onbekend bestuursorgaan",
    ));
  }

  function formatMeetingLabel(meeting) {
    const parts = [
      formatDate(pick(meeting?.date, meeting?.meeting_date, meeting?.start_date, meeting?.start_time)),
      pick(meeting?.start_time, meeting?.start),
      pick(meeting?.location),
    ].filter(Boolean);
    return parts.join(" • ");
  }

  function formatItemLabel(item) {
    return [pick(item?.number, item?.item_number, item?.agenda_number), pick(item?.title, item?.description)].filter(Boolean).join(" ");
  }

  function formatDocumentLabel(documentRecord) {
    return text(pick(documentRecord?.title, documentRecord?.description, documentRecord?.filename, `Document ${documentRecord?.id || documentRecord?.source_id || "onbekend"}`));
  }

  function getDocumentSearchTerm(documentRecord) {
    return [documentRecord?.title, documentRecord?.filename, documentRecord?.source_id, documentRecord?.source_object_id, documentRecord?.id]
      .filter(Boolean)
      .join(" ");
  }

  function createLookup(items, keyFn) {
    const map = new Map();
    for (const item of items) {
      const key = keyFn(item);
      if (!key) continue;
      const list = map.get(key) || [];
      list.push(item);
      map.set(key, list);
    }
    return map;
  }

  function compareMaybeNumeric(a, b) {
    const aNum = Number.parseFloat(String(a).replace(",", "."));
    const bNum = Number.parseFloat(String(b).replace(",", "."));
    const aValid = Number.isFinite(aNum);
    const bValid = Number.isFinite(bNum);
    if (aValid && bValid && aNum !== bNum) return aNum - bNum;
    return String(a || "").localeCompare(String(b || ""), "nl");
  }

  function buildModel() {
    const meetingsById = new Map();
    const itemsById = new Map();
    const documentsById = new Map();

    for (const documentRecord of state.documents) {
      const id = toId(documentRecord);
      if (id) documentsById.set(id, documentRecord);
    }

    for (const meeting of state.meetings) {
      const normalized = { ...meeting, id: toId(meeting), items: [], documents: [], agendaSearchBlob: "" };
      if (normalized.id) meetingsById.set(normalized.id, normalized);
    }

    for (const item of state.meetingItems) {
      const normalized = { ...item, id: toId(item), documents: [] };
      if (!normalized.id) continue;
      itemsById.set(normalized.id, normalized);
      const meetingId = String(pick(item?.meeting_id, item?.meetingId, item?.session_id, item?.sessionId));
      const meeting = meetingsById.get(meetingId);
      if (meeting) meeting.items.push(normalized);
    }

    for (const relation of state.meetingDocuments) {
      const meetingId = String(pick(relation?.meeting_id, relation?.meetingId));
      const documentId = String(pick(relation?.document_id, relation?.documentId));
      const meeting = meetingsById.get(meetingId);
      const documentRecord = documentsById.get(documentId);
      if (meeting && documentRecord) {
        meeting.documents.push(documentRecord);
      }
    }

    for (const relation of state.meetingItemDocuments) {
      const itemId = String(pick(relation?.meeting_item_id, relation?.meetingItemId, relation?.item_id));
      const documentId = String(pick(relation?.document_id, relation?.documentId));
      const item = itemsById.get(itemId);
      const documentRecord = documentsById.get(documentId);

      if (item && documentRecord) {
        item.documents.push(documentRecord);
      }

      if (documentRecord) {
        const meetingId = String(pick(relation?.meeting_id, relation?.meetingId));
        const meeting = meetingsById.get(meetingId) || (item ? meetingsById.get(String(pick(item?.meeting_id, item?.meetingId, item?.session_id, item?.sessionId))) : null);
        if (meeting && !meeting.documents.includes(documentRecord)) {
          meeting.documents.push(documentRecord);
        }
      }
    }

    const meetings = [...meetingsById.values()].map((meeting) => {
      meeting.items.sort((a, b) => compareMaybeNumeric(pick(a?.number, a?.item_number, a?.agenda_number), pick(b?.number, b?.item_number, b?.agenda_number)));
      meeting.documents.sort((a, b) => formatDocumentLabel(a).localeCompare(formatDocumentLabel(b), "nl"));
      meeting.agendaSearchBlob = [
        meeting.description,
        meeting.dmu_name,
        meeting.organ_name,
        meeting.organization_name,
        meeting.title,
        meeting.location,
        meeting.date,
        meeting.start_time,
        meeting.items.map((item) => [item.number, item.title, item.description].filter(Boolean).join(" ")).join(" "),
        meeting.documents.map((doc) => [doc.title, doc.filename, doc.source_id].filter(Boolean).join(" ")).join(" "),
      ].filter(Boolean).join(" ").toLowerCase();
      return meeting;
    });

    meetings.sort((a, b) => {
      const aKey = `${normalizeDateKey(pick(a?.date, a?.meeting_date, a?.start_time))} ${pick(a?.start_time, a?.start)}`.trim();
      const bKey = `${normalizeDateKey(pick(b?.date, b?.meeting_date, b?.start_time))} ${pick(b?.start_time, b?.start)}`.trim();
      return bKey.localeCompare(aKey, "nl");
    });

    state.meetings = meetings;
    state.filteredMeetings = meetings;
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

  function linkToDocumentRecord(documentRecord) {
    const searchInput = document.querySelector("#search-input");
    if (searchInput) {
      searchInput.value = getDocumentSearchTerm(documentRecord);
      searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    }
    document.querySelector("#documents-title")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function createDocumentLink(documentRecord) {
    const link = document.createElement("a");
    link.href = "#documents-title";
    link.textContent = formatDocumentLabel(documentRecord);
    link.title = "Filter de documentenlijst op dit document";
    link.addEventListener("click", (event) => {
      event.preventDefault();
      linkToDocumentRecord(documentRecord);
    });
    return link;
  }

  function renderMeetingList() {
    const query = elements.search.value.trim().toLowerCase();
    const from = elements.from.value;
    const to = elements.to.value;
    const org = elements.org.value;

    state.filteredMeetings = state.meetings.filter((meeting) => {
      const meetingDate = normalizeDateKey(pick(meeting.date, meeting.meeting_date, meeting.start_time));
      const matchesQuery = !query || meeting.agendaSearchBlob.includes(query);
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

    if (state.filteredMeetings.length === 0) {
      elements.list.replaceChildren();
      const empty = document.createElement("p");
      empty.textContent = "Geen vergaderingen gevonden voor deze filter.";
      elements.list.appendChild(empty);
      return;
    }

    const fragment = document.createDocumentFragment();

    for (const meeting of state.filteredMeetings) {
      const card = document.createElement("article");
      card.className = "meeting-card";

      const heading = document.createElement("h3");
      heading.textContent = pick(meeting.title, meeting.description, formatOrg(meeting));
      card.appendChild(heading);

      const meta = document.createElement("p");
      meta.textContent = `${formatMeetingLabel(meeting)} • ${formatOrg(meeting)}`;
      card.appendChild(meta);

      if (meeting.documents.length > 0) {
        const docsIntro = document.createElement("p");
        docsIntro.textContent = `Koppelingen op vergaderniveau: ${meeting.documents.length}`;
        card.appendChild(docsIntro);

        const meetingDocs = document.createElement("ul");
        for (const documentRecord of meeting.documents) {
          const item = document.createElement("li");
          item.appendChild(createDocumentLink(documentRecord));
          meetingDocs.appendChild(item);
        }
        card.appendChild(meetingDocs);
      }

      if (meeting.items.length > 0) {
        const itemList = document.createElement("ol");
        for (const itemRecord of meeting.items) {
          const item = document.createElement("li");

          const title = document.createElement("strong");
          title.textContent = formatItemLabel(itemRecord) || "Agendapunt zonder titel";
          item.appendChild(title);

          const infoText = [pick(itemRecord?.status, itemRecord?.phase, itemRecord?.resolution)].filter(Boolean).join(" • ");
          if (infoText) {
            const info = document.createElement("p");
            info.textContent = infoText;
            item.appendChild(info);
          }

          if (itemRecord.documents.length > 0) {
            const docsLabel = document.createElement("p");
            docsLabel.textContent = `Documenten: ${itemRecord.documents.length}`;
            item.appendChild(docsLabel);

            const docs = document.createElement("ul");
            for (const documentRecord of itemRecord.documents) {
              const docItem = document.createElement("li");
              docItem.appendChild(createDocumentLink(documentRecord));
              docs.appendChild(docItem);
            }
            item.appendChild(docs);
          }

          itemList.appendChild(item);
        }
        card.appendChild(itemList);
      }

      fragment.appendChild(card);
    }

    elements.list.replaceChildren(fragment);
  }

  async function loadData() {
    state.latest = await fetchJson(`${DATA_BASE}/latest.json`);
    const outputs = state.latest.outputs || {};

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
