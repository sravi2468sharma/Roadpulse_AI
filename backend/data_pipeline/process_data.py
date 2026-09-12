import json
import re
from pathlib import Path

import pandas as pd

from backend.config import settings
from backend.data_pipeline.normalization import clean_header
from backend.data_pipeline.source_registry import discover_sources, source_profile
from backend.data_pipeline.validate import validate_frame


def _state_column(columns):
    return next((column for column in columns if clean_header(column) in {'states uts', 'state', 'state ut', 'state name'} or 'states uts' in clean_header(column)), None)


def _year_columns(columns):
    return [(column, int(match.group(1))) for column in columns if (match := re.search(r'(20\d{2})', str(column)))]


def _numeric(series):
    return pd.to_numeric(series.astype(str).str.replace(',', '', regex=False).str.replace('-', '', regex=False), errors='coerce')


def _process_accident_totals(frame, path, profile):
    state_column = _state_column(frame.columns)
    year_columns = _year_columns(frame.columns)
    if not state_column or not year_columns:
        return pd.DataFrame()
    rows = []
    for _, source_row in frame.iterrows():
        state = str(source_row[state_column]).strip()
        if not state or state.lower() in {'total', 'india', 'nan'}:
            continue
        for column, year in year_columns:
            if 'accident' not in clean_header(column) and str(column).strip() != str(year):
                continue
            value = _numeric(pd.Series([source_row[column]])).iloc[0]
            if pd.notna(value):
                rows.append({'state': state, 'year': year, 'accidents': float(value), 'source_file': path.name, 'source_type': profile['likely_dataset_category'], 'source_name': 'Official Government CSV', 'source_url': profile['source_url'], 'source_year': year, 'source_granularity': profile['source_granularity']})
    return pd.DataFrame(rows)


def _process_road_classification(frame, path, profile):
    state_column = _state_column(frame.columns)
    if not state_column:
        return pd.DataFrame()
    rows = []
    for column in frame.columns:
        header = clean_header(column)
        if 'total number of accidents' not in header and 'total accidents' not in header:
            continue
        category = str(column).split(' - ')[0].strip()
        for _, source_row in frame.iterrows():
            value = _numeric(pd.Series([source_row[column]])).iloc[0]
            if pd.notna(value):
                rows.append({'state': str(source_row[state_column]).strip(), 'year': 2019, 'road_category': category, 'accidents': float(value), 'source_file': path.name, 'source_type': profile['likely_dataset_category'], 'source_name': 'Official Government CSV', 'source_url': profile['source_url'], 'source_year': 2019, 'source_granularity': profile['source_granularity']})
    return pd.DataFrame(rows)


def _process_national_mode(frame, path, profile):
    columns = {clean_header(column): column for column in frame.columns}
    mode = columns.get('mode of transport')
    injured = next((column for key, column in columns.items() if 'involved mode of transport injured' in key), None)
    died = next((column for key, column in columns.items() if 'involved mode of transport died' in key), None)
    injured_share = columns.get('percentage share of injured')
    death_share = columns.get('percentage share of deaths')
    if not all((mode, injured, died, injured_share, death_share)):
        return pd.DataFrame()
    result = pd.DataFrame({'mode': frame[mode].astype(str).str.strip(), 'injured': _numeric(frame[injured]), 'died': _numeric(frame[died]), 'injured_share': _numeric(frame[injured_share]), 'death_share': _numeric(frame[death_share])})
    result = result[~result['mode'].str.lower().str.contains('total|grand total', regex=True)].dropna(subset=['mode'])
    result['year'] = 2023; result['scope'] = 'India'; result['aggregation_level'] = 'All-India aggregate'; result['source_file'] = path.name; result['source_type'] = profile['likely_dataset_category']; result['source_name'] = 'NCRB ADSI 2023 Table 1A.3_2'; result['source_url'] = profile['source_url']
    return result


