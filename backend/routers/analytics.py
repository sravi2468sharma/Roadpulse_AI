from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from backend.database import get_db
from backend.models import IncidentAnalytics, RoadIncident, SeverityLevel
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class AnalyticsCreate(BaseModel):
    incident_id: int
    risk_score: float = Field(..., ge=0.0, le=100.0)
    predicted_severity: SeverityLevel
    weather_condition: str | None = None
    traffic_density: str | None = None
    time_of_day: str | None = None
    day_of_week: str | None = None
    contributing_factors: str | None = None
    ai_recommendations: str | None = None


class AnalyticsResponse(BaseModel):
    id: int
    incident_id: int
    risk_score: float
    predicted_severity: SeverityLevel
    weather_condition: str | None
    traffic_density: str | None
    time_of_day: str | None
    day_of_week: str | None
    contributing_factors: str | None
    ai_recommendations: str | None
    analyzed_at: datetime

    class Config:
        from_attributes = True


class RiskAnalysisResponse(BaseModel):
    total_incidents: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_risk_score: float
    high_risk_areas: List[dict]


@router.post("/", response_model=AnalyticsResponse, status_code=status.HTTP_201_CREATED)
async def create_analytics(analytics: AnalyticsCreate, db: Session = Depends(get_db)):
    """Create analytics data for an incident"""
    try:
        # Verify incident exists
        incident = db.query(RoadIncident).filter(RoadIncident.id == analytics.incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        db_analytics = IncidentAnalytics(**analytics.model_dump())
        db.add(db_analytics)
        db.commit()
        db.refresh(db_analytics)
        logger.info(f"Created analytics for incident: {analytics.incident_id}")
        return db_analytics
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to create analytics")


@router.get("/incident/{incident_id}", response_model=List[AnalyticsResponse])
async def get_incident_analytics(incident_id: int, db: Session = Depends(get_db)):
    """Get all analytics for a specific incident"""
    analytics = db.query(IncidentAnalytics).filter(
        IncidentAnalytics.incident_id == incident_id
    ).all()
    return analytics


@router.get("/risk-analysis", response_model=RiskAnalysisResponse)
async def get_risk_analysis(db: Session = Depends(get_db)):
    """Get overall risk analysis across all incidents"""
    try:
        analytics = db.query(IncidentAnalytics).all()
        
        if not analytics:
            return RiskAnalysisResponse(
                total_incidents=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0,
                average_risk_score=0.0,
                high_risk_areas=[]
            )
        
        total = len(analytics)
        high_risk = sum(1 for a in analytics if a.risk_score >= 70)
        medium_risk = sum(1 for a in analytics if 40 <= a.risk_score < 70)
        low_risk = sum(1 for a in analytics if a.risk_score < 40)
        avg_score = sum(a.risk_score for a in analytics) / total
        
        # Get high risk areas (simplified)
        high_risk_incidents = db.query(RoadIncident).join(IncidentAnalytics).filter(
            IncidentAnalytics.risk_score >= 70
        ).limit(10).all()
        
        high_risk_areas = [
            {
                "location": incident.location,
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "risk_score": next((a.risk_score for a in analytics if a.incident_id == incident.id), 0)
            }
            for incident in high_risk_incidents
        ]
        
        return RiskAnalysisResponse(
            total_incidents=total,
            high_risk_count=high_risk,
            medium_risk_count=medium_risk,
            low_risk_count=low_risk,
            average_risk_score=round(avg_score, 2),
            high_risk_areas=high_risk_areas
        )
    except Exception as e:
        logger.error(f"Error getting risk analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve risk analysis")


@router.delete("/{analytics_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analytics(analytics_id: int, db: Session = Depends(get_db)):
    """Delete analytics data"""
    try:
        db_analytics = db.query(IncidentAnalytics).filter(
            IncidentAnalytics.id == analytics_id
        ).first()
        if not db_analytics:
            raise HTTPException(status_code=404, detail="Analytics not found")
        
        db.delete(db_analytics)
        db.commit()
        logger.info(f"Deleted analytics: {analytics_id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete analytics")
