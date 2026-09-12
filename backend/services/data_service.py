import os
import re
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any
from backend.config import settings

COLUMN_ALIASES = {
    'accidents': ['accidents', 'no. of accidents', 'total accidents', 'accident count', 'accident_count'],
    'fatalities': ['fatalities', 'deaths', 'persons killed', 'killed', 'fatal_count', 'death_count'],
    'injuries': ['injuries', 'persons injured', 'injured', 'injury_count'],
    'state': ['state', 'state/ut', 'state_name'],
    'district': ['district', 'district_name', 'district / city'],
    'city': ['city', 'town'],
    'road_name': ['road_name', 'road', 'corridor', 'location', 'highway_name'],
    'road_segment': ['road_segment', 'segment', 'stretch', 'location_detail'],
    'latitude': ['latitude', 'lat'],
    'longitude': ['longitude', 'lon', 'long'],
    'year': ['year', 'incident_year'],
    'month': ['month', 'incident_month'],
    'day': ['day', 'incident_day'],
    'hour': ['hour', 'time_hour', 'time'],
    'road_category': ['road_category', 'category', 'road_type'],
    'cause': ['cause', 'cause of accident', 'accident_cause', 'primary_cause'],
    'vehicle_type': ['vehicle_type', 'mode of transport', 'vehicle', 'vehicle_category'],
    'road_user_type': ['road_user_type', 'user_type', 'vru_type'],
    'weather': ['weather', 'weather_condition'],
    'road_condition': ['road_condition', 'surface_condition'],
    'lighting_condition': ['lighting_condition', 'light_condition', 'lighting'],
    'traffic_level': ['traffic_level', 'traffic_density']
}

def slugify_location(name: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '-', name).strip('-').lower()
    return f'loc-{cleaned[:32]}'

