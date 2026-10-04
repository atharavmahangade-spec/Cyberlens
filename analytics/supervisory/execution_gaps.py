"""
CyberLens - Execution Gap Detection
===================================

Phase 3: Supervisory Intelligence & Gap Detection

This module identifies potential execution gaps in SOC operations.

An execution gap occurs when the available operational evidence suggests
that a documented process, expected control, or supervisory practice may
not be functioning effectively in practice.

Important:
- These are supervisory signals, not confirmed violations.
- Every signal is explainable and traceable to source records.
- The module does not make decisions about whether an alert is a
  genuine cyber attack.
"""

from collections import defaultdict
from statistics import median
from typing import Any


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

# These thresholds are intentionally kept in one place so that they
# can later be calibrated using real NCIIPC/CSE data.
DEFAULT_THRESHOLDS = {
    "minimum_investigation_evidence": 1,
    "fast_closure_minutes": 15,
    "repeated_alert_threshold": 3,
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def _get_alert_id(alert: dict[str, Any]) -> str | None:
    """Return the alert identifier if one is available."""

    return alert.get("alert_id") or alert.get("id")


def _has_investigation_evidence(alert: dict[str, Any]) -> bool:
    """
    Check whether the alert contains meaningful investigation evidence.

    Different SOC systems may use different field names, so we support
    a few common representations rather than depending on one schema.
    """

    evidence_fields = [
        "investigation_notes",
        "investigation_summary",
        "analysis_notes",
        "analyst_notes",
        "investigation_evidence",
    ]

    for field in evidence_fields:
        value = alert.get(field)

        if value is None:
            continue

        if isinstance(value, str) and value.strip():
            return True

        if isinstance(value, (list, dict)) and len(value) > 0:
            return True

    return False


def _get_closure_minutes(alert: dict[str, Any]) -> float | None:
    """
    Get alert closure time in minutes.

    The preferred input is an already calculated field such as
    `closure_time_minutes`.

    We intentionally do not parse timestamps here because timestamp
    normalization belongs to the Phase 1/2 data team.
    """

    value = alert.get("closure_time_minutes")

    if value is None:
        value = alert.get("resolution_time_minutes")

    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _build_finding(
    alert: dict[str, Any],
    rule_id: str,
    category: str,
    priority: str,
    reason: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a standardized supervisory finding.

    Keeping one output format makes it easier for the later dashboard,
    reporting layer, and validation system to consume Phase 3 results.
    """

    alert_id = _get_alert_id(alert)

    return {
        "signal_type": "EXECUTION_GAP",
        "rule_id": rule_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "evidence": evidence,
        "source_record_ids": [alert_id] if alert_id else [],
    }


# ---------------------------------------------------------------------
# Individual execution-gap rules
# ---------------------------------------------------------------------

def check_missing_escalation(
    alert: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Detect a critical/high-severity alert that was closed without
    escalation.

    Rule:
        High/Critical + Closed + Not Escalated
        -> potential escalation execution gap
    """

    severity = str(alert.get("severity", "")).lower()
    status = str(alert.get("status", "")).lower()
    escalated = alert.get("escalated")

    if (
        severity in {"critical", "high"}
        and status == "closed"
        and escalated is False
    ):
        return _build_finding(
            alert=alert,
            rule_id="EXEC-ESC-001",
            category="ESCALATION",
            priority="HIGH" if severity == "critical" else "MEDIUM",
            reason=(
                f"{severity.capitalize()} severity alert was closed "
                "without escalation."
            ),
            evidence={
                "alert_id": _get_alert_id(alert),
                "severity": severity,
                "status": status,
                "escalated": escalated,
            },
        )

    return None


def check_insufficient_investigation(
    alert: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any] | None:
    """
    Detect high-priority alerts with no meaningful investigation evidence.

    This is useful for identifying cases where an alert appears to have
    been processed administratively but lacks evidence of substantive
    investigation.
    """

    severity = str(alert.get("severity", "")).lower()
    status = str(alert.get("status", "")).lower()

    if severity not in {"critical", "high"} or status != "closed":
        return None

    evidence_count = alert.get("investigation_evidence_count")

    if evidence_count is not None:
        try:
            has_evidence = (
                float(evidence_count)
                >= thresholds["minimum_investigation_evidence"]
            )
        except (TypeError, ValueError):
            has_evidence = _has_investigation_evidence(alert)
    else:
        has_evidence = _has_investigation_evidence(alert)

    if not has_evidence:
        return _build_finding(
            alert=alert,
            rule_id="EXEC-INV-001",
            category="INVESTIGATION",
            priority="HIGH" if severity == "critical" else "MEDIUM",
            reason=(
                f"{severity.capitalize()} severity alert was closed "
                "without sufficient investigation evidence."
            ),
            evidence={
                "alert_id": _get_alert_id(alert),
                "severity": severity,
                "status": status,
                "investigation_evidence_present": False,
            },
        )

    return None


def check_fast_closure(
    alert: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any] | None:
    """
    Detect unusually fast closure of high/critical alerts.

    Fast closure by itself is NOT proof of poor investigation.
    It becomes a supervisory signal because unusually short handling
    time may warrant manual review, especially for high-risk alerts.
    """

    severity = str(alert.get("severity", "")).lower()
    status = str(alert.get("status", "")).lower()

    if severity not in {"critical", "high"} or status != "closed":
        return None

    closure_minutes = _get_closure_minutes(alert)

    if closure_minutes is None:
        return None

    if closure_minutes < thresholds["fast_closure_minutes"]:
        return _build_finding(
            alert=alert,
            rule_id="EXEC-CLS-001",
            category="CLOSURE",
            priority="HIGH" if severity == "critical" else "MEDIUM",
            reason=(
                f"{severity.capitalize()} severity alert was closed "
                f"within {closure_minutes:g} minutes, which is below "
                "the configured supervisory review threshold."
            ),
            evidence={
                "alert_id": _get_alert_id(alert),
                "severity": severity,
                "closure_time_minutes": closure_minutes,
                "threshold_minutes": thresholds["fast_closure_minutes"],
            },
        )

    return None


def check_repeated_alert_without_remediation(
    alert: dict[str, Any],
    thresholds: dict[str, float],
) -> dict[str, Any] | None:
    """
    Detect repeated alerts associated with the same asset when there
    is no evidence of remediation.

    The repetition count is expected to be calculated by the upstream
    data-processing layer.
    """

    repeat_count = alert.get("repeat_count")

    try:
        repeat_count = int(repeat_count)
    except (TypeError, ValueError):
        return None

    remediation_recorded = alert.get("remediation_recorded")

    if (
        repeat_count >= thresholds["repeated_alert_threshold"]
        and remediation_recorded is False
    ):
        return _build_finding(
            alert=alert,
            rule_id="EXEC-REM-001",
            category="REMEDIATION",
            priority="HIGH",
            reason=(
                f"The same alert pattern has occurred {repeat_count} "
                "times without recorded remediation evidence."
            ),
            evidence={
                "alert_id": _get_alert_id(alert),
                "repeat_count": repeat_count,
                "remediation_recorded": remediation_recorded,
                "threshold": thresholds["repeated_alert_threshold"],
            },
        )

    return None


def check_metric_driven_closure(
    alert: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Identify a possible metric-driven operational pattern.

    Example:
        Alert meets SLA target
        + very limited investigation evidence
        + alert is closed
        -> supervisory review signal

    This does NOT claim that KPI manipulation occurred.
    It simply identifies a pattern worth examination.
    """

    severity = str(alert.get("severity", "")).lower()
    status = str(alert.get("status", "")).lower()

    if severity not in {"critical", "high"} or status != "closed":
        return None

    sla_met = alert.get("sla_met")

    if sla_met is not True:
        return None

    if _has_investigation_evidence(alert):
        return None

    return _build_finding(
        alert=alert,
        rule_id="EXEC-KPI-001",
        category="OPERATIONAL_EFFECTIVENESS",
        priority="HIGH" if severity == "critical" else "MEDIUM",
        reason=(
            "Alert met the recorded SLA target but contains limited "
            "investigation evidence; supervisory review may be warranted."
        ),
        evidence={
            "alert_id": _get_alert_id(alert),
            "severity": severity,
            "sla_met": sla_met,
            "investigation_evidence_present": False,
        },
    )


# ---------------------------------------------------------------------
# Main execution-gap engine
# ---------------------------------------------------------------------

def find_execution_gaps(
    alerts: list[dict[str, Any]],
    thresholds: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """
    Run all execution-gap rules against processed SOC records.

    Parameters
    ----------
    alerts:
        Processed alert records from the Phase 1/2 data pipeline.

    thresholds:
        Optional configuration overrides for supervisory rules.

    Returns
    -------
    list[dict]
        Standardized, explainable execution-gap findings.
    """

    active_thresholds = DEFAULT_THRESHOLDS.copy()

    if thresholds:
        active_thresholds.update(thresholds)

    findings = []

    for alert in alerts:

        if not isinstance(alert, dict):
            # Ignore malformed records rather than crashing the entire
            # supervisory analysis.
            continue

        rules = [
            check_missing_escalation(alert),
            check_insufficient_investigation(alert, active_thresholds),
            check_fast_closure(alert, active_thresholds),
            check_repeated_alert_without_remediation(
                alert,
                active_thresholds,
            ),
            check_metric_driven_closure(alert),
        ]

        for finding in rules:
            if finding is not None:
                findings.append(finding)

    return findings


# ---------------------------------------------------------------------
# Development test
# ---------------------------------------------------------------------

if __name__ == "__main__":

    # These records are ONLY for local development.
    #
    # They allow us to test the Phase 3 logic before the actual
    # processed dataset from the Phase 1/2 team is available.

    sample_alerts = [
        {
            "alert_id": "ALT-001",
            "severity": "critical",
            "status": "closed",
            "escalated": False,
            "closure_time_minutes": 8,
            "investigation_evidence_count": 0,
            "sla_met": True,
            "repeat_count": 1,
            "remediation_recorded": True,
        },
        {
            "alert_id": "ALT-002",
            "severity": "high",
            "status": "closed",
            "escalated": True,
            "closure_time_minutes": 90,
            "investigation_evidence_count": 3,
            "sla_met": True,
            "repeat_count": 1,
            "remediation_recorded": True,
        },
        {
            "alert_id": "ALT-003",
            "severity": "high",
            "status": "closed",
            "escalated": True,
            "closure_time_minutes": 120,
            "investigation_evidence_count": 2,
            "sla_met": True,
            "repeat_count": 5,
            "remediation_recorded": False,
        },
    ]

    results = find_execution_gaps(sample_alerts)

    print(f"\nExecution-gap findings: {len(results)}\n")

    for finding in results:
        print(
            f"[{finding['priority']}] "
            f"{finding['rule_id']} - "
            f"{finding['category']}"
        )
        print(f"Reason: {finding['reason']}")
        print(f"Evidence: {finding['evidence']}")
        print(f"Source records: {finding['source_record_ids']}")
        print("-" * 70) 