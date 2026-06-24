import { loadJson, loadJsonl, loadOptionalJsonl } from "./jsonl.js";
export const DATA_BASE = "../data/public";
export async function loadPublicData(basePath = DATA_BASE) {
    const [latest, documents, documentVersions, meetings, agendaItems, meetingDocumentRelations, meetingItemDocumentRelations, organizationGroups, organizationPersons, organizationRoles, organizationPositions, organizationGroupMemberships,] = await Promise.all([
        loadJson(`${basePath}/latest.json`),
        loadJsonl(`${basePath}/documents.jsonl`),
        loadOptionalJsonl(`${basePath}/document_versions.jsonl`),
        loadOptionalJsonl(`${basePath}/meetings.jsonl`),
        loadOptionalJsonl(`${basePath}/meeting_items.jsonl`),
        loadOptionalJsonl(`${basePath}/meeting_documents.jsonl`),
        loadOptionalJsonl(`${basePath}/meeting_item_documents.jsonl`),
        loadOptionalJsonl(`${basePath}/organization_groups.jsonl`),
        loadOptionalJsonl(`${basePath}/organization_persons.jsonl`),
        loadOptionalJsonl(`${basePath}/organization_roles.jsonl`),
        loadOptionalJsonl(`${basePath}/organization_positions.jsonl`),
        loadOptionalJsonl(`${basePath}/organization_group_memberships.jsonl`),
    ]);
    return {
        latest,
        documents,
        documentVersions,
        meetings,
        agendaItems,
        meetingDocumentRelations,
        meetingItemDocumentRelations,
        organizationGroups,
        organizationPersons,
        organizationRoles,
        organizationPositions,
        organizationGroupMemberships,
    };
}
//# sourceMappingURL=loaders.js.map