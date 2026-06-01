from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml


def parse_ids(value: str | None) -> list[int]:
    if not value:
        return []
    ids: list[int] = []
    for part in value.split(','):
        part = part.strip()
        if not part:
            continue
        ids.append(int(part))
    return ids


def unique_ordered(values: list[int]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def load_base_url(municipality: str, config_dir: Path = Path('config/municipalities')) -> str:
    config_path = config_dir / f'{municipality}.yml'
    if not config_path.exists():
        raise FileNotFoundError(f'Municipality config not found: {config_path}')
    config = yaml.safe_load(config_path.read_text(encoding='utf-8')) or {}

    def find_base_url(value: Any) -> str | None:
        if isinstance(value, dict):
            if isinstance(value.get('base_url'), str):
                return value['base_url']
            for child in value.values():
                found = find_base_url(child)
                if found:
                    return found
        if isinstance(value, list):
            for child in value:
                found = find_base_url(child)
                if found:
                    return found
        return None

    base_url = find_base_url(config)
    if not base_url:
        raise ValueError(f'No base_url found in {config_path}')
    return base_url.rstrip('/') + '/'


def result_object(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get('result', {})
    return result if isinstance(result, dict) else {}


def list_from_result(payload: dict[str, Any], preferred_key: str | None = None) -> list[dict[str, Any]]:
    result = result_object(payload)
    if preferred_key and isinstance(result.get(preferred_key), list):
        return [item for item in result[preferred_key] if isinstance(item, dict)]
    for value in result.values():
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def response_shape(payload: dict[str, Any]) -> str:
    result = payload.get('result')
    if isinstance(result, dict):
        if any(isinstance(value, list) for value in result.values()):
            return 'object.result.object_with_list'
        return 'object.result.object'
    if isinstance(result, list):
        return 'object.result.list'
    return 'object'


def classify_payload(payload: dict[str, Any]) -> tuple[str, list[str], list[str], int | None, list[int]]:
    result = result_object(payload)
    records = list_from_result(payload)
    sample_keys = list(records[0].keys()) if records else []
    sample_ids = [record['id'] for record in records if isinstance(record.get('id'), int)]
    sample_count: int | None = len(records) if records else 0
    return response_shape(payload), list(result.keys()), sample_keys, sample_count, sample_ids


def total_count(payload: dict[str, Any]) -> str | None:
    value = result_object(payload).get('totalCount')
    return None if value is None else str(value)


def probe(
    session: requests.Session,
    base_url: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    url = base_url.rstrip('/') + '/' + path.lstrip('/')
    try:
        response = session.get(url, params=params, timeout=timeout)
        status_code = response.status_code
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError(f'Expected JSON object, got {type(payload).__name__}')
        shape, result_keys, sample_keys, sample_count, sample_ids = classify_payload(payload)
        records = list_from_result(payload)
        return {
            'path': path,
            'url': response.url,
            'ok': True,
            'status_code': status_code,
            'error': None,
            'response_shape': shape,
            'result_keys': result_keys,
            'sample_keys': sample_keys,
            'sample_count': sample_count,
            'sample_ids': sample_ids,
            'total_count': total_count(payload),
            'sample_records': records[:3],
            '_payload': payload,
        }
    except Exception as exc:  # noqa: BLE001 - discovery should capture failures as data
        return {
            'path': path,
            'url': url,
            'ok': False,
            'status_code': getattr(getattr(exc, 'response', None), 'status_code', None),
            'error': f'{type(exc).__name__}: {exc}',
            'response_shape': None,
            'result_keys': [],
            'sample_keys': [],
            'sample_count': None,
            'sample_ids': [],
            'total_count': None,
            'sample_records': [],
            '_payload': None,
        }


def public_probe(probe_result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in probe_result.items() if key != '_payload'}


def meeting_ids_from_meetingsessions(records: list[dict[str, Any]]) -> list[int]:
    ids: list[int] = []
    for record in records:
        container = record.get('container')
        if not isinstance(container, dict):
            continue
        meeting = container.get('meeting')
        if not isinstance(meeting, dict):
            continue
        meeting_id = meeting.get('id')
        if isinstance(meeting_id, int):
            ids.append(meeting_id)
    return unique_ordered(ids)


def discover_relations(
    *,
    municipality: str,
    base_url: str,
    meeting_limit: int = 3,
    item_limit: int = 10,
    scan_limit: int = 100,
    manual_meeting_ids: list[int] | None = None,
) -> dict[str, Any]:
    session = requests.Session()
    probes: list[dict[str, Any]] = []

    meetings_probe = probe(session, base_url, 'meetings', params={'limit': meeting_limit, 'offset': 0})
    dmus_probe = probe(session, base_url, 'dmus', params={'limit': 10, 'offset': 0})
    events_probe = probe(session, base_url, 'events', params={'limit': 3, 'offset': 0})
    sessions_probe = probe(session, base_url, 'meetingsessions', params={'limit': scan_limit, 'offset': 0})
    probes.extend([meetings_probe, dmus_probe, events_probe, sessions_probe])

    recent_meeting_ids = meetings_probe.get('sample_ids', []) if meetings_probe.get('ok') else []
    meetingsession_records = list_from_result(sessions_probe.get('_payload') or {}, 'meetingsessions')
    session_meeting_ids = meeting_ids_from_meetingsessions(meetingsession_records)

    if manual_meeting_ids:
        meeting_selection_source = 'manual'
        candidate_meeting_ids = unique_ordered(manual_meeting_ids)
    else:
        meeting_selection_source = 'recent_meetings_plus_meetingsessions'
        candidate_meeting_ids = unique_ordered([*recent_meeting_ids, *session_meeting_ids])

    sampled_meeting_item_ids: list[int] = []
    populated_meetings: list[dict[str, Any]] = []

    for meeting_id in candidate_meeting_ids:
        detail = probe(session, base_url, f'meetings/{meeting_id}')
        documents = probe(
            session,
            base_url,
            f'meetings/{meeting_id}/documents',
            params={'limit': item_limit, 'offset': 0},
        )
        items = probe(
            session,
            base_url,
            f'meetings/{meeting_id}/meetingitems',
            params={'limit': item_limit, 'offset': 0},
        )
        probes.extend([detail, documents, items])

        item_records = list_from_result(items.get('_payload') or {}, 'meetingitems')
        document_records = list_from_result(documents.get('_payload') or {}, 'documents')
        item_ids = [item['id'] for item in item_records if isinstance(item.get('id'), int)]
        sampled_meeting_item_ids.extend(item_ids)

        if item_records or document_records:
            populated_meetings.append(
                {
                    'meeting_id': meeting_id,
                    'meeting_detail_ok': bool(detail.get('ok')),
                    'meetingitems_count': len(item_records),
                    'documents_count': len(document_records),
                    'sample_meetingitem_keys': list(item_records[0].keys()) if item_records else [],
                    'sample_document_keys': list(document_records[0].keys()) if document_records else [],
                    'sample_meetingitem_ids': item_ids[:item_limit],
                    'sample_document_ids': [doc['id'] for doc in document_records if isinstance(doc.get('id'), int)][:item_limit],
                }
            )

    for meeting_item_id in unique_ordered(sampled_meeting_item_ids)[:item_limit]:
        probes.append(probe(session, base_url, f'meetingitems/{meeting_item_id}'))
        probes.append(
            probe(
                session,
                base_url,
                f'meetingitems/{meeting_item_id}/documents',
                params={'limit': item_limit, 'offset': 0},
            )
        )

    public_probes = [public_probe(item) for item in probes]
    working_paths = [item['path'] for item in public_probes if item.get('ok')]

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'municipality': municipality,
        'base_url': base_url,
        'meeting_limit': meeting_limit,
        'item_limit': item_limit,
        'scan_limit': scan_limit,
        'manual_meeting_ids': manual_meeting_ids or [],
        'summary': {
            'meeting_selection_source': meeting_selection_source,
            'sampled_meeting_ids': candidate_meeting_ids,
            'recent_meeting_ids': recent_meeting_ids,
            'meetingsession_meeting_ids': session_meeting_ids,
            'sampled_meeting_item_ids': unique_ordered(sampled_meeting_item_ids),
            'working_path_count': len(working_paths),
            'working_paths': working_paths,
            'meeting_items_discovered': len(unique_ordered(sampled_meeting_item_ids)),
            'populated_meeting_count': len(populated_meetings),
            'populated_meetings': populated_meetings,
        },
        'probes': public_probes,
        'notes': [
            'This report uses documented nested routes and a small number of sampled meetings.',
            'Manual meeting IDs can be supplied to probe known meetings with likely agenda items or documents.',
            'When manual IDs return 404 on /meetings/{id}, they are likely not meeting IDs.',
            'meetingsessions can expose historical meeting IDs through container.meeting.id.',
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Discover GemeenteOplossingen meeting relation endpoints.')
    parser.add_argument('--municipality', default='huizen')
    parser.add_argument('--base-url', default='')
    parser.add_argument('--meeting-limit', type=int, default=3)
    parser.add_argument('--item-limit', type=int, default=10)
    parser.add_argument('--scan-limit', type=int, default=100)
    parser.add_argument('--meeting-ids', default='')
    parser.add_argument('--output-path', default='data/public/quality/gemeenteoplossingen_relation_discovery.json')
    args = parser.parse_args()

    base_url = args.base_url.rstrip('/') + '/' if args.base_url else load_base_url(args.municipality)
    report = discover_relations(
        municipality=args.municipality,
        base_url=base_url,
        meeting_limit=args.meeting_limit,
        item_limit=args.item_limit,
        scan_limit=args.scan_limit,
        manual_meeting_ids=parse_ids(args.meeting_ids),
    )

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
