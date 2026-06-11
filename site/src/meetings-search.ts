type MeetingRow = {
  row: HTMLTableRowElement;
  dateText: string;
  titleText: string;
  agendaText: string;
  searchableText: string;
  timestamp: number;
};

const meetingsSearchElements = {
  form: document.getElementById("meetings-controls") as HTMLFormElement | null,
  query: document.getElementById("meeting-search-input") as HTMLInputElement | null,
  sort: document.getElementById("meeting-sort-select") as HTMLSelectElement | null,
  count: document.getElementById("visible-meetings-count"),
  resultCount: document.getElementById("meetings-result-count"),
  tableBody: document.getElementById("meetings-table-body") as HTMLTableSectionElement | null,
};

let meetingRowsObserver: MutationObserver | null = null;
let applyingMeetingFilters = false;
let lastRenderedMeetingSignature = "";

function meetingTimestamp(value: string): number {
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function collectMeetingRows(): MeetingRow[] {
  const rows = Array.from(meetingsSearchElements.tableBody?.querySelectorAll("tr") ?? []);
  return rows
    .filter((row) => row.querySelector("button"))
    .map((row) => {
      const cells = Array.from(row.querySelectorAll("td"));
      const dateText = cells[0]?.textContent?.trim() ?? "";
      const titleText = cells[1]?.textContent?.trim() ?? "";
      const agendaText = cells[2]?.textContent?.trim() ?? "";
      const documentText = cells[3]?.textContent?.trim() ?? "";
      return {
        row,
        dateText,
        titleText,
        agendaText,
        searchableText: [dateText, titleText, agendaText, documentText].join(" ").toLowerCase(),
        timestamp: meetingTimestamp(dateText),
      };
    });
}

function renderEmptyMeetingSearchResult(): void {
  const tableBody = meetingsSearchElements.tableBody;
  if (!tableBody) return;
  const row = document.createElement("tr");
  row.dataset.meetingSearchEmpty = "true";
  const cell = document.createElement("td");
  cell.colSpan = 5;
  cell.textContent = "Geen vergaderingen gevonden voor deze zoekopdracht.";
  row.appendChild(cell);
  tableBody.appendChild(row);
}

function updateMeetingCounts(visibleCount: number, totalCount: number): void {
  if (meetingsSearchElements.count) meetingsSearchElements.count.textContent = `${visibleCount} zichtbaar`;
  if (meetingsSearchElements.resultCount) meetingsSearchElements.resultCount.textContent = `${visibleCount} van ${totalCount} vergadering(en)`;
}

function meetingSignature(rows: MeetingRow[]): string {
  return rows.map((entry) => `${entry.dateText}|${entry.titleText}|${entry.agendaText}`).join("\n");
}

function pauseMeetingRowsObserver(): void {
  meetingRowsObserver?.disconnect();
}

function resumeMeetingRowsObserver(): void {
  if (!meetingRowsObserver || !meetingsSearchElements.tableBody) return;
  meetingRowsObserver.observe(meetingsSearchElements.tableBody, { childList: true });
}

function applyMeetingFilters(): void {
  const tableBody = meetingsSearchElements.tableBody;
  if (!tableBody || applyingMeetingFilters) return;

  applyingMeetingFilters = true;
  pauseMeetingRowsObserver();
  try {
    tableBody.querySelectorAll('tr[data-meeting-search-empty="true"]').forEach((row) => row.remove());

    const rows = collectMeetingRows();
    if (rows.length === 0) {
      lastRenderedMeetingSignature = "";
      updateMeetingCounts(0, 0);
      return;
    }

    const query = meetingsSearchElements.query?.value.trim().toLowerCase() ?? "";
    const sortMode = meetingsSearchElements.sort?.value ?? "date-desc";
    const visibleRows = rows.filter((entry) => !query || entry.searchableText.includes(query));

    visibleRows.sort((a, b) => (sortMode === "date-asc" ? a.timestamp - b.timestamp : b.timestamp - a.timestamp));

    const nextSignature = `${query}|${sortMode}|${meetingSignature(visibleRows)}`;
    if (nextSignature !== lastRenderedMeetingSignature) {
      tableBody.replaceChildren(...visibleRows.map((entry) => entry.row));
      if (visibleRows.length === 0) renderEmptyMeetingSearchResult();
      lastRenderedMeetingSignature = nextSignature;
    }
    updateMeetingCounts(visibleRows.length, rows.length);
  } finally {
    applyingMeetingFilters = false;
    resumeMeetingRowsObserver();
  }
}

function initializeMeetingSearch(): void {
  if (!meetingsSearchElements.form || !meetingsSearchElements.query || !meetingsSearchElements.sort || !meetingsSearchElements.tableBody) return;

  meetingsSearchElements.form.addEventListener("submit", (event) => event.preventDefault());
  meetingsSearchElements.query.addEventListener("input", applyMeetingFilters);
  meetingsSearchElements.sort.addEventListener("change", applyMeetingFilters);

  meetingRowsObserver = new MutationObserver(() => applyMeetingFilters());
  resumeMeetingRowsObserver();
  applyMeetingFilters();
}

initializeMeetingSearch();
