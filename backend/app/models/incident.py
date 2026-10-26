from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class IncidentPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


class SLAStatus(str, Enum):
    HEALTHY = "HEALTHY"
    AT_RISK = "AT_RISK"
    BREACHED = "BREACHED"
    RESOLVED = "RESOLVED"


class Incident(BaseModel):
    id: str
    title: str
    service: str
    priority: IncidentPriority
    status: IncidentStatus
    created_at: str  # ISO 8601 string, e.g. "2026-10-26T08:00:00Z"
    sla_target_minutes: int
    assigned_to: str
    summary: str
    resolved_at: Optional[str] = None


class SLAResult(BaseModel):
    elapsed_minutes: float
    remaining_minutes: float
    sla_status: SLAStatus
    sla_target_minutes: int
    breached: bool
    percentage_consumed: float
    calculation_notes: Optional[str] = None


class IncidentWithSLA(Incident):
    sla: SLAResult


class IncidentSummary(BaseModel):
    total_incidents: int
    active_incidents: int
    p1_incidents: int
    at_risk_incidents: int
    breached_incidents: int


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's query")


class ChatResponse(BaseModel):
    response: str
    tools_used: List[str] = Field(default_factory=list)
    status: str = "success"  # "success" or "fallback" or "error"
