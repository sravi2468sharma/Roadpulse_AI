import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = 'RoadPulse AI'
    APP_TITLE: str = 'RoadPulse AI – Predictive Road Risk & Explainable Intervention Intelligence for Indian Roads'
    TAGLINE: str = 'Predict. Explain. Prevent. Prioritize.'
    VERSION: str = '1.0.0'
    DEBUG: bool = True
    HOST: str = '0.0.0.0'
    PORT: int = 8000
    
    ALLOWED_ORIGINS: List[str] = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        '*'
    ]
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DEMO_DATA_PATH: str = os.path.join(BASE_DIR, 'data', 'demo_accidents.csv')
    MODEL_DIR: str = os.path.join(BASE_DIR, 'backend', 'ml')
    MODEL_FILE: str = os.path.join(MODEL_DIR, 'road_risk_rf.joblib')
    METRICS_FILE: str = os.path.join(MODEL_DIR, 'metrics.json')
    ALLOW_DEMO_DATA: bool = False
    DATA_GOV_API_KEY: str = ''
    DATA_GOV_RESOURCE_ACCIDENTS: str = ''
    DATA_GOV_RESOURCE_CAUSES: str = ''
    DATA_GOV_RESOURCE_TRANSPORT: str = ''
    OFFICIAL_RAW_DIR: str = os.path.join(BASE_DIR, 'data', 'raw')
    PROCESSED_DATA_DIR: str = os.path.join(BASE_DIR, 'data', 'processed')
    METADATA_DIR: str = os.path.join(BASE_DIR, 'data', 'metadata')
    
    class Config:
        env_file = '.env'
        extra = 'allow'

settings = Settings()
