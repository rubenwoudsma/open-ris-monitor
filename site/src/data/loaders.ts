import type {
  AgendaItemRecord,
  DashboardExport,
  DocumentRecord,
  DocumentVersionRecord,
  LatestExport,
  MeetingRecord,
  OrganizationGroupMembershipRecord,
  OrganizationGroupRecord,
  OrganizationPersonRecord,
  OrganizationPositionRecord,
  OrganizationRoleRecord,
  PublicDataSet,
  RelationRecord,
} from "./types.js";
import { loadJson, loadJsonl, loadOptionalJson, loadOptionalJsonl } from "./jsonl.js";

export const DATA_BASE = "../data/public";

export async function loadPublicData(basePath = DATA_BASE): Promise<PublicDataSet> {
  const [
    latest,
    dashboard,
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
  ] = await Promise.all([
    loadJson<LatestExport>(`${basePath}/latest.json`),
    loadOptionalJson<DashboardExport>(`${basePath}/quality/dashboard.json`),
    loadJsonl<DocumentRecord>(`${basePath}/documents.jsonl`),
    loadOptionalJsonl<DocumentVersionRecord>(`${basePath}/document_versions.jsonl`),
    loadOptionalJsonl<MeetingRecord>(`${basePath}/meetings.jsonl`),
    loadOptionalJsonl<AgendaItemRecord>(`${basePath}/meeting_items.jsonl`),
    loadOptionalJsonl<RelationRecord>(`${basePath}/meeting_documents.jsonl`),
    loadOptionalJsonl<RelationRecord>(`${basePath}/meeting_item_documents.jsonl`),
    loadOptionalJsonl<OrganizationGroupRecord>(`${basePath}/organization_groups.jsonl`),
    loadOptionalJsonl<OrganizationPersonRecord>(`${basePath}/organization_persons.jsonl`),
    loadOptionalJsonl<OrganizationRoleRecord>(`${basePath}/organization_roles.jsonl`),
    loadOptionalJsonl<OrganizationPositionRecord>(`${basePath}/organization_positions.jsonl`),
    loadOptionalJsonl<OrganizationGroupMembershipRecord>(`${basePath}/organization_group_memberships.jsonl`),
  ]);

  return {
    latest,
    dashboard,
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
