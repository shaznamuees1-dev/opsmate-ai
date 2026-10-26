"""
Incident Query & Management Service

Provides filtering, retrieval, and metric summaries for IT incidents.
All incident operations integrate with the deterministic SLA risk engine.
"""

from datetime import datetime
from typing import List, Optional
from app.models.incident import (
    Incident,
    IncidentWithSLA,
    IncidentSummary,
    SLAStatus,
    IncidentPriority,
    IncidentStatus,
)
from app.data.incidents import get_incident_store
from app.services.sla_engine import calculate_sla_risk


def get_incidents_with_sla(
    priority: Optional[str] = None,
    status: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None,
    now: Optional[datetime] = None,
) -> List[IncidentWithSLA]:
    """
    Retrieve incidents filtered by priority, status, service, or keyword search,
    annotated with deterministic SLA risk metrics.
    """
    incidents = get_incident_store()
    results: List[IncidentWithSLA] = []

    # Normalization for case-insensitive filtering
    norm_priority = priority.strip().upper() if priority and priority.strip() else None
    norm_status = status.strip().lower() if status and status.strip() else None
    norm_service = service.strip().lower() if service and service.strip() else None
    norm_search = search.strip().lower() if search and search.strip() else None

    for inc in incidents:
        # Priority match
        if norm_priority and inc.priority.value.upper() != norm_priority:
            continue

        # Status match (flexible casing)
        if norm_status and inc.status.value.lower() != norm_status:
            continue

        # Service match (substring case-insensitive)
        if norm_service and norm_service not in inc.service.lower():
            continue

        # Keyword search across title, summary, id, and service
        if norm_search:
            searchable_text = f"{inc.id} {inc.title} {inc.summary} {inc.service} {inc.assigned_to}".lower()
            if norm_search not in searchable_text:
                continue

        # Calculate SLA risk deterministically
        sla_result = calculate_sla_risk(inc, now=now)

        results.append(
            IncidentWithSLA(
                id=inc.id,
                title=inc.title,
                service=inc.service,
                priority=inc.priority,
                status=inc.status,
                created_at=inc.created_at,
                sla_target_minutes=inc.sla_target_minutes,
                assigned_to=inc.assigned_to,
                summary=inc.summary,
                resolved_at=inc.resolved_at,
                sla=sla_result,
            )
        )

    return results


def get_incident_summary(now: Optional[datetime] = None) -> IncidentSummary:
    """
    Compute aggregate operational metrics across the incident dataset:
    - total_incidents: total count of all incidents in the dataset
    - active_incidents: incidents not marked as Resolved
    - p1_incidents: count of active P1 priority incidents
    - at_risk_incidents: count of active incidents currently in AT_RISK SLA status
    - breached_incidents: count of active incidents currently in BREACHED SLA status
    """
    all_incidents = get_incidents_with_sla(now=now)

    total_incidents = len(all_incidents)
    active_incidents = 0
    p1_incidents = 0
    at_risk_incidents = 0
    breached_incidents = 0

    for item in all_incidents:
        is_active = item.status != IncidentStatus.RESOLVED
        if is_active:
            active_incidents += 1
            if item.priority == IncidentPriority.P1:
                p1_incidents += 1
            if item.sla.sla_status == SLAStatus.AT_RISK:
                at_risk_incidents += 1
            elif item.sla.sla_status == SLAStatus.BREACHED:
                breached_incidents += 1

    return IncidentSummary(
        total_incidents=total_incidents,
        active_incidents=active_incidents,
        p1_incidents=p1_incidents,
        at_risk_incidents=at_risk_incidents,
        breached_incidents=breached_incidents,
    )


def get_incident_by_id(incident_id: str, now: Optional[datetime] = None) -> Optional[IncidentWithSLA]:
    """Retrieve a single incident by ID with calculated SLA metrics."""
    target_id = incident_id.strip().upper()
    for inc in get_incident_store():
        if inc.id.upper() == target_id:
            sla_result = calculate_sla_risk(inc, now=now)
            return IncidentWithSLA(
                id=inc.id,
                title=inc.title,
                service=inc.service,
                priority=inc.priority,
                status=inc.status,
                created_at=inc.created_at,
                sla_target_minutes=inc.sla_target_minutes,
                assigned_to=inc.assigned_to,
                summary=inc.summary,
                resolved_at=inc.resolved_at,
                sla=sla_result,
            )
    return None
