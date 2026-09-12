from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from backend.database import get_db
from backend.models import RoadIncident, SeverityLevel, IncidentStatus
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    location: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    incident_type: str | None = None
    reported_by: str | None = None


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    severity: SeverityLevel | None = None
    status: IncidentStatus | None = None
    incident_type: str | None = None


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str | None
    location: str
    latitude: float
    longitude: float
    severity: SeverityLevel
    status: IncidentStatus
    incident_type: str | None
    reported_by: str | None
    reported_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """Create a new road incident report"""
    try:
        db_incident = RoadIncident(**incident.model_dump())
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        logger.info(f"Created incident: {db_incident.id}")
        return db_incident
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating incident: {e}")
        raise HTTPException(status_code=500, detail="Failed to create incident")


@router.get("/", response_model=List[IncidentResponse])
async def list_incidents(
    skip: int = 0,
    limit: int = 100,
    severity: SeverityLevel | None = None,
    status: IncidentStatus | None = None,
    db: Session = Depends(get_db)
):
    """List all road incidents with optional filters"""
    try:
        query = db.query(RoadIncident)
        
        if severity:
            query = query.filter(RoadIncident.severity == severity)
        if status:
            query = query.filter(RoadIncident.status == status)
        
        incidents = query.offset(skip).limit(limit).all()
        return incidents
    except Exception as e:
        logger.error(f"Error listing incidents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve incidents")


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Get a specific incident by ID"""
    incident = db.query(RoadIncident).filter(RoadIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    incident_update: IncidentUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing incident"""
    try:
        db_incident = db.query(RoadIncident).filter(RoadIncident.id == incident_id).first()
        if not db_incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        update_data = incident_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_incident, field, value)
        
        db_incident.updated_at = datetime.utcnow()
        
        if incident_update.status == IncidentStatus.RESOLVED and not db_incident.resolved_at:
            db_incident.resolved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_incident)
        logger.info(f"Updated incident: {incident_id}")
        return db_incident
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating incident: {e}")
        raise HTTPException(status_code=500, detail="Failed to update incident")


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    """Delete an incident"""
    try:
        db_incident = db.query(RoadIncident).filter(RoadIncident.id == incident_id).first()
        if not db_incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        db.delete(db_incident)
        db.commit()
        logger.info(f"Deleted incident: {incident_id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting incident: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete incident")
