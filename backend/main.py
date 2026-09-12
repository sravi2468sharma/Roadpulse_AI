from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import settings
from backend.services.data_service import data_service
from backend.services.mvp_service import mvp_service
from backend.services.official_service import official_service

app = FastAPI(title=settings.APP_TITLE, description=settings.TAGLINE, version=settings.VERSION)
app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class SimulationRequest(BaseModel):
    location_id: str = Field(min_length=1)
    intervention_ids: List[str] = Field(min_length=1)


def require_analytics_data() -> None:
    if data_service.mode() not in {'official', 'demo', 'upload'} or data_service.get_df().empty:
        raise HTTPException(status_code=503, detail={"message": data_service.status().get('message', 'Official dataset not ready.'), "mode": data_service.mode(), "required_files": data_service.status().get('required_files', []), "instructions": "Place official CSV files in data/raw/*.csv, then run python -m backend.data_pipeline.process_data."})


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "tagline": settings.TAGLINE, "status": "operational" if data_service.mode() != 'unavailable' else "data_unavailable", "data": "OFFICIAL GOVERNMENT DATA" if data_service.mode() == 'official' else "DEMO / SYNTHETIC DATA" if data_service.mode() == 'demo' else "OFFICIAL DATA REQUIRED", "data_mode": data_service.mode()}


@app.get("/health")
def health():
    loaded = data_service.mode() in {'official', 'demo', 'upload'} and not data_service.get_df().empty
    return {"status": "ok" if loaded else "data_unavailable", "app": settings.APP_NAME, "data_loaded": loaded, "data_mode": data_service.mode()}


@app.get('/api/data/status')
def data_status():
    return data_service.status()


@app.get('/api/data/sources')
def data_sources():
    from backend.data_pipeline.source_registry import discover_sources, source_profile
    return [{**source_profile(path), 'status': 'processed' if data_service.status().get('processed') else 'available'} for path in discover_sources()]


@app.get("/api/dashboard/summary")
def dashboard_summary():
    require_analytics_data()
    if data_service.mode() == 'official':
        return official_service.summary()
    return mvp_service.summary()


@app.get("/api/locations")
def locations(state: Optional[str] = None, district: Optional[str] = None, risk_level: Optional[str] = None, road_category: Optional[str] = None):
    require_analytics_data()
    if data_service.mode() == 'official':
        result = official_service.regions()
        return [item for item in result if (not state or item['state'] == state) and (not risk_level or item['risk_level'] == risk_level)]
    items = mvp_service.locations({"state": state or "", "district": district or "", "road_category": road_category or ""})
    return [item for item in items if not risk_level or item["risk_level"] == risk_level]


@app.get("/api/risk-map")
def risk_map():
    require_analytics_data()
    if data_service.mode() == 'official':
        return {'data_label': 'OFFICIAL GOVERNMENT DATA', 'granularity': 'State/UT', 'locations': official_service.regions()}
    return {"data_label": "DEMO / SYNTHETIC DATA", "locations": mvp_service.locations()}


