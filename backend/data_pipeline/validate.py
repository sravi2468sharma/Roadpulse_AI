from typing import Dict, Any

import pandas as pd


def validate_frame(frame: pd.DataFrame) -> Dict[str, Any]:
    numeric = [column for column in ('accidents', 'fatalities', 'injuries') if column in frame.columns]
    negative = {column: int((pd.to_numeric(frame[column], errors='coerce') < 0).sum()) for column in numeric}
    invalid_years = int((~pd.to_numeric(frame['year'], errors='coerce').between(1900, 2100)).sum()) if 'year' in frame.columns else 0
    missing_state = int(frame['state'].isna().sum()) if 'state' in frame.columns else len(frame)
    return {
        'rows': len(frame),
        'columns': list(frame.columns),
        'negative_values': negative,
        'invalid_years': invalid_years,
        'missing_state': missing_state,
        'duplicate_rows': int(frame.duplicated().sum()),
        'valid': not any(negative.values()) and invalid_years == 0 and missing_state == 0,
    }