def _process_national_cause(frame, path, profile):
    columns = {clean_header(column): column for column in frame.columns}
    cause = columns.get('cause'); cases = columns.get('number of cases'); injured = columns.get('persons injured total'); died = columns.get('persons died total'); share = columns.get('percentage share cases')
    if not all((cause, cases, injured, died, share)):
        return pd.DataFrame()
    result = pd.DataFrame({'cause': frame[cause].astype(str).str.strip(), 'cases': _numeric(frame[cases]), 'injured': _numeric(frame[injured]), 'died': _numeric(frame[died]), 'share_cases': _numeric(frame[share])})
    result = result[~result['cause'].str.lower().str.contains('total|grand total', regex=True)].dropna(subset=['cause'])
    result['year'] = 2023; result['scope'] = 'India'; result['aggregation_level'] = 'All-India aggregate'; result['source_file'] = path.name; result['source_type'] = profile['likely_dataset_category']; result['source_name'] = 'NCRB ADSI 2023 Table 1A.8'; result['source_url'] = profile['source_url']
    return result


def process_official_data() -> dict:
    output = Path(settings.PROCESSED_DATA_DIR)
    output.mkdir(parents=True, exist_ok=True)
    profiles = {}
    state_rows, classification_rows, national_modes, national_causes = [], [], [], []
    for path in discover_sources():
        try:
            frame = pd.read_csv(path)
            profile = source_profile(path)
            profiles[path.name] = {**profile, 'status': 'processed'}
            role = profile['likely_dataset_category']
            if role in {'accident_totals', 'historical_time_series'}:
                processed = _process_accident_totals(frame, path, profile)
                if not processed.empty:
                    state_rows.append(processed)
            elif role == 'road_classification':
                processed = _process_road_classification(frame, path, profile)
                if not processed.empty:
                    classification_rows.append(processed)
            elif role == 'mode_of_transport':
                processed = _process_national_mode(frame, path, profile)
                if not processed.empty: national_modes.append(processed)
            elif role == 'cause_wise':
                processed = _process_national_cause(frame, path, profile)
                if not processed.empty: national_causes.append(processed)
        except Exception as error:
            profiles[path.name] = {'filename': path.name, 'status': 'error', 'error': str(error), 'source_type': 'official_csv'}

    state_frame = pd.concat(state_rows, ignore_index=True) if state_rows else pd.DataFrame()
    if not state_frame.empty:
        state_frame = state_frame.drop_duplicates(subset=['state', 'year', 'accidents', 'source_file'])
        state_frame.to_csv(output / 'state_year_summary.csv', index=False)
        state_frame.to_csv(output / 'accident_master.csv', index=False)
        validation = validate_frame(state_frame)
    else:
        validation = {'rows': 0, 'valid': False, 'message': 'No compatible accident-total rows found'}
    if classification_rows:
        pd.concat(classification_rows, ignore_index=True).to_csv(output / 'road_category_summary.csv', index=False)
    if national_modes:
        pd.concat(national_modes, ignore_index=True).to_csv(output / 'vulnerability_analysis.csv', index=False)
    if national_causes:
        pd.concat(national_causes, ignore_index=True).to_csv(output / 'cause_analysis.csv', index=False)
    (output / 'validation_report.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')
    metadata = Path(settings.METADATA_DIR)
    metadata.mkdir(parents=True, exist_ok=True)
    (metadata / 'data_profile.json').write_text(json.dumps(profiles, indent=2), encoding='utf-8')
    report = {'processed_at': pd.Timestamp.now('UTC').isoformat(), 'source_count': len(profiles), 'successful_sources': sum(value.get('status') == 'processed' for value in profiles.values()), 'state_year_rows': len(state_frame), 'road_classification_rows': sum(len(item) for item in classification_rows), 'cause_rows': sum(len(item) for item in national_causes), 'vulnerability_rows': sum(len(item) for item in national_modes)}
    (metadata / 'processing_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return {'profiles': profiles, **report, 'processed': not state_frame.empty}


if __name__ == '__main__':
    print(json.dumps(process_official_data(), indent=2))
