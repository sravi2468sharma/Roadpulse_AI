from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from backend.database import get_db
from backend.models import SafetyReport
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic schemas
class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    report_type: str
    area: str
    start_date: datetime
    end_date: datetime
    total_incidents: int = 0
    high_risk_areas: str | None = None
    recommendations: str | None = None
    generated_by: str | None = None


class ReportResponse(BaseModel):
    id: int
    title: str
    report_type: str
    area: str
    start_date: datetime
    end_date: datetime
    total_incidents: int
    high_risk_areas: str | None
    recommendations: str | None
    generated_by: str | None
    generated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    """Create a new safety report"""
    try:
        db_report = SafetyReport(**report.model_dump())
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        logger.info(f"Created report: {db_report.id}")
        return db_report
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create report")


@router.get("/", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    report_type: str | None = None,
    db: Session = Depends(get_db)
):
    """List all safety reports with optional filters"""
    try:
        query = db.query(SafetyReport)
        
        if report_type:
            query = query.filter(SafetyReport.report_type == report_type)
        
        reports = query.order_by(SafetyReport.generated_at.desc()).offset(skip).limit(limit).all()
        return reports
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve reports")


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """Get a specific report by ID"""
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    """Delete a report"""
    try:
        db_report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
        if not db_report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        db.delete(db_report)
        db.commit()
        logger.info(f"Deleted report: {report_id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete report")