class DataService:
    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._is_demo: bool = False
        self._mode: str = 'unavailable'
        self._current_file: Optional[str] = None
        self._status: Dict[str, Any] = {'mode': 'unavailable', 'message': 'Official dataset not loaded.', 'required_files': ['data/raw/morth_accidents.csv']}
        self._load_available_data()

    def _load_available_data(self) -> None:
        processed = os.path.join(settings.PROCESSED_DATA_DIR, 'state_year_summary.csv')
        raw_files = sorted(name for name in os.listdir(settings.OFFICIAL_RAW_DIR) if name.lower().endswith('.csv')) if os.path.isdir(settings.OFFICIAL_RAW_DIR) else []
        if os.path.exists(processed):
            self._df = pd.read_csv(processed)
            self._mode = 'official'
            self._current_file = processed
            self._status = {'status': 'ready', 'mode': 'official', 'data': 'OFFICIAL', 'records': len(self._df), 'years': sorted(self._df['year'].dropna().astype(int).unique().tolist()), 'regions': int(self._df['state'].nunique()), 'sources_loaded': raw_files, 'source_count': len(raw_files), 'processed': True, 'cause_data': os.path.exists(os.path.join(settings.PROCESSED_DATA_DIR, 'cause_analysis.csv')), 'vulnerability_data': os.path.exists(os.path.join(settings.PROCESSED_DATA_DIR, 'vulnerability_analysis.csv'))}
        elif raw_files:
            self._mode = 'official_pending_processing'
            self._status = {'status': 'not_processed', 'mode': self._mode, 'message': 'Official CSV files found. Run python -m backend.data_pipeline.process_data.', 'sources_loaded': raw_files, 'source_count': len(raw_files), 'processed': False}
        elif settings.ALLOW_DEMO_DATA and os.path.exists(settings.DEMO_DATA_PATH):
            self.load_data(settings.DEMO_DATA_PATH, is_upload=False)
            self._mode = 'demo'
            self._is_demo = True
            self._status = {'status': 'ready', 'mode': 'demo', 'message': 'Explicit demo mode enabled.', 'records': len(self._df), 'processed': True}
        else:
            self._df = pd.DataFrame()
            self._status = {'status': 'unavailable', 'mode': 'unavailable', 'message': 'Official dataset not loaded.', 'required_files': ['one or more data/raw/*.csv files'], 'source_count': 0, 'processed': False}

    def load_data(self, file_path: Optional[str] = None, is_upload: bool = False) -> Dict[str, Any]:
        target_path = file_path or settings.DEMO_DATA_PATH
        if not os.path.exists(target_path):
            raise FileNotFoundError(f'Data file not found at {target_path}')

        raw_df = pd.read_csv(target_path)
        mapped_df, mapping_report = self._normalize_columns(raw_df)
        cleaned_df = self._clean_and_enrich(mapped_df)

        self._df = cleaned_df
        self._is_demo = not is_upload and settings.ALLOW_DEMO_DATA
        self._mode = 'demo' if self._is_demo else 'upload'
        self._current_file = target_path

        return {
            'total_records': len(cleaned_df),
            'columns_mapped': mapping_report['mapped'],
            'missing_optional': mapping_report['missing_optional'],
            'is_demo': self._is_demo
        }

    def _normalize_columns(self, df: pd.DataFrame) -> (pd.DataFrame, Dict[str, Any]):
        normalized_cols = {}
        mapped = {}
        missing_optional = []

        lower_cols = {str(col).strip().lower(): col for col in df.columns}

        for canonical, aliases in COLUMN_ALIASES.items():
            matched = None
            for alias in aliases:
                if alias in lower_cols:
                    matched = lower_cols[alias]
                    break
            if matched:
                normalized_cols[matched] = canonical
                mapped[matched] = canonical
            else:
                missing_optional.append(canonical)

        renamed_df = df.rename(columns=normalized_cols)
        return renamed_df, {'mapped': mapped, 'missing_optional': missing_optional}

    def _clean_and_enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df.drop_duplicates().reset_index(drop=True)

        # Required defaults
        if 'accidents' not in df.columns:
            df['accidents'] = 1
        else:
            df['accidents'] = pd.to_numeric(df['accidents'], errors='coerce').fillna(1).astype(int)

        if 'fatalities' not in df.columns:
            df['fatalities'] = 0
        else:
            df['fatalities'] = pd.to_numeric(df['fatalities'], errors='coerce').fillna(0).astype(int)

        if 'injuries' not in df.columns:
            df['injuries'] = 0
        else:
            df['injuries'] = pd.to_numeric(df['injuries'], errors='coerce').fillna(0).astype(int)

        # Categoricals
        for col in ['state', 'district', 'city', 'road_name', 'road_segment', 'road_category', 'cause', 'vehicle_type', 'weather', 'road_condition', 'lighting_condition', 'traffic_level']:
            if col not in df.columns:
                df[col] = 'Unknown'
            else:
                df[col] = df[col].fillna('Unknown').astype(str).str.strip()

        # Numerics
        if 'year' not in df.columns:
            df['year'] = 2023
        else:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(2023).astype(int)

        if 'month' not in df.columns:
            df['month'] = 1
        else:
            df['month'] = pd.to_numeric(df['month'], errors='coerce').fillna(1).astype(int)

        if 'hour' not in df.columns:
            df['hour'] = 12
        else:
            df['hour'] = pd.to_numeric(df['hour'], errors='coerce').fillna(12).astype(int)

        # Coordinates
        if 'latitude' not in df.columns:
            df['latitude'] = 20.5937
        else:
            df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce').fillna(20.5937)

        if 'longitude' not in df.columns:
            df['longitude'] = 78.9629
        else:
            df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce').fillna(78.9629)

        # Assign location ID
        df['location_id'] = (df['road_name'].fillna('Unknown road') + '|' + df['road_segment'].fillna('Unknown segment')).apply(slugify_location)

        # VRU Classification
        vru_keywords = {'two-wheeler', 'pedestrian', 'bicycle', 'auto-rickshaw', 'cycle', 'scooter', 'bike', 'motorcycle'}
        if 'road_user_type' not in df.columns or df['road_user_type'].nunique() <= 1:
            df['road_user_type'] = df['vehicle_type'].apply(
                lambda v: 'Vulnerable Road User (VRU)' if any(k in str(v).lower() for k in vru_keywords) else 'Other Road User'
            )

        return df

    def get_df(self) -> pd.DataFrame:
        if self._df is None:
            self._load_available_data()
        return self._df

    def is_demo(self) -> bool:
        return self._is_demo

    def mode(self) -> str:
        return self._mode

    def status(self) -> Dict[str, Any]:
        return self._status

    def get_corridors_summary(self) -> pd.DataFrame:
        df = self.get_df()
        grouped = df.groupby('location_id').agg(
            road_name=('road_name', 'first'),
            road_segment=('road_segment', 'first'),
            state=('state', 'first'),
            district=('district', 'first'),
            city=('city', 'first'),
            road_category=('road_category', 'first'),
            latitude=('latitude', 'mean'),
            longitude=('longitude', 'mean'),
            total_records=('id', 'count') if 'id' in df.columns else ('road_name', 'count'),
            total_accidents=('accidents', 'sum'),
            total_fatalities=('fatalities', 'sum'),
            total_injuries=('injuries', 'sum')
        ).reset_index()
        return grouped

    def get_filter_options(self) -> Dict[str, List[str]]:
        df = self.get_df()
        return {
            'states': sorted([str(s) for s in df['state'].unique() if str(s) != 'Unknown']),
            'districts': sorted([str(d) for d in df['district'].unique() if str(d) != 'Unknown']),
            'road_categories': sorted([str(c) for c in df['road_category'].unique() if str(c) != 'Unknown']),
            'causes': sorted([str(c) for c in df['cause'].unique() if str(c) != 'Unknown']),
            'vehicle_types': sorted([str(v) for v in df['vehicle_type'].unique() if str(v) != 'Unknown'])
        }

data_service = DataService()
