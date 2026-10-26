"""
Synthetic IT Incident Dataset

DISCLAIMER: This dataset contains fictional, synthetic IT service management data
created solely for demonstration and interview testing. No real customer, company,
or proprietary data is contained herein.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.models.incident import Incident, IncidentPriority, IncidentStatus


def generate_synthetic_incidents(reference_time: Optional[datetime] = None) -> List[Incident]:
    """
    Generate a diverse set of synthetic incidents with timestamps calculated
    relative to a reference time. This ensures that whenever the demo is run,
    there are examples of HEALTHY, AT_RISK, BREACHED, and RESOLVED incidents.
    """
    if reference_time is None:
        ref = datetime.now(timezone.utc)
    else:
        ref = reference_time.astimezone(timezone.utc) if reference_time.tzinfo else reference_time.replace(tzinfo=timezone.utc)

    # Helper to produce ISO string from timedelta
    def iso_ago(minutes: int) -> str:
        return (ref - timedelta(minutes=minutes)).isoformat()

    def iso_resolved(created_minutes_ago: int, elapsed_minutes: int) -> str:
        resolved_dt = ref - timedelta(minutes=created_minutes_ago) + timedelta(minutes=elapsed_minutes)
        return resolved_dt.isoformat()

    incidents = [
        Incident(
            id="INC-1001",
            title="Production Database Connection Pool Exhaustion",
            service="Database Service",
            priority=IncidentPriority.P1,
            status=IncidentStatus.IN_PROGRESS,
            created_at=iso_ago(50),
            sla_target_minutes=60,  # 50/60 = 83.3% consumed -> AT_RISK
            assigned_to="DevOps On-Call (Alex Rivera)",
            summary="PostgreSQL connection pool maxed out at 500 connections causing cascading query timeouts across user services."
        ),
        Incident(
            id="INC-1002",
            title="Payment Gateway API Elevated Latency & Dropped Webhooks",
            service="Payment Gateway",
            priority=IncidentPriority.P1,
            status=IncidentStatus.OPEN,
            created_at=iso_ago(75),
            sla_target_minutes=60,  # 75/60 = 125% consumed -> BREACHED
            assigned_to="Payments Engineering (Samira Khan)",
            summary="Stripe and PayPal third-party checkout endpoints reporting HTTP 504 gateway timeouts. Transactions failing for checkout customers."
        ),
        Incident(
            id="INC-1003",
            title="Single Sign-On (SSO) SAML Token Validation Failures",
            service="Auth & Identity",
            priority=IncidentPriority.P2,
            status=IncidentStatus.IN_PROGRESS,
            created_at=iso_ago(90),
            sla_target_minutes=120,  # 90/120 = 75% consumed -> AT_RISK
            assigned_to="Security & Identity Team (Elena Rostova)",
            summary="Okta SAML certificate rotation caused intermittent 401 Unauthorized errors during enterprise user logins."
        ),
        Incident(
            id="INC-1004",
            title="Product Catalog API Slow Search Responses",
            service="Catalog API",
            priority=IncidentPriority.P2,
            status=IncidentStatus.OPEN,
            created_at=iso_ago(30),
            sla_target_minutes=120,  # 30/120 = 25% consumed -> HEALTHY
            assigned_to="Search Platform (Marcus Chen)",
            summary="Elasticsearch node cache miss rate increased following morning catalog ingestion batch."
        ),
        Incident(
            id="INC-1005",
            title="Customer Notification Email Delivery Delays",
            service="Email Delivery",
            priority=IncidentPriority.P3,
            status=IncidentStatus.OPEN,
            created_at=iso_ago(40),
            sla_target_minutes=240,  # 40/240 = 16.7% consumed -> HEALTHY
            assigned_to="Platform Ops (Jordan Taylor)",
            summary="SendGrid outbound mail queue backlog of 15,000 order confirmation and password reset emails."
        ),
        Incident(
            id="INC-1006",
            title="Customer Support Portal 502 Bad Gateway",
            service="Customer Support Portal",
            priority=IncidentPriority.P2,
            status=IncidentStatus.RESOLVED,
            created_at=iso_ago(180),
            sla_target_minutes=120,
            assigned_to="Site Reliability Team (Alex Rivera)",
            summary="Nginx ingress reverse proxy crashed due to bad SSL cipher renegotiation. Ingress Pod restarted and SSL config corrected.",
            resolved_at=iso_resolved(180, 70)  # Resolved in 70 mins (within 120 target) -> RESOLVED
        ),
        Incident(
            id="INC-1007",
            title="Internal Knowledge Base & Wiki Search Index Degraded",
            service="Internal Tools",
            priority=IncidentPriority.P4,
            status=IncidentStatus.OPEN,
            created_at=iso_ago(60),
            sla_target_minutes=480,  # 60/480 = 12.5% consumed -> HEALTHY
            assigned_to="IT Helpdesk (David Kim)",
            summary="Internal Notion/Confluence connector indexing slowed due to API rate limiting."
        ),
        Incident(
            id="INC-1008",
            title="Financial Ledger Transaction Deadlock",
            service="Billing & Accounting",
            priority=IncidentPriority.P1,
            status=IncidentStatus.OPEN,
            created_at=iso_ago(65),
            sla_target_minutes=45,  # 65/45 = 144% consumed -> BREACHED
            assigned_to="Core Banking Team (Samira Khan)",
            summary="Concurrent batch reconciliation jobs triggered row-level lock contention in the general ledger database table."
        ),
    ]

    return incidents


# Global in-memory incident store
_INCIDENT_STORE: List[Incident] = generate_synthetic_incidents()


def get_incident_store() -> List[Incident]:
    """Retrieve the in-memory incident list."""
    global _INCIDENT_STORE
    return _INCIDENT_STORE


def reset_incident_store(reference_time: Optional[datetime] = None) -> List[Incident]:
    """Reset the in-memory incident store to initial synthetic state."""
    global _INCIDENT_STORE
    _INCIDENT_STORE = generate_synthetic_incidents(reference_time)
    return _INCIDENT_STORE
