"""
Unit tests for the Deterministic SLA Risk Engine.
Validates healthy, at-risk, breached, and resolved states, plus boundary cases.
"""

from datetime import datetime, timezone, timedelta
from app.models.incident import Incident, IncidentPriority, IncidentStatus, SLAStatus
from app.services.sla_engine import calculate_sla_risk


def test_healthy_sla_calculation():
    """An incident that consumed < 70% of SLA time should be HEALTHY."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    # Target 60 mins, created 20 mins ago -> 33.3% consumed (< 70%)
    created_at = (fixed_now - timedelta(minutes=20)).isoformat()

    incident = {
        "id": "TEST-1",
        "status": "Open",
        "created_at": created_at,
        "sla_target_minutes": 60,
    }

    result = calculate_sla_risk(incident, now=fixed_now)

    assert result.sla_status == SLAStatus.HEALTHY
    assert result.breached is False
    assert result.elapsed_minutes == 20.0
    assert result.remaining_minutes == 40.0
    assert result.percentage_consumed == 33.3


def test_at_risk_sla_calculation():
    """An incident that consumed between 70% and 100% of SLA should be AT_RISK."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    # Target 100 mins, created 75 mins ago -> 75% consumed
    created_at = (fixed_now - timedelta(minutes=75)).isoformat()

    incident = {
        "id": "TEST-2",
        "status": "In Progress",
        "created_at": created_at,
        "sla_target_minutes": 100,
    }

    result = calculate_sla_risk(incident, now=fixed_now)

    assert result.sla_status == SLAStatus.AT_RISK
    assert result.breached is False
    assert result.elapsed_minutes == 75.0
    assert result.remaining_minutes == 25.0
    assert result.percentage_consumed == 75.0


def test_at_risk_exact_70_percent_boundary():
    """Exact 70% threshold boundary should be marked AT_RISK."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    # Target 100 mins, created 70 mins ago -> exactly 70.0%
    created_at = (fixed_now - timedelta(minutes=70)).isoformat()

    incident = {
        "id": "TEST-3",
        "status": "Open",
        "created_at": created_at,
        "sla_target_minutes": 100,
    }

    result = calculate_sla_risk(incident, now=fixed_now)

    assert result.sla_status == SLAStatus.AT_RISK
    assert result.percentage_consumed == 70.0
    assert result.breached is False


def test_breached_sla_calculation():
    """An incident that exceeded its target minutes should be BREACHED."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    # Target 60 mins, created 75 mins ago -> 125% consumed
    created_at = (fixed_now - timedelta(minutes=75)).isoformat()

    incident = {
        "id": "TEST-4",
        "status": "Open",
        "created_at": created_at,
        "sla_target_minutes": 60,
    }

    result = calculate_sla_risk(incident, now=fixed_now)

    assert result.sla_status == SLAStatus.BREACHED
    assert result.breached is True
    assert result.elapsed_minutes == 75.0
    assert result.remaining_minutes == -15.0


def test_resolved_incident_within_sla():
    """A resolved incident should report SLAStatus.RESOLVED using its resolution time."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    # Created 120 mins ago, resolved 50 mins after creation (target: 60)
    created_dt = fixed_now - timedelta(minutes=120)
    resolved_dt = created_dt + timedelta(minutes=50)

    incident = {
        "id": "TEST-5",
        "status": "Resolved",
        "created_at": created_dt.isoformat(),
        "resolved_at": resolved_dt.isoformat(),
        "sla_target_minutes": 60,
    }

    result = calculate_sla_risk(incident, now=fixed_now)

    assert result.sla_status == SLAStatus.RESOLVED
    assert result.elapsed_minutes == 50.0
    assert result.remaining_minutes == 10.0
    assert result.breached is False


def test_resolved_incident_past_target():
    """A resolved incident that resolved after SLA deadline is marked RESOLVED with breached=True."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
    created_dt = fixed_now - timedelta(minutes=120)
    resolved_dt = created_dt + timedelta(minutes=80)  # Target 60, resolved at 80 mins

    incident = {
        "id": "TEST-6",
        "status": "Resolved",
        "created_at": created_dt.isoformat(),
        "resolved_at": resolved_dt.isoformat(),
        "sla_target_minutes": 60,
    }

    result = calculate_sla_risk(incident, now=fixed_now)

    assert result.sla_status == SLAStatus.RESOLVED
    assert result.breached is True
    assert result.elapsed_minutes == 80.0


def test_invalid_or_negative_sla_target():
    """Edge Case: Non-positive or zero SLA targets should be marked as BREACHED safely."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)

    incident_zero = {
        "id": "TEST-ZERO",
        "status": "Open",
        "created_at": fixed_now.isoformat(),
        "sla_target_minutes": 0,
    }
    result_zero = calculate_sla_risk(incident_zero, now=fixed_now)
    assert result_zero.sla_status == SLAStatus.BREACHED
    assert result_zero.breached is True

    incident_neg = {
        "id": "TEST-NEG",
        "status": "Open",
        "created_at": fixed_now.isoformat(),
        "sla_target_minutes": -30,
    }
    result_neg = calculate_sla_risk(incident_neg, now=fixed_now)
    assert result_neg.sla_status == SLAStatus.BREACHED
    assert result_neg.breached is True


def test_invalid_or_missing_timestamp():
    """Edge Case: Missing or malformed created_at timestamp should safely return BREACHED."""
    fixed_now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)

    incident_bad_ts = {
        "id": "TEST-BAD-TS",
        "status": "Open",
        "created_at": "not-a-valid-timestamp",
        "sla_target_minutes": 60,
    }
    result = calculate_sla_risk(incident_bad_ts, now=fixed_now)
    assert result.sla_status == SLAStatus.BREACHED
    assert result.breached is True

    incident_none_ts = {
        "id": "TEST-NONE-TS",
        "status": "Open",
        "created_at": None,
        "sla_target_minutes": 60,
    }
    result_none = calculate_sla_risk(incident_none_ts, now=fixed_now)
    assert result_none.sla_status == SLAStatus.BREACHED
    assert result_none.breached is True
