from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backend.config import settings
from backend.services.data_service import data_service


class OfficialService:
    def _frame(self) -> pd.DataFrame:
        return data_service.get_df().copy()

    def _risk(self, frame: pd.DataFrame) -> Dict[str, Any]:
        available = frame
        accidents = float(available['accidents'].sum()) if 'accidents' in available else None
        fatalities = float(available['fatalities'].sum()) if 'fatalities' in available else None
        injuries = float(available['injuries'].sum()) if 'injuries' in available else None
        components: Dict[str, float] = {}
        if accidents is not None:
            components['accident_frequency'] = accidents
        if fatalities is not None:
            components['fatality_burden'] = fatalities
        if injuries is not None:
            components['injury_burden'] = injuries
        score = 0.0
        if 'accidents' in available:
            latest_year = available['year'].max() if 'year' in available else None
            comparable = self._frame()
            if latest_year is not None:
                comparable = comparable[comparable['year'] == latest_year]
            maximum = max(float(comparable.groupby('state')['accidents'].sum().max()), 1.0)
            score = 100.0 * accidents / maximum
        normalized_components = {name: round(float(value), 1) for name, value in components.items()}
        return {'risk_score': round(float(np.clip(score, 0, 100)), 1), 'risk_level': self._level(score), 'components': normalized_components, 'component_scores': normalized_components, 'contribution_breakdown': [{'name': name.replace('_', ' ').title(), 'score': round(value, 1), 'max_score': 100, 'weight_pct': round(value / max(sum(normalized_components.values()), 1) * 100, 1), 'description': 'Observed official measure'} for name, value in normalized_components.items()], 'available_components': list(normalized_components), 'limitations': ['Official source does not provide road coordinates or hourly observations.']}

    @staticmethod
    def _level(score: float) -> str:
        return 'Critical' if score >= 75 else 'High' if score >= 50 else 'Medium' if score >= 25 else 'Low'

    def regions(self) -> List[Dict[str, Any]]:
        frame = self._frame()
        if frame.empty or 'state' not in frame:
            return []
        latest = int(frame['year'].max()) if 'year' in frame else None
        selected = frame[frame['year'] == latest] if latest is not None else frame
        result = []
        for state, group in selected.groupby('state'):
            risk = self._risk(group)
            result.append({'id': str(state), 'state': str(state), 'road_name': str(state), 'district': None, 'latitude': None, 'longitude': None, 'year': latest, 'accidents': int(group['accidents'].sum()) if 'accidents' in group else None, 'fatalities': int(group['fatalities'].sum()) if 'fatalities' in group else None, 'injuries': int(group['injuries'].sum()) if 'injuries' in group else None, **risk})
        return sorted(result, key=lambda item: item['risk_score'], reverse=True)

    def region(self, region_id: str) -> Dict[str, Any]:
        frame = self._frame()
        group = frame[frame['state'].astype(str) == str(region_id)]
        if group.empty:
            raise KeyError(region_id)
        latest = group[group['year'] == group['year'].max()] if 'year' in group else group
        item = next(item for item in self.regions() if item['id'] == str(region_id))
        trend = [{'year': int(year), 'accidents': int(rows['accidents'].sum())} for year, rows in group.groupby('year')] if 'year' in group and 'accidents' in group else []
        return {**item, 'risk': self._risk(latest), 'trend': trend, 'top_cause': None, 'top_user': None, 'peak_hour': None, 'causes': [], 'vulnerability': [], 'temporal': [], 'road_segment': None, 'explanation': f"{region_id} is ranked from official State/UT annual accident totals for {item['year']}. Cause, road-user, coordinate, and hourly fields are not asserted because they are absent from the loaded source."}

    def summary(self) -> Dict[str, Any]:
        frame = self._frame()
        regions = self.regions()
        latest = int(frame['year'].max()) if 'year' in frame and not frame.empty else None
        selected = frame[frame['year'] == latest] if latest is not None else frame
        critical = sum(item['risk_level'] == 'Critical' for item in regions)
        high = sum(item['risk_level'] == 'High' for item in regions)
        average = round(float(np.mean([item['risk_score'] for item in regions])), 1) if regions else None
        return {'data_mode': 'official', 'data_label': 'OFFICIAL GOVERNMENT DATA', 'source_granularity': 'State/UT', 'selected_year': latest, 'total_accidents': int(selected['accidents'].sum()) if 'accidents' in selected else None, 'total_fatalities': int(selected['fatalities'].sum()) if 'fatalities' in selected else None, 'total_injuries': int(selected['injuries'].sum()) if 'injuries' in selected else None, 'regions_analyzed': len(regions), 'critical_regions': critical, 'critical_risk_roads': critical, 'high_risk_regions': high, 'high_risk_roads': high, 'average_risk': average, 'average_risk_score': average, 'highest_risk_region': regions[0] if regions else None, 'highest_risk_location': regions[0] if regions else None, 'most_vulnerable_user': None, 'leading_cause': None, 'peak_risk_hour': None, 'risk_distribution': pd.Series([item['risk_level'] for item in regions]).value_counts().to_dict()}

    def causes(self, region_id: str) -> Dict[str, Any]:
        frame = self._frame(); group = frame[frame['state'].astype(str) == str(region_id)]
        if 'cause' not in group:
            return {'top_cause': None, 'distribution': [], 'message': 'Cause data is not available in the loaded official source.'}
        values = group.groupby('cause')['accidents'].sum().sort_values(ascending=False)
        return {'top_cause': str(values.index[0]) if len(values) else None, 'distribution': [{'cause': str(index), 'value': int(value)} for index, value in values.items()]}

    def vulnerability(self, region_id: str) -> Dict[str, Any]:
        frame = self._frame(); group = frame[frame['state'].astype(str) == str(region_id)]
        column = 'road_user' if 'road_user' in group else None
        if not column:
            return {'top_group': None, 'distribution': [], 'message': 'Road-user data is not available in the loaded official source.'}
        values = group.groupby(column)['fatalities'].sum().sort_values(ascending=False)
        return {'top_group': str(values.index[0]) if len(values) else None, 'distribution': [{'group': str(index), 'value': int(value)} for index, value in values.items()]}

    def prediction(self, region_id: str) -> Dict[str, Any]:
        detail = self.region(region_id); trend = detail['trend']; predicted = None
        if len(trend) >= 2:
            change = trend[-1]['accidents'] - trend[-2]['accidents']; predicted = max(0, trend[-1]['accidents'] + change)
        comparable = self._frame()
        comparable = comparable[comparable['year'] == detail['year']] if 'year' in comparable else comparable
        maximum = max(float(comparable.groupby('state')['accidents'].sum().max()), 1.0)
        predicted_risk = round(float(np.clip((predicted or detail['accidents']) / maximum * 100, 0, 100)), 1)
        trend_label = 'Increasing' if len(trend) > 1 and trend[-1]['accidents'] > trend[-2]['accidents'] else 'Decreasing' if len(trend) > 1 and trend[-1]['accidents'] < trend[-2]['accidents'] else 'Stable'
        return {'region_id': region_id, 'current_risk': detail['risk']['risk_score'], 'predicted_risk': predicted_risk, 'predicted_accidents': predicted, 'predicted_level': self._level(predicted_risk), 'trend': trend_label, 'model_type': 'Historical Trend Forecast', 'metrics': None, 'limitation': 'Historical trend forecast from official annual State/UT data; this is not an accident probability.'}


official_service = OfficialService()
