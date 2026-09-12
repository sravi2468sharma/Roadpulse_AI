import pandas as pd
from fastapi.testclient import TestClient

from backend.data_pipeline.normalize import wide_state_year_to_long
from backend.data_pipeline.validate import validate_frame
from backend.main import app
from backend.services.risk_service import risk_engine

client = TestClient(app)


def test_health_and_data_status_are_explicit_when_official_data_is_missing():
    health = client.get('/health')
    status = client.get('/api/data/status')
    assert health.status_code == 200
    assert status.status_code == 200
    assert health.json()['status'] in {'ok', 'data_unavailable'}
    if status.json()['mode'] == 'unavailable':
        assert client.get('/api/dashboard/summary').status_code == 503


def test_risk_thresholds():
    assert risk_engine.classify_risk_level(0) == 'Low'
    assert risk_engine.classify_risk_level(25) == 'Medium'
    assert risk_engine.classify_risk_level(50) == 'High'
    assert risk_engine.classify_risk_level(75) == 'Critical'


def test_official_wide_state_table_normalizes_without_inventing_fields():
    source = pd.DataFrame({
        'States/UTs': ['State A', 'State B'],
        'State/UT-Wise Total Number of Road Accidents during 2018': [10, 20],
        'State/UT-Wise Total Number of Road Accidents during 2019': [12, 18],
    })
    normalized = wide_state_year_to_long(source)
    assert set(normalized.columns) == {'state', 'year', 'accidents'}
    assert 'latitude' not in normalized.columns
    assert validate_frame(normalized)['valid']
