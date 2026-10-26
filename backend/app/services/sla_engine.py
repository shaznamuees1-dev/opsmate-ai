"""
Deterministic SLA Risk Engine

Calculates SLA performance metrics for IT Service Management (ITSM) incidents.
All calculations are performed strictly in Python logic without language model estimation.

Assumptions:
1. Timestamps: ISO 8601 strings (e.g. '2026-10-26T10:00:00Z'). If naive, parsed as UTC.
2. Controllable Clock: The `now` parameter accepts an optional timezone-aware datetime
   for fully deterministic testing and evaluation. If omitted, `datetime.now(timezone.utc)` is used.
3. Elapsed Time:
   - For open/in-progress incidents: `(now - created_at)` in minutes.
   - For resolved incidents: `(resolved_at - created_at)` if `resolved_at` is present;
     otherwise `(now - created_at)` capped to resolution.
   - Elapsed time cannot be negative; any negative delta (e.g., created_at in the future)
     is clamped to 0.0 minutes.
4. Remaining Time: `sla_target_minutes - elapsed_minutes`. Negative values indicate
   minutes past breach.
5. Non-Positive SLA Targets: If `sla_target_minutes <= 0`, the target is treated as invalid
   and immediately flagged as BREACHED.
6. Status Classification Rules:
   - If incident status == "Resolved": status is RESOLVED.
   - Else if elapsed >= target or target <= 0: status is BREACHED.
   - Else if elapsed / target >= 0.70 (70%): status is AT_RISK.
   - Else: status is HEALTHY.
"""

from datetime import datetime, timezone
from typing import Optional, Union, Dict, Any
from app.models.incident import Incident, SLAStatus, SLAResult


def parse_timestamp(ts: Union[str, datetime, None]) -> Optional[datetime]:
    """Parse an ISO 8601 string or datetime into a timezone-aware UTC datetime."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    if not isinstance(ts, str) or not ts.strip():
        return None

    try:
        # Support trailing 'Z' as UTC
        clean_ts = ts.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def calculate_sla_risk(
    incident: Union[Incident, Dict[str, Any]],
    now: Optional[datetime] = None,
) -> SLAResult:
    """
    Deterministic calculation of SLA status and remaining time for a given incident.

    Args:
        incident: Incident model or dict containing created_at, sla_target_minutes, status, resolved_at
        now: Optional reference datetime (timezone-aware). Defaults to current UTC time.

    Returns:
        SLAResult containing elapsed_minutes, remaining_minutes, sla_status, breached flag, etc.
    """
    # Normalize inputs whether dict or Incident object
    if isinstance(incident, dict):
        status_raw = incident.get("status", "Open")
        created_at_raw = incident.get("created_at")
        resolved_at_raw = incident.get("resolved_at")
        target_minutes = incident.get("sla_target_minutes", 0)
    else:
        status_raw = incident.status.value if hasattr(incident.status, "value") else incident.status
        created_at_raw = incident.created_at
        resolved_at_raw = incident.resolved_at
        target_minutes = incident.sla_target_minutes

    # Determine reference current time
    if now is None:
        eval_now = datetime.now(timezone.utc)
    else:
        eval_now = parse_timestamp(now) or datetime.now(timezone.utc)

    # Edge Case: Target is non-positive
    try:
        target_minutes = int(target_minutes)
    except (ValueError, TypeError):
        target_minutes = 0

    if target_minutes <= 0:
        return SLAResult(
            elapsed_minutes=0.0,
            remaining_minutes=0.0,
            sla_status=SLAStatus.BREACHED,
            sla_target_minutes=target_minutes,
            breached=True,
            percentage_consumed=100.0,
            calculation_notes="Invalid non-positive SLA target minutes. Marked as BREACHED."
        )

    # Edge Case: Missing or invalid created_at timestamp
    created_dt = parse_timestamp(created_at_raw)
    if created_dt is None:
        return SLAResult(
            elapsed_minutes=0.0,
            remaining_minutes=float(target_minutes),
            sla_status=SLAStatus.BREACHED,
            sla_target_minutes=target_minutes,
            breached=True,
            percentage_consumed=0.0,
            calculation_notes="Missing or malformed created_at timestamp. Defaulted to BREACHED for safety."
        )

    # Calculate end timestamp for elapsed time
    is_resolved = str(status_raw).strip().lower() == "resolved"
    resolved_dt = parse_timestamp(resolved_at_raw) if is_resolved else None

    end_dt = resolved_dt if (is_resolved and resolved_dt is not None) else eval_now

    # Elapsed time in minutes (clamped to 0.0 if end is before created_at)
    delta_seconds = (end_dt - created_dt).total_seconds()
    elapsed_minutes = round(max(0.0, delta_seconds / 60.0), 1)

    # Remaining time in minutes
    remaining_minutes = round(target_minutes - elapsed_minutes, 1)

    # Percentage of SLA target consumed
    percentage_consumed = round(min(999.0, (elapsed_minutes / target_minutes) * 100.0), 1)

    # Status classification
    if is_resolved:
        sla_status = SLAStatus.RESOLVED
        breached = elapsed_minutes > target_minutes
        notes = "Incident is resolved."
    elif elapsed_minutes >= target_minutes:
        sla_status = SLAStatus.BREACHED
        breached = True
        notes = f"SLA breached by {round(elapsed_minutes - target_minutes, 1)} minutes."
    elif elapsed_minutes >= 0.70 * target_minutes:
        sla_status = SLAStatus.AT_RISK
        breached = False
        notes = f"Incident at risk ({percentage_consumed}% consumed, >= 70% threshold)."
    else:
        sla_status = SLAStatus.HEALTHY
        breached = False
        notes = f"Incident SLA is healthy ({percentage_consumed}% consumed)."

    return SLAResult(
        elapsed_minutes=elapsed_minutes,
        remaining_minutes=remaining_minutes,
        sla_status=sla_status,
        sla_target_minutes=target_minutes,
        breached=breached,
        percentage_consumed=percentage_consumed,
        calculation_notes=notes,
    )
