from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class RoadIncident(Base):
    __tablename__ = "road_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(String(500), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.MEDIUM)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.REPORTED)
    incident_type = Column(String(100))
    reported_by = Column(String(255))
    reported_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analytics = relationship("IncidentAnalytics", back_populates="incident", cascade="all, delete-orphan")


class IncidentAnalytics(Base):
    __tablename__ = "incident_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("road_incidents.id"), nullable=False)
    risk_score = Column(Float, default=0.0)
    predicted_severity = Column(Enum(SeverityLevel))
    weather_condition = Column(String(100))
    traffic_density = Column(String(50))
    time_of_day = Column(String(50))
    day_of_week = Column(String(20))
    contributing_factors = Column(Text)
    ai_recommendations = Column(Text)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incident = relationship("RoadIncident", back_populates="analytics")


class SafetyReport(Base):
    __tablename__ = "safety_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(100))
    area = Column(String(255))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_incidents = Column(Integer, default=0)
    high_risk_areas = Column(Text)
    recommendations = Column(Text)
    generated_by = Column(String(255))
    generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
