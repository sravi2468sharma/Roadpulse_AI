from pathlib import Path
from typing import Dict, Any
import re

import pandas as pd

from backend.config import settings
from backend.data_pipeline.normalize import clean_header


def detect_role(columns: list[str], filename: str) -> str:
    headers = ' '.join(clean_header(column) for column in columns)
    name = filename.lower()
    if 'junction' in headers or 'junction' in name or 'road feature' in headers:
        return 'road_classification'
    if 'mode of transport' in headers or 'road user' in headers or 'vehicle type' in headers:
        return 'mode_of_transport'
    if 'cause' in headers or 'reason' in headers:
        return 'cause_analysis'
    if any(str(year) in columns for year in range(2000, 2031)) and ('states/uts' in headers or 'state' in headers):
        return 'historical_time_series'
    if 'accidents' in headers and any(str(year) in headers for year in range(2000, 2031)):
        return 'accident_totals' if '2019' in headers or 'total number' in headers else 'historical_time_series'
    if 'accidents' in headers:
        return 'accident_totals'
    return 'unclassified_official'


def source_profile(path: Path) -> Dict[str, Any]:
    frame = pd.read_csv(path, nrows=1000)
    columns = list(frame.columns)
    headers = ' '.join(clean_header(column) for column in columns)
    years = sorted({int(year) for year in __import__('re').findall(r'20\d{2}', headers)})
    recognized = []
    aliases = {
        'state': ('state', 'states/uts'), 'city': ('city', 'cities'), 'year': ('year', 'years'),
        'accidents': ('accidents', 'total number of road accidents'), 'fatalities': ('persons killed', 'fatalities', 'deaths'),
        'injuries': ('persons injured', 'injuries'), 'cause': ('cause', 'causes'), 'road_user': ('mode of transport', 'road user', 'vehicle type'),
        'road_category': ('road category', 'junction', 'road feature'),
    }
    for field, candidates in aliases.items():
        if any(candidate in headers for candidate in candidates):
            recognized.append(field)
    if re.search(r'\b20\d{2}\b', headers):
        recognized.append('year')
    role = detect_role(columns, path.name)
    if role == 'historical_time_series' and 'accidents' not in recognized:
        recognized.append('accidents')
    return {
        'filename': path.name,
        'rows': int(len(pd.read_csv(path))),
        'columns': columns,
        'detected_years': years,
        'year_range': [min(years), max(years)] if years else [],
        'likely_dataset_category': role,
        'recognized_fields': recognized,
        'missing_fields': sorted(set(aliases) - set(recognized)),
        'source_type': 'official_csv',
        'source_file': path.name,
        'source_url': 'https://www.data.gov.in/catalog/road-accidents-india-2019',
        'source_granularity': 'State/UT' if 'states/uts' in headers or 'state' in headers else 'unknown',
    }


def discover_sources() -> list[Path]:
    return sorted(Path(settings.OFFICIAL_RAW_DIR).glob('*.csv'))
