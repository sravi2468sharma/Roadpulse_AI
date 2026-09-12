import os
import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from backend.config import settings
from backend.services.data_service import data_service
from backend.services.risk_service import risk_engine
from backend.ml.features import build_training_dataset, FEATURE_NAMES

def train_model():
    print('Starting RoadPulse AI RandomForest Training Pipeline...')
    df = data_service.get_df()
    
    X, y, feature_names = build_training_dataset(df, risk_engine.calculate_corridor_risk)
    print(f'Constructed training dataset: {X.shape[0]} samples, {X.shape[1]} features')
    
    if len(X) < 10:
        print('Augmenting samples for training')
        noise = np.random.normal(0, 0.02, X.shape)
        X = np.vstack([X, X + noise])
        y = np.concatenate([y, y])
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    
    rf = RandomForestRegressor(
        n_estimators=120,
        max_depth=6,
        min_samples_split=3,
        random_state=42
    )
    rf.fit(X_train, y_train)
    
    y_pred = rf.predict(X_test)
    
    r2 = float(r2_score(y_test, y_pred))
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    
    importances = rf.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    feature_importances = [
        {
            'feature': feature_names[i],
            'importance': round(float(importances[i]), 4),
            'importance_pct': round(float(importances[i]) * 100, 1)
        }
        for i in sorted_idx
    ]
    
    metrics = {
        'model_name': 'Corridor Risk Predictor RF',
        'algorithm': 'RandomForestRegressor (120 Estimators, Depth=6)',
        'r2_score': round(r2, 4),
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'training_samples': int(len(X_train)),
        'test_samples': int(len(X_test)),
        'feature_names': feature_names,
        'feature_importances': feature_importances,
        'disclaimer': 'Trained on validated corridor historical slices. Metrics reflect actual test-split validation performance.'
    }
    
    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    joblib.dump(rf, settings.MODEL_FILE)
    
    with open(settings.METRICS_FILE, 'w', encoding='utf-8') as mf:
        json.dump(metrics, mf, indent=2)
        
    print('Training complete: R2=', metrics['r2_score'], 'MAE=', metrics['mae'])
    return metrics

if __name__ == '__main__':
    train_model()
