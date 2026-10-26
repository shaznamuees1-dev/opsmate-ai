"""
FastAPI Route Handlers

Exposes:
- GET /api/health: Service and AI availability indicator
- GET /api/incidents: Filterable incidents with deterministic SLA metrics
- GET /api/incidents/summary: KPI metrics across the incident dataset
- POST /api/chat: LangGraph + Groq assistant endpoint
"""

import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.models.incident import (
    IncidentWithSLA,
    IncidentSummary,
    ChatRequest,
    ChatResponse,
)
from app.services.incident_service import (
    get_incidents_with_sla,
    get_incident_summary,
    get_incident_by_id,
)
from app.agent.ops_agent import run_ops_assistant

router = APIRouter(prefix="/api")


@router.get("/health")
def health_check():
    """Basic health check endpoint reporting backend and AI status."""
    groq_configured = bool(
        os.getenv("GROQ_API_KEY")
        and os.getenv("GROQ_API_KEY") != "your_groq_api_key_here"
        and not os.getenv("GROQ_API_KEY", "").startswith("your_")
    )
    return {
        "status": "healthy",
        "service": "opsmate-ai-backend",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_ready": groq_configured,
        "dataset_type": "synthetic_in_memory",
    }


@router.get("/incidents", response_model=List[IncidentWithSLA])
def list_incidents_endpoint(
    priority: Optional[str] = Query(None, description="Filter by priority: P1, P2, P3, P4"),
    status: Optional[str] = Query(None, description="Filter by status: Open, In Progress, Resolved"),
    service: Optional[str] = Query(None, description="Filter by service name substring"),
    search: Optional[str] = Query(None, description="Search across title, summary, ID, or service"),
):
    """Return incidents matching query filters with calculated deterministic SLA info."""
    return get_incidents_with_sla(
        priority=priority,
        status=status,
        service=service,
        search=search,
    )


@router.get("/incidents/summary", response_model=IncidentSummary)
def incident_summary_endpoint():
    """Return operational summary KPIs: total, active, P1, at-risk, and breached incidents."""
    return get_incident_summary()


@router.get("/incidents/{incident_id}", response_model=IncidentWithSLA)
def get_single_incident(incident_id: str):
    """Retrieve an individual incident by ID with SLA details."""
    inc = get_incident_by_id(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return inc


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """Accept a user query and execute the LangGraph assistant with Groq and deterministic tools."""
    return run_ops_assistant(request.message)
