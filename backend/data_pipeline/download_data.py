import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from backend.config import settings

SOURCES = {
    'morth_accidents': {
        'name': 'State/UT-wise Total Number of Road Accidents in India from 2016 to 2019',
        'organization': 'Ministry of Road Transport and Highways',
        'url': 'https://www.data.gov.in/resource/stateut-wise-total-number-road-accidents-india-2016-2019',
        'granularity': 'State/UT',
        'filename': 'morth_accidents.csv',
        'resource_env': 'DATA_GOV_RESOURCE_ACCIDENTS',
    },
    'cause_accidents': {
        'name': 'Road Accidents in India 2019 cause resources',
        'organization': 'Ministry of Road Transport and Highways',
        'url': 'https://www.data.gov.in/catalog/road-accidents-india-2019',
        'granularity': 'City/State where provided',
        'filename': 'cause_accidents.csv',
        'resource_env': 'DATA_GOV_RESOURCE_CAUSES',
    },
    'mode_transport': {
        'name': 'Accidental Deaths & Suicides in India (ADSI) 2023',
        'organization': 'National Crime Records Bureau',
        'url': 'https://www.data.gov.in/catalog/accidental-deaths-suicides-india-adsi-2023',
        'granularity': 'State/UT where provided',
        'filename': 'mode_transport.csv',
        'resource_env': 'DATA_GOV_RESOURCE_TRANSPORT',
    },
}


def download_configured_sources() -> Dict[str, str]:
    Path(settings.OFFICIAL_RAW_DIR).mkdir(parents=True, exist_ok=True)
    results = {}
    for source_id, metadata in SOURCES.items():
        target = Path(settings.OFFICIAL_RAW_DIR) / metadata['filename']
        if target.exists() and target.stat().st_size > 0:
            results[source_id] = 'cached'
            continue
        resource_id = getattr(settings, metadata['resource_env'])
        if not resource_id or not settings.DATA_GOV_API_KEY:
            results[source_id] = 'manual download required'
            continue
        params = urlencode({'api-key': settings.DATA_GOV_API_KEY, 'format': 'csv', 'limit': 10000})
        endpoint = f'https://api.data.gov.in/resource/{resource_id}?{params}'
        try:
            request = Request(endpoint, headers={'User-Agent': 'RoadPulse-AI/1.0'})
            with urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise URLError(f'HTTP {response.status}')
                target.write_bytes(response.read())
            results[source_id] = 'downloaded'
        except (OSError, URLError) as error:
            results[source_id] = f'error: {error}'
    metadata_path = Path(settings.METADATA_DIR)
    metadata_path.mkdir(parents=True, exist_ok=True)
    (metadata_path / 'retrieval.json').write_text(json.dumps({'retrieved_at': datetime.now(timezone.utc).isoformat(), 'results': results}, indent=2), encoding='utf-8')
    return results


if __name__ == '__main__':
    print(json.dumps(download_configured_sources(), indent=2))
