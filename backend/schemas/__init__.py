from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class RiskLevelDistribution(BaseModel):
    low: int
    medium: int
    high: int
    critical: int

class TrendPoint(BaseModel):
    year: int
    accidents: int
    fatalities: int
    injuries: int

class RiskyRoadItem(BaseModel):
    id: str
    road_name: str
    road_segment: str
    district: str
    state: str
    risk_score: float
    risk_level: str
    fatalities: int
    accidents: int
    top_cause: str
    most_vulnerable_user: str

class SummaryResponse(BaseModel):
    app_name: str
    tagline: str
    total_records: int
    total_accidents: int
    total_fatalities: int
    total_injuries: int
    critical_risk_roads_count: int
    high_risk_roads_count: int
    average_risk_score: float
    highest_risk_road: Optional[RiskyRoadItem]
    highest_risk_district: str
    most_vulnerable_category: str
    peak_risk_time_period: str
    top_recommended_intervention: str
    risk_distribution: RiskLevelDistribution
    accident_trend: List[TrendPoint]
    top_5_risky_roads: List[RiskyRoadItem]
    is_demo_dataset: bool

class LocationItem(BaseModel):
    id: str
    road_name: str
    road_segment: str
    district: str
    state: str
    city: str
    road_category: str
    latitude: float
    longitude: float
    risk_score: float
    risk_level: str
    accident_count: int
    fatalities: int
    injuries: int
    top_cause: str
    most_vulnerable_user: str
    peak_risk_period: str

class RiskMapResponse(BaseModel):
    locations: List[LocationItem]
    total_locations: int
    states: List[str]
    districts: List[str]
    road_categories: List[str]
    causes: List[str]
    vehicle_types: List[str]

class RiskComponentDetail(BaseModel):
    name: str
    score: float
    max_score: float
    weight_pct: float
    description: str

class RiskScoreResponse(BaseModel):
    location_id: str
    road_name: str
    road_segment: str
    risk_score: float
    risk_level: str
    severity_raw: float
    component_scores: Dict[str, float]
    contribution_breakdown: List[RiskComponentDetail]

class CauseFactor(BaseModel):
    factor: str
    percentage: float
    incidents: int
    fatalities: int
    severity_impact: float
    description: str

class CauseAnalysisResponse(BaseModel):
    location_id: str
    road_name: str
    road_segment: str
    primary_cause: str
    causes: List[CauseFactor]
    plain_explanation: str
    feature_importance: List[Dict[str, Any]]

class VulnerabilityItem(BaseModel):
    category: str
    count: int
    percentage: float
    fatalities: int

class VulnerabilityResponse(BaseModel):
    location_id: str
    road_name: str
    top_vulnerable_category: str
    vru_percentage: float
    categories: List[VulnerabilityItem]

class TemporalHour(BaseModel):
    hour: int
    label: str
    accident_count: int
    fatality_count: int
    risk_intensity: float

class TemporalResponse(BaseModel):
    location_id: str
    road_name: str
    peak_hours: str
    peak_hour_int: int
    weekday_vs_weekend: Dict[str, int]
    hourly_distribution: List[TemporalHour]
    monthly_distribution: List[Dict[str, Any]]

class PredictionRequest(BaseModel):
    target_period: str = 'Next Quarter'
    custom_speed_reduction_pct: Optional[float] = 0.0
    custom_lighting_improved: Optional[bool] = False

class PredictionResponse(BaseModel):
    location_id: str
    road_name: str
    road_segment: str
    target_period: str
    current_risk_score: float
    predicted_risk_score: float
    predicted_risk_level: str
    confidence_lower: float
    confidence_upper: float
    trend_direction: str
    historical_trend: List[Dict[str, Any]]
    influencing_factors: List[Dict[str, Any]]
    model_type: str
    model_disclaimer: str

class ModelMetricsResponse(BaseModel):
    model_name: str
    algorithm: str
    r2_score: float
    mae: float
    rmse: float
    training_samples: int
    test_samples: int
    feature_names: List[str]
    feature_importances: List[Dict[str, Any]]
    disclaimer: str

class InterventionItem(BaseModel):
    id: str
    name: str
    reason: str
    applicable_factors: List[str]
    description: str
    estimated_effectiveness: float
    estimated_impact_display: str
    cost_level: str
    difficulty: str
    timeframe: str
    priority_score: float
    target_risk_factor: str

class InterventionRecommendationResponse(BaseModel):
    location_id: str
    road_name: str
    current_risk_score: float
    current_risk_level: str
    primary_cause: str
    recommendations: List[InterventionItem]

class SimulationRequest(BaseModel):
    location_id: str
    intervention_ids: List[str]

class SimulationComparisonItem(BaseModel):
    intervention_id: str
    name: str
    cost_level: str
    scenario_risk_score: float
    risk_reduction_points: float
    relative_safety_benefit_pct: float

class SimulationResponse(BaseModel):
    location_id: str
    road_name: str
    current_risk_score: float
    current_risk_level: str
    scenario_risk_score: float
    scenario_risk_level: str
    estimated_risk_reduction_points: float
    relative_safety_benefit_pct: float
    cost_category: str
    priority_ranking: str
    selected_interventions: List[InterventionItem]
    comparisons: List[SimulationComparisonItem]
    scientific_disclaimer: str

class ActionPlanItem(BaseModel):
    priority_rank: int
    location_id: str
    road_name: str
    road_segment: str
    district: str
    state: str
    current_risk_score: float
    risk_level: str
    main_cause: str
    vulnerable_group: str
    peak_risk_time: str
    recommended_intervention: str
    estimated_impact: str
    implementation_cost: str
    urgency: str

class ActionPlanResponse(BaseModel):
    actions: List[ActionPlanItem]
    total_actions: int
    immediate_actions_count: int
    high_urgency_count: int

class DataUploadResponse(BaseModel):
    message: str
    filename: str
    total_records: int
    columns_mapped: Dict[str, str]
    missing_optional_columns: List[str]
    is_demo: bool
