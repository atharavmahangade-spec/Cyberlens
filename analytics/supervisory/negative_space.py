"""
CyberLens - Phase 3
Negative Space Detection
========================

Purpose:
    Identify situations where expected operational evidence is absent,
    incomplete, or unexpectedly low in periodic SOC/CSE assessment data.

Important:
    Negative space is a supervisory indicator.

    Missing evidence does NOT automatically mean that a control failed.
    It means the available evidence does not demonstrate the expected
    operational activity and may therefore require human review.

This module is:
    - Offline
    - Deterministic
    - Explainable
    - Evidence-oriented
    - Human-review focused
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd


# ---------------------------------------------------------------------
# Module version
# ---------------------------------------------------------------------

MODEL_VERSION = "cyberlens-phase3-negative-space-0.1.0"


# ---------------------------------------------------------------------
# Default thresholds
# ---------------------------------------------------------------------

DEFAULT_CRITICAL_MONITORING_THRESHOLD = 1.0
DEFAULT_LOW_MONITORING_THRESHOLD = 0.50


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _empty_signals() -> list[dict[str, Any]]:
    """Return an empty signal list."""

    return []


def _safe_string(
    value: Any,
    default: str = "",
) -> str:
    """Safely convert a value to a stripped string."""

    if value is None:
        return default

    if pd.isna(value):
        return default

    return str(value).strip()


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    try:
        if value is None or pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def _entity_column(
    df: pd.DataFrame,
) -> Optional[str]:
    """Find the supported entity identifier."""

    for column in (
        "entity_id",
        "cse_id",
        "cse",
        "organization_id",
    ):
        if column in df.columns:
            return column

    return None


def _record_id_column(
    df: pd.DataFrame,
) -> Optional[str]:
    """Find a source record identifier."""

    for column in (
        "record_id",
        "alert_id",
        "case_id",
        "investigation_id",
        "asset_id",
        "event_id",
    ):
        if column in df.columns:
            return column

    return None


def _normalise_ids(
    values: list[Any],
) -> list[str]:
    """Normalize and deduplicate source record IDs."""

    result: list[str] = []

    for value in values:

        record_id = _safe_string(value)

        if not record_id:
            continue

        if record_id not in result:
            result.append(record_id)

    return result


def _make_signal(
    *,
    entity_id: str,
    signal_id: str,
    rule_id: str,
    priority: str,
    reason: str,
    evidence: list[dict[str, Any]],
    source_record_ids: list[str],
    evidence_confidence: str = "MEDIUM",
) -> dict[str, Any]:
    """
    Construct a standardized negative-space signal.
    """

    return {
        "signal_id": signal_id,
        "signal_type": "NEGATIVE_SPACE",
        "rule_id": rule_id,
        "category": "EVIDENCE_GAP",
        "priority": priority,
        "reason": reason,
        "evidence": evidence,
        "source_record_ids": _normalise_ids(
            source_record_ids
        ),
        "historical_context": {},
        "peer_context": {},
        "evidence_confidence": evidence_confidence,
        "rule_model_version": MODEL_VERSION,
        "entity_id": entity_id,
        "human_review_required": True,
    }


def _entity_values(
    df: pd.DataFrame,
) -> set[str]:
    """Return all entity IDs in a table."""

    if df.empty:
        return set()

    entity_column = _entity_column(df)

    if entity_column is None:
        return set()

    return {
        _safe_string(value)
        for value in df[entity_column].dropna()
        if _safe_string(value)
    }


def _records_for_entity(
    df: pd.DataFrame,
    entity_id: str,
) -> pd.DataFrame:
    """Return records belonging to one entity."""

    if df.empty:
        return df.copy()

    entity_column = _entity_column(df)

    if entity_column is None:
        return pd.DataFrame()

    mask = (
        df[entity_column]
        .astype(str)
        .str.strip()
        == entity_id
    )

    return df.loc[mask].copy()


def _source_ids(
    df: pd.DataFrame,
) -> list[str]:
    """Extract source record identifiers."""

    if df.empty:
        return []

    record_column = _record_id_column(df)

    if record_column is None:
        return []

    return _normalise_ids(
        df[record_column]
        .dropna()
        .tolist()
    )


# ---------------------------------------------------------------------
# Rule 1
# Critical assets without monitoring evidence
# ---------------------------------------------------------------------


def detect_unmonitored_critical_assets(
    assets: Optional[pd.DataFrame],
) -> list[dict[str, Any]]:
    """
    Detect critical/high-priority assets without monitoring evidence.

    Required fields:
        entity identifier
        criticality
        monitoring_status
    """

    if assets is None or assets.empty:
        return []

    entity_column = _entity_column(assets)

    if entity_column is None:
        return []

    if "criticality" not in assets.columns:
        return []

    if "monitoring_status" not in assets.columns:
        return []

    signals = []

    criticality = (
        assets["criticality"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    monitoring_status = (
        assets["monitoring_status"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    critical_mask = criticality.isin(
        (
            "critical",
            "high",
            "1",
            "p1",
        )
    )

    monitored_mask = monitoring_status.isin(
        (
            "active",
            "monitored",
            "enabled",
            "healthy",
        )
    )

    missing_monitoring = (
        critical_mask
        & ~monitored_mask
    )

    for entity_id, group in (
        assets.loc[missing_monitoring]
        .groupby(entity_column)
    ):

        entity_id = _safe_string(
            entity_id
        )

        record_ids = _source_ids(group)

        signals.append(
            _make_signal(
                entity_id=entity_id,
                signal_id=(
                    f"NS-CRITICAL-MONITORING-"
                    f"{entity_id}"
                ),
                rule_id="NS-001",
                priority="HIGH",
                reason=(
                    "Critical or high-priority assets "
                    "are present without corresponding "
                    "monitoring evidence."
                ),
                evidence=[
                    {
                        "type": "asset_monitoring_gap",
                        "critical_asset_count": int(
                            len(group)
                        ),
                        "source": "asset_inventory",
                    }
                ],
                source_record_ids=record_ids,
                evidence_confidence="HIGH",
            )
        )

    return signals


# ---------------------------------------------------------------------
# Rule 2
# High severity alerts without investigations
# ---------------------------------------------------------------------


def detect_high_severity_without_investigation(
    alerts: Optional[pd.DataFrame],
    investigations: Optional[pd.DataFrame],
) -> list[dict[str, Any]]:
    """
    Detect high/critical alerts for which no investigation record
    exists for the same entity.

    This is an entity-level supervisory indicator, not an assertion
    that every individual alert requires investigation.
    """

    if alerts is None or alerts.empty:
        return []

    if investigations is None:
        investigations = pd.DataFrame()

    entity_column = _entity_column(alerts)

    if entity_column is None:
        return []

    if "severity" not in alerts.columns:
        return []

    severity = (
        alerts["severity"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    high_mask = severity.isin(
        (
            "high",
            "critical",
            "1",
            "p1",
            "p2",
        )
    )

    high_alerts = alerts.loc[
        high_mask
    ].copy()

    if high_alerts.empty:
        return []

    investigation_entities = (
        _entity_values(
            investigations
        )
    )

    signals = []

    for entity_id, group in (
        high_alerts.groupby(entity_column)
    ):

        entity_id = _safe_string(
            entity_id
        )

        if entity_id in investigation_entities:
            continue

        record_ids = _source_ids(group)

        signals.append(
            _make_signal(
                entity_id=entity_id,
                signal_id=(
                    f"NS-HIGH-INVESTIGATION-"
                    f"{entity_id}"
                ),
                rule_id="NS-002",
                priority="HIGH",
                reason=(
                    "High-severity or critical alerts "
                    "are present, but no investigation "
                    "evidence is available for the entity "
                    "within the supplied assessment data."
                ),
                evidence=[
                    {
                        "type": "missing_investigation_evidence",
                        "high_severity_alert_count": int(
                            len(group)
                        ),
                        "source": "alert_records",
                    }
                ],
                source_record_ids=record_ids,
                evidence_confidence="MEDIUM",
            )
        )

    return signals


# ---------------------------------------------------------------------
# Rule 3
# Investigations without escalation evidence
# ---------------------------------------------------------------------


def detect_investigation_without_escalation(
    investigations: Optional[pd.DataFrame],
    escalations: Optional[pd.DataFrame],
) -> list[dict[str, Any]]:
    """
    Detect entities with investigation activity but no escalation
    evidence.

    This is intentionally phrased as a potential evidence gap.
    It does not assume escalation was mandatory.
    """

    if investigations is None or investigations.empty:
        return []

    if escalations is None:
        escalations = pd.DataFrame()

    entity_column = _entity_column(
        investigations
    )

    if entity_column is None:
        return []

    escalation_entities = _entity_values(
        escalations
    )

    signals = []

    for entity_id, group in (
        investigations.groupby(entity_column)
    ):

        entity_id = _safe_string(
            entity_id
        )

        if entity_id in escalation_entities:
            continue

        record_ids = _source_ids(group)

        signals.append(
            _make_signal(
                entity_id=entity_id,
                signal_id=(
                    f"NS-ESCALATION-EVIDENCE-"
                    f"{entity_id}"
                ),
                rule_id="NS-003",
                priority="MEDIUM",
                reason=(
                    "Investigation activity is present, "
                    "but no escalation evidence is available "
                    "for the entity in the supplied records."
                ),
                evidence=[
                    {
                        "type": "missing_escalation_evidence",
                        "investigation_count": int(
                            len(group)
                        ),
                        "source": "investigation_records",
                    }
                ],
                source_record_ids=record_ids,
                evidence_confidence="MEDIUM",
            )
        )

    return signals


# ---------------------------------------------------------------------
# Rule 4
# Alerts without closure evidence
# ---------------------------------------------------------------------


def detect_missing_alert_closure_evidence(
    alerts: Optional[pd.DataFrame],
) -> list[dict[str, Any]]:
    """
    Detect entities with alert activity but missing closure evidence.

    The rule only evaluates closure evidence when a status field exists.
    """

    if alerts is None or alerts.empty:
        return []

    entity_column = _entity_column(alerts)

    if entity_column is None:
        return []

    if "status" not in alerts.columns:
        return []

    status = (
        alerts["status"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    closed_statuses = {
        "closed",
        "resolved",
        "complete",
        "completed",
    }

    open_statuses = {
        "open",
        "new",
        "pending",
        "in_progress",
        "investigating",
    }

    signals = []

    for entity_id, group in (
        alerts.groupby(entity_column)
    ):

        entity_id = _safe_string(
            entity_id
        )

        statuses = set(
            status.loc[group.index]
        )

        if not statuses.intersection(
            open_statuses
        ):
            continue

        if statuses.intersection(
            closed_statuses
        ):
            continue

        record_ids = _source_ids(group)

        signals.append(
            _make_signal(
                entity_id=entity_id,
                signal_id=(
                    f"NS-ALERT-CLOSURE-"
                    f"{entity_id}"
                ),
                rule_id="NS-004",
                priority="MEDIUM",
                reason=(
                    "Alert activity is present, but "
                    "the supplied records contain no "
                    "closure or resolution evidence."
                ),
                evidence=[
                    {
                        "type": "missing_closure_evidence",
                        "alert_count": int(
                            len(group)
                        ),
                        "source": "alert_records",
                    }
                ],
                source_record_ids=record_ids,
                evidence_confidence="MEDIUM",
            )
        )

    return signals


# ---------------------------------------------------------------------
# Rule 5
# Low monitoring coverage
# ---------------------------------------------------------------------


def detect_low_monitoring_coverage(
    monitoring: Optional[pd.DataFrame],
    threshold: float = DEFAULT_LOW_MONITORING_THRESHOLD,
) -> list[dict[str, Any]]:
    """
    Detect entities whose observed monitoring coverage is below
    the configured threshold.

    Coverage can be supplied as:
        0.45
    or:
        45
    """

    if monitoring is None or monitoring.empty:
        return []

    entity_column = _entity_column(
        monitoring
    )

    if entity_column is None:
        return []

    if "coverage" not in monitoring.columns:
        return []

    threshold = _safe_float(
        threshold,
        DEFAULT_LOW_MONITORING_THRESHOLD,
    )

    if threshold < 0:
        threshold = 0.0

    if threshold > 1:
        threshold = threshold / 100.0

    coverage = pd.to_numeric(
        monitoring["coverage"],
        errors="coerce",
    )

    coverage = coverage.where(
        coverage <= 1,
        coverage / 100.0,
    )

    temp = monitoring.copy()

    temp["_coverage"] = coverage

    signals = []

    for entity_id, group in (
        temp.groupby(entity_column)
    ):

        entity_id = _safe_string(
            entity_id
        )

        observed = group[
            "_coverage"
        ].dropna()

        if observed.empty:
            continue

        average_coverage = float(
            observed.mean()
        )

        if average_coverage >= threshold:
            continue

        record_ids = _source_ids(group)

        priority = (
            "HIGH"
            if average_coverage < 0.25
            else "MEDIUM"
        )

        signals.append(
            _make_signal(
                entity_id=entity_id,
                signal_id=(
                    f"NS-LOW-COVERAGE-"
                    f"{entity_id}"
                ),
                rule_id="NS-005",
                priority=priority,
                reason=(
                    "Observed monitoring coverage is "
                    "below the configured supervisory "
                    "evidence threshold."
                ),
                evidence=[
                    {
                        "type": "monitoring_coverage_gap",
                        "observed_coverage": round(
                            average_coverage,
                            4,
                        ),
                        "threshold": threshold,
                        "source": "monitoring_records",
                    }
                ],
                source_record_ids=record_ids,
                evidence_confidence="HIGH",
            )
        )

    return signals


# ---------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------


def detect_negative_space(
    alerts: Optional[pd.DataFrame] = None,
    cases: Optional[pd.DataFrame] = None,
    investigations: Optional[pd.DataFrame] = None,
    escalations: Optional[pd.DataFrame] = None,
    assets: Optional[pd.DataFrame] = None,
    monitoring: Optional[pd.DataFrame] = None,
    monitoring_threshold: float = DEFAULT_LOW_MONITORING_THRESHOLD,
) -> list[dict[str, Any]]:
    """
    Run all supported negative-space rules.

    Parameters
    ----------
    alerts:
        Alert metadata.

    cases:
        Case-management records.

    investigations:
        Investigation workflow records.

    escalations:
        Escalation records.

    assets:
        Asset/system inventory.

    monitoring:
        Monitoring and telemetry evidence.

    monitoring_threshold:
        Minimum expected monitoring coverage.

    Returns
    -------
    list[dict]
        Explainable negative-space supervisory signals.
    """

    signals: list[dict[str, Any]] = []

    # Rule NS-001
    signals.extend(
        detect_unmonitored_critical_assets(
            assets
        )
    )

    # Rule NS-002
    signals.extend(
        detect_high_severity_without_investigation(
            alerts,
            investigations,
        )
    )

    # Rule NS-003
    signals.extend(
        detect_investigation_without_escalation(
            investigations,
            escalations,
        )
    )

    # Rule NS-004
    signals.extend(
        detect_missing_alert_closure_evidence(
            alerts
        )
    )

    # Rule NS-005
    signals.extend(
        detect_low_monitoring_coverage(
            monitoring,
            threshold=monitoring_threshold,
        )
    )

    return signals


# ---------------------------------------------------------------------
# Compatibility aliases
# ---------------------------------------------------------------------


find_negative_space = detect_negative_space

run_negative_space_detection = detect_negative_space