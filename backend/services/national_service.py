from pathlib import Path
from typing import Any, Dict

import pandas as pd

from backend.config import settings


class NationalService:
    def _read(self, filename: str) -> pd.DataFrame:
        path = Path(settings.PROCESSED_DATA_DIR) / filename
        return pd.read_csv(path) if path.exists() else pd.DataFrame()

    def causes(self) -> Dict[str, Any]:
        frame = self._read('cause_analysis.csv')
        distribution = frame.to_dict('records') if not frame.empty else []
        top = max(distribution, key=lambda row: row.get('share_cases', 0) or 0) if distribution else None
        return {
            'scope': 'India', 'year': 2023,
            'top_cause': top.get('cause') if top else None,
            'distribution': distribution,
            'source': 'NCRB ADSI 2023 Table 1A.8',
            'source_file': 'NCRB_ADSI_2023_Table_1A.8.csv',
            'aggregation_level': 'All-India aggregate',
        }

    def vulnerability(self) -> Dict[str, Any]:
        frame = self._read('vulnerability_analysis.csv')
        distribution = frame.to_dict('records') if not frame.empty else []
        top = max(distribution, key=lambda row: row.get('death_share', 0) or 0) if distribution else None
        return {
            'scope': 'India', 'year': 2023,
            'most_vulnerable_mode': top.get('mode') if top else None,
            'distribution': distribution,
            'source': 'NCRB ADSI 2023 Table 1A.3_2',
            'source_file': 'NCRB_ADSI_2023_Table_1A.3_2.csv',
            'aggregation_level': 'All-India aggregate',
        }


national_service = NationalService()