@app.get("/api/locations/{location_id}")
def location(location_id: str):
    require_analytics_data()
    try:
        if data_service.mode() == 'official':
            return official_service.region(location_id)
        return mvp_service.location(location_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Location not found") from error


@app.get("/api/locations/{location_id}/risk")
def location_risk(location_id: str):
    return location(location_id)["risk"]


@app.get("/api/locations/{location_id}/causes")
def causes(location_id: str):
    detail = location(location_id)
    if data_service.mode() == 'official':
        return official_service.causes(location_id)
    return {"top_cause": detail["top_cause"], "distribution": [{"cause": item["cause"], "value": item["accidents"]} for item in detail["causes"]], "explanation": detail["explanation"]}


@app.get("/api/locations/{location_id}/vulnerability")
def vulnerability(location_id: str):
    detail = location(location_id)
    if data_service.mode() == 'official':
        return official_service.vulnerability(location_id)
    return {"top_group": detail["top_user"], "distribution": [{"group": item["user"], "value": item["accidents"]} for item in detail["vulnerability"]]}


@app.get("/api/locations/{location_id}/temporal")
def temporal(location_id: str):
    detail = location(location_id)
    if data_service.mode() == 'official':
        return {'peak_hour': None, 'peak_year': detail.get('year'), 'hourly': [], 'monthly': [], 'yearly': detail.get('trend', []), 'message': 'The official source is annual; hourly and monthly resolution is not available.'}
    frame = data_service.get_df().query("location_id == @location_id")
    monthly = frame.groupby("month")["accidents"].sum().sort_index()
    return {"peak_hour": detail["peak_hour"], "peak_month": int(monthly.idxmax()) if len(monthly) else 0, "hourly": detail["temporal"], "monthly": [{"month": int(index), "accidents": int(value)} for index, value in monthly.items()]}


@app.get("/api/locations/{location_id}/prediction")
def prediction(location_id: str):
    try:
        if data_service.mode() == 'official':
            return official_service.prediction(location_id)
        return mvp_service.prediction(location_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Location not found") from error


@app.get("/api/locations/{location_id}/interventions")
def interventions(location_id: str):
    if data_service.mode() == 'official':
        detail = official_service.region(location_id)
        return [
            {'rank': 1, 'id': 'official_audit', 'name': 'State road safety audit', 'matched_factors': ['official accident burden'], 'reason': 'Recommended because official annual State/UT accident totals identify this region as a priority.', 'effectiveness': 0.15, 'cost': 'Medium', 'difficulty': 'Medium', 'timeframe': '1-3 months', 'confidence': 'Scenario assumption'},
            {'rank': 2, 'id': 'data_collection', 'name': 'Improve crash data collection', 'matched_factors': ['granularity limitation'], 'reason': 'Recommended because the loaded official source does not provide cause, user, or location detail.', 'effectiveness': 0.05, 'cost': 'Low', 'difficulty': 'Low', 'timeframe': '1-3 months', 'confidence': 'Planning recommendation'},
            {'rank': 3, 'id': 'regional_enforcement', 'name': 'Targeted regional enforcement review', 'matched_factors': ['accident frequency'], 'reason': 'Recommended because official accident frequency is elevated relative to other State/UT records.', 'effectiveness': 0.10, 'cost': 'Medium', 'difficulty': 'Medium', 'timeframe': '1-3 months', 'confidence': 'Scenario assumption'},
        ]
    return mvp_service.interventions(location_id)


@app.post("/api/simulate")
def simulate(request: SimulationRequest):
    try:
        if data_service.mode() == 'official':
            base = official_service.region(request.location_id)['risk']['risk_score']
            assumptions = {'official_audit': 0.15, 'data_collection': 0.05, 'regional_enforcement': 0.10}
            reduction = 1
            for intervention_id in request.intervention_ids:
                reduction *= 1 - assumptions.get(intervention_id, 0.02)
            scenario = round(max(0, base * reduction), 1)
            return {'location_id': request.location_id, 'current_risk': base, 'scenario_risk': scenario, 'estimated_reduction': round(base - scenario, 1), 'estimated_reduction_percent': round((base - scenario) / base * 100, 1) if base else 0, 'label': 'SCENARIO-BASED ESTIMATE', 'observed_data': 'Official annual State/UT accident totals', 'scenario_assumptions': assumptions, 'disclaimer': 'Scenario-based estimated impact. Not a guaranteed causal reduction.'}
        return mvp_service.simulate(request.location_id, request.intervention_ids)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Location not found") from error


@app.get("/api/action-plan")
def action_plan():
    require_analytics_data()
    if data_service.mode() == 'official':
        plan = []
        for rank, item in enumerate(official_service.regions(), start=1):
            detail = official_service.region(item['id'])
            plan.append({'rank': rank, 'priority': rank, 'region': item['state'], 'state': item['state'], 'road_name': item['state'], 'risk_score': item['risk_score'], 'risk_level': item['risk_level'], 'main_cause': None, 'vulnerable_group': None, 'trend': official_service.prediction(item['id'])['trend'], 'recommended_intervention': 'State road safety audit', 'estimated_impact': 0.15, 'cost': 'Medium', 'urgency': 'Immediate' if item['risk_score'] >= 75 else 'High' if item['risk_score'] >= 50 else 'Monitor'})
        return plan
    plan = []
    for priority, item in enumerate(mvp_service.locations(), start=1):
        detail = mvp_service.location(item["id"])
        recommendation = mvp_service.interventions(item["id"])[0]
        plan.append({"priority": priority, "rank": priority, "urgency": "Immediate" if item["risk_score"] >= 75 else "High" if item["risk_score"] >= 50 else "Monitor", "road": item["road_name"], "road_name": item["road_name"], "state": item["state"], "district": item["district"], "current_risk": item["risk_score"], "risk_score": item["risk_score"], "risk_level": item["risk_level"], "main_cause": detail["top_cause"], "vulnerable_group": detail["top_user"], "peak_hour": detail["peak_hour"], "recommended_intervention": recommendation["name"], "estimated_impact": recommendation["effectiveness"], "cost": recommendation["cost"]})
    return plan


@app.get("/api/model/metrics")
def model_metrics():
    require_analytics_data()
    if data_service.mode() == 'official':
        return {'model_type': 'Historical Trend Forecast', 'metrics': None, 'message': 'Validated ML metrics are unavailable because the loaded official source is annual and insufficient for chronological model validation.'}
    return mvp_service.train()


@app.post("/api/data/upload")
async def upload_data(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file")
    upload_path = settings.DEMO_DATA_PATH + ".upload.csv"
    with open(upload_path, "wb") as target:
        target.write(await file.read())
    return data_service.load_data(upload_path, is_upload=True)