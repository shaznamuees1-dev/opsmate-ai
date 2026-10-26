"""
Unit tests for Incident filtering and Summary metrics service.
"""

from datetime import datetime, timezone
from app.data.incidents import reset_incident_store
from app.services.incident_service import (
    get_incidents_with_sla,
    get_incident_summary,
    get_incident_by_id,
)
from app.models.incident import IncidentPriority, IncidentStatus, SLAStatus


def setup_function():
    """Reset the incident store before each test with a fixed reference time."""
    fixed_ref = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    reset_incident_store(fixed_ref)


def test_filter_by_priority():
    """Verify filtering by priority (e.g. P1) returns only P1 incidents."""
    p1_list = get_incidents_with_sla(priority="P1")
    assert len(p1_list) > 0
    assert all(inc.priority == IncidentPriority.P1 for inc in p1_list)

    # Case insensitive
    p2_list = get_incidents_with_sla(priority="p2")
    assert len(p2_list) > 0
    assert all(inc.priority == IncidentPriority.P2 for inc in p2_list)


def test_filter_by_status():
    """Verify filtering by status (Open, In Progress, Resolved)."""
    open_list = get_incidents_with_sla(status="Open")
    assert len(open_list) > 0
    assert all(inc.status == IncidentStatus.OPEN for inc in open_list)

    resolved_list = get_incidents_with_sla(status="resolved")
    assert len(resolved_list) > 0
    assert all(inc.status == IncidentStatus.RESOLVED for inc in resolved_list)


def test_filter_by_service():
    """Verify substring case-insensitive service search."""
    db_list = get_incidents_with_sla(service="database")
    assert len(db_list) >= 1
    assert any("database" in inc.service.lower() for inc in db_list)


def test_filter_by_keyword_search():
    """Verify searching across title, summary, ID, and service."""
    search_results = get_incidents_with_sla(search="stripe")
    assert len(search_results) >= 1
    assert any("stripe" in (inc.summary + inc.title).lower() for inc in search_results)

    id_search = get_incidents_with_sla(search="INC-1001")
    assert len(id_search) == 1
    assert id_search[0].id == "INC-1001"


def test_summary_metrics():
    """Verify KPI aggregation calculations."""
    fixed_ref = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    summary = get_incident_summary(now=fixed_ref)

    assert summary.total_incidents == 8
    assert summary.active_incidents == 7  # 8 total - 1 resolved
    assert summary.p1_incidents == 3      # 3 active P1s
    assert summary.at_risk_incidents >= 1
    assert summary.breached_incidents >= 1
    assert summary.total_incidents >= summary.active_incidents


def test_get_incident_by_id():
    """Verify single incident retrieval by ID."""
    inc = get_incident_by_id("INC-1001")
    assert inc is not None
    assert inc.id == "INC-1001"
    assert inc.service == "Database Service"
    assert inc.sla is not None

    non_existent = get_incident_by_id("INC-9999")
    assert non_existent is None
