import json
from pathlib import Path

from backend.config import settings
from backend.data_pipeline.source_registry import discover_sources, source_profile


def inspect_raw_data() -> dict:
    profile = {}
    for path in discover_sources():
        try:
            profile[path.name] = {**source_profile(path), 'status': 'inspected'}
        except Exception as error:
            profile[path.name] = {'filename': path.name, 'status': 'error', 'error': str(error), 'source_type': 'official_csv'}
    output = Path(settings.METADATA_DIR)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'data_profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
    return profile


if __name__ == '__main__':
    print(json.dumps(inspect_raw_data(), indent=2))
