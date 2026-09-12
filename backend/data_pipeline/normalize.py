import re
from typing import Dict, Iterable

import pandas as pd

ALIASES: Dict[str, Iterable[str]] = {
    'state': ('state', 'state/ut', 'states/uts', 'state name', 'state/ut name'),
    'city': ('city', 'cities', 'city name'),
    'year': ('year', 'years'),
    'accidents': ('accidents', 'total accidents', 'no. of accidents', 'number of road accidents', 'total number of road accidents'),
    'fatalities': ('deaths', 'fatalities', 'persons killed', 'number of persons killed', 'total persons killed'),
    'injuries': ('injuries', 'persons injured', 'number of persons injured', 'total persons injured'),
    'fatal_accidents': ('fatal accidents', 'fatal accidents total'),
    'cause': ('cause', 'cause of accident', 'causes'),
    'road_user': ('road user', 'road user category', 'mode of transport', 'vehicle type'),
    'road_category': ('road category', 'road type', 'category'),
}


def clean_header(value: object) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', str(value).strip().lower()).strip()


def normalize_columns(frame: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, str]]:
    lookup = {clean_header(column): column for column in frame.columns}
    rename: Dict[str, str] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            source = lookup.get(clean_header(alias))
            if source is not None:
                rename[source] = canonical
                break
    return frame.rename(columns=rename), {source: target for source, target in rename.items()}


def wide_state_year_to_long(frame: pd.DataFrame) -> pd.DataFrame:
    normalized, _ = normalize_columns(frame)
    state_column = 'state' if 'state' in normalized.columns else next((column for column in normalized.columns if 'state' in clean_header(column)), None)
    if state_column is None:
        raise ValueError('Official file must contain a State/UT column')
    year_columns = [column for column in normalized.columns if re.search(r'20\d{2}', str(column))]
    if not year_columns:
        return normalized
    rows = []
    for _, source_row in normalized.iterrows():
        for year_column in year_columns:
            match = re.search(r'(20\d{2})', str(year_column))
            if match:
                rows.append({'state': source_row[state_column], 'year': int(match.group(1)), 'accidents': source_row[year_column]})
    return pd.DataFrame(rows)
