import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any

ROAD_CATEGORY_MAP = {
    'Urban Arterial': 0,
    'State Highway': 1,
    'National Highway': 2,
    'Ring Road': 3,
    'Expressway': 4
}

FEATURE_NAMES = [
    'accident_count',
    'fatality_rate',
    'injury_rate',
    'vru_ratio',
    'night_ratio',
    'speed_ratio',
    'bad_surface_ratio',
    'unlit_ratio',
    'weather_hazard_ratio',
    'road_category_code'
]

def extract_corridor_features(corridor_df: pd.DataFrame) -> Dict[str, float]:
    total_acc = max(int(corridor_df['accidents'].sum()), 1)
    total_rec = max(len(corridor_df), 1)
    fatalities = int(corridor_df['fatalities'].sum())
    injuries = int(corridor_df['injuries'].sum())
    
    vru_users = {'two-wheeler', 'pedestrian', 'bicycle', 'auto-rickshaw'}
    vru_count = corridor_df['vehicle_type'].apply(lambda v: str(v).lower() in vru_users).sum()
    night_count = corridor_df['hour'].apply(lambda h: h >= 21 or h <= 4).sum()
    speed_count = corridor_df['cause'].apply(lambda c: 'overspeed' in str(c).lower()).sum()
    bad_surface = corridor_df['road_condition'].apply(lambda r: 'damage' in str(r).lower() or 'pothole' in str(r).lower()).sum()
    unlit_count = corridor_df['lighting_condition'].apply(lambda l: 'unlit' in str(l).lower() or 'poor' in str(l).lower()).sum()
    weather_hazard = corridor_df['weather'].apply(lambda w: str(w).lower() in ['rain', 'fog/mist', 'dust storm']).sum()
    
    cat_str = str(corridor_df['road_category'].iloc[0]) if not corridor_df.empty else 'National Highway'
    cat_code = ROAD_CATEGORY_MAP.get(cat_str, 2)
    
    return {
        'accident_count': float(total_acc),
        'fatality_rate': round(fatalities / total_acc, 4),
        'injury_rate': round(injuries / total_acc, 4),
        'vru_ratio': round(vru_count / total_rec, 4),
        'night_ratio': round(night_count / total_rec, 4),
        'speed_ratio': round(speed_count / total_rec, 4),
        'bad_surface_ratio': round(bad_surface / total_rec, 4),
        'unlit_ratio': round(unlit_count / total_rec, 4),
        'weather_hazard_ratio': round(weather_hazard / total_rec, 4),
        'road_category_code': float(cat_code)
    }

def build_training_dataset(df: pd.DataFrame, risk_calculator) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    X_list = []
    y_list = []
    
    # Slice by corridor and year/quarter to generate genuine time-series training rows
    for loc_id, loc_group in df.groupby('location_id'):
        for yr, yr_group in loc_group.groupby('year'):
            if len(yr_group) < 3:
                continue
            feats = extract_corridor_features(yr_group)
            risk_info = risk_calculator(loc_id, yr_group)
            
            x_vec = [feats[name] for name in FEATURE_NAMES]
            y_val = risk_info['risk_score']
            
            X_list.append(x_vec)
            y_list.append(y_val)
            
    return np.array(X_list), np.array(y_list), FEATURE_NAMES
