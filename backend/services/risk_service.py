import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.services.data_service import data_service

class RiskScoreEngine:
    WEIGHT_SEVERITY_FREQ = 35.0
    WEIGHT_VRU_EXPOSURE = 20.0
    WEIGHT_HAZARD_CAUSES = 20.0
    WEIGHT_TEMPORAL_NIGHT = 15.0
    WEIGHT_TREND_TRAJECTORY = 10.0

    SEVERITY_WEIGHT_ACCIDENT = 1.0
    SEVERITY_WEIGHT_INJURY = 3.0
    SEVERITY_WEIGHT_FATALITY = 5.0

    HIGH_HAZARD_CAUSES = {
        'overspeeding', 'drunk driving', 'poor lighting',
        'potholes / road surface defect', 'wrong-side driving',
        'dangerous junction geometry'
    }

    VRU_USERS = {'two-wheeler', 'pedestrian', 'bicycle', 'auto-rickshaw'}

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_severity_benchmark = 150.0

    def classify_risk_level(self, score: float) -> str:
        if score >= 75.0:
            return 'Critical'
        elif score >= 50.0:
            return 'High'
        elif score >= 25.0:
            return 'Medium'
        else:
            return 'Low'

    def calculate_corridor_risk(self, location_id: str, corridor_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        if corridor_df is None:
            all_df = data_service.get_df()
            corridor_df = all_df[all_df['location_id'] == location_id]

        if corridor_df.empty:
            return {
                'risk_score': 0.0,
                'risk_level': 'Low',
                'severity_raw': 0.0,
                'component_scores': {},
                'contribution_breakdown': []
            }

        total_records = len(corridor_df)
        total_accidents = int(corridor_df['accidents'].sum())
        total_fatalities = int(corridor_df['fatalities'].sum())
        total_injuries = int(corridor_df['injuries'].sum())

        # 1. Severity Raw
        severity_raw = (
            total_accidents * self.SEVERITY_WEIGHT_ACCIDENT +
            total_injuries * self.SEVERITY_WEIGHT_INJURY +
            total_fatalities * self.SEVERITY_WEIGHT_FATALITY
        )

        # Dynamic max severity scaling benchmark based on corridor size
        benchmark = max(self._max_severity_benchmark, severity_raw * 1.1)
        severity_score = min(self.WEIGHT_SEVERITY_FREQ, (severity_raw / benchmark) * self.WEIGHT_SEVERITY_FREQ * 1.5)

        # 2. VRU Exposure
        vru_count = corridor_df.apply(
            lambda row: 'vulnerable' in str(row.get('road_user_type', '')).lower()
            or str(row.get('vehicle_type', '')).lower() in self.VRU_USERS,
            axis=1,
        ).sum()
        vru_ratio = vru_count / total_records if total_records > 0 else 0.0
        vru_score = vru_ratio * self.WEIGHT_VRU_EXPOSURE

        # 3. Hazardous Causes & Conditions
        hazard_count = corridor_df['cause'].apply(lambda c: str(c).lower() in self.HIGH_HAZARD_CAUSES).sum()
        hazard_ratio = hazard_count / total_records if total_records > 0 else 0.0
        hazard_score = hazard_ratio * self.WEIGHT_HAZARD_CAUSES

        # 4. Temporal Night Risk (21:00 to 04:00)
        night_count = corridor_df['hour'].apply(lambda h: h >= 21 or h <= 4).sum()
        night_ratio = night_count / total_records if total_records > 0 else 0.0
        temporal_score = night_ratio * self.WEIGHT_TEMPORAL_NIGHT

        # 5. Trend Trajectory (YoY growth)
        yearly_counts = corridor_df.groupby('year')['accidents'].sum().to_dict()
        years = sorted(yearly_counts.keys())
        if len(years) >= 2:
            first_half = yearly_counts.get(years[0], 1)
            last_half = yearly_counts.get(years[-1], 1)
            growth = (last_half - first_half) / max(first_half, 1)
            trend_score = min(self.WEIGHT_TREND_TRAJECTORY, max(0.0, (growth + 0.3) * 5.0))
        else:
            trend_score = 5.0

        # Total 0-100 bounded
        raw_total = severity_score + vru_score + hazard_score + temporal_score + trend_score
        final_risk_score = round(float(np.clip(raw_total, 0.0, 100.0)), 1)
        risk_level = self.classify_risk_level(final_risk_score)

        component_scores = {
            'severity_frequency': round(float(severity_score), 1),
            'vru_exposure': round(float(vru_score), 1),
            'hazard_causes': round(float(hazard_score), 1),
            'temporal_night': round(float(temporal_score), 1),
            'trend_trajectory': round(float(trend_score), 1)
        }

        contribution_breakdown = [
            {
                'name': 'Frequency & Fatal Severity',
                'score': component_scores['severity_frequency'],
                'max_score': self.WEIGHT_SEVERITY_FREQ,
                'weight_pct': round((component_scores['severity_frequency'] / max(final_risk_score, 1)) * 100, 1),
                'description': f'{total_accidents} accidents, {total_fatalities} deaths, {total_injuries} injuries'
            },
            {
                'name': 'Vulnerable Road User Exposure',
                'score': component_scores['vru_exposure'],
                'max_score': self.WEIGHT_VRU_EXPOSURE,
                'weight_pct': round((component_scores['vru_exposure'] / max(final_risk_score, 1)) * 100, 1),
                'description': f'{round(vru_ratio * 100, 1)}% involves two-wheelers, pedestrians or auto-rickshaws'
            },
            {
                'name': 'Hazardous Road Factors & Causes',
                'score': component_scores['hazard_causes'],
                'max_score': self.WEIGHT_HAZARD_CAUSES,
                'weight_pct': round((component_scores['hazard_causes'] / max(final_risk_score, 1)) * 100, 1),
                'description': f'{round(hazard_ratio * 100, 1)}% driven by overspeeding, lighting defects, or poor surfaces'
            },
            {
                'name': 'Temporal Night-time Clustering',
                'score': component_scores['temporal_night'],
                'max_score': self.WEIGHT_TEMPORAL_NIGHT,
                'weight_pct': round((component_scores['temporal_night'] / max(final_risk_score, 1)) * 100, 1),
                'description': f'{round(night_ratio * 100, 1)}% of incidents clustered between 21:00 and 04:00'
            },
            {
                'name': 'Historical Trend Trajectory',
                'score': component_scores['trend_trajectory'],
                'max_score': self.WEIGHT_TREND_TRAJECTORY,
                'weight_pct': round((component_scores['trend_trajectory'] / max(final_risk_score, 1)) * 100, 1),
                'description': 'Year-over-year corridor accident evolution trajectory'
            }
        ]

        return {
            'risk_score': final_risk_score,
            'risk_level': risk_level,
            'severity_raw': round(float(severity_raw), 1),
            'component_scores': component_scores,
            'contribution_breakdown': contribution_breakdown
        }

risk_engine = RiskScoreEngine()
