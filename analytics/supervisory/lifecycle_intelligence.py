"""
CyberLens - SOC Operational Lifecycle Intelligence

Analyzes the operational relationship between alerts, investigations,
escalations, cases, and closure/resolution evidence.

This module identifies lifecycle inconsistencies that may require
supervisory examination. It does not assume that every alert must
follow every lifecycle stage.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


MODEL_VERSION = "cyberlens-phase3-lifecycle-0.1.0"


def _safe_string(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _entity_column(df: pd.DataFrame | None) -> str | None:
    if df is None or df.empty:
        return None

    for column in ("entity_id", "cse_id", "organization_id"):
        if column in df.columns:
            return column

    return None


def _record_id_column(df: pd.DataFrame | None) -> str | None:
    if df is None or df.empty:
        return None

    for column in (
        "record_id",
        "alert_id",
        "case_id",
        "investigation_id",
        "escalation_id",
    ):
        if column in df.columns:
            return column

    return None


def _entities(*frames: pd.DataFrame | None) -> list[str]:
    entities: set[str] = set()

    for frame in frames:
        column = _entity_column(frame)

        if column is None:
            continue

        for value in frame[column].dropna():
            entity_id = _safe_string(value)

            if entity_id:
                entities.add(entity_id)

    return sorted(entities)


def _records_for_entity(
    frame: pd.DataFrame | None,
    entity_id: str,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    column = _entity_column(frame)

    if column is None:
        return pd.DataFrame()

    return frame[
        frame[column].astype(str).str.strip() == entity_id
    ].copy()


def _source_ids(
    frame: pd.DataFrame | None,
    entity_id: str,
) -> list[str]:
    records = _records_for_entity(frame, entity_id)

    if records.empty:
        return []

    column = _record_id_column(records)

    if column is None:
        return []

    return [
        _safe_string(value)
        for value in records[column].dropna()
        if _safe_string(value)
    ]


def _make_signal(
    *,
    entity_id: str,
    rule_id: str,
    priority: str,
    reason: str,
    evidence: dict[str, Any],
    source_record_ids: list[str],
) -> dict[str, Any]:
    return {
        "signal_id": (
            f"{rule_id}-{entity_id}"
        ),
        "signal_type": "LIFECYCLE_INTELLIGENCE",
        "rule_id": rule_id,
        "category": "OPERATIONAL_LIFECYCLE",
        "priority": priority,
        "reason": reason,
        "evidence": [evidence],
        "source_record_ids": sorted(set(source_record_ids)),
        "historical_context": {},
        "peer_context": {},
        "evidence_confidence": (
            "HIGH" if source_record_ids else "MEDIUM"
        ),
        "rule_model_version": MODEL_VERSION,
        "entity_id": entity_id,
        "human_review_required": True,
    }


def detect_alerts_without_investigation(
    *,
    alerts: pd.DataFrame | None,
    investigations: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    """
    Identify entities with alert activity but no investigation evidence.

    This is a supervisory indicator and does not assert that every
    alert necessarily required investigation.
    """

    signals = []

    for entity_id in _entities(alerts):

        alert_records = _records_for_entity(
            alerts,
            entity_id,
        )

        investigation_records = _records_for_entity(
            investigations,
            entity_id,
        )

        if alert_records.empty or not investigation_records.empty:
            continue

        source_ids = _source_ids(
            alerts,
            entity_id,
        )

        signals.append(
            _make_signal(
                entity_id=entity_id,
                rule_id="LIFE-001",
                priority="HIGH",
                reason=(
                    "Alert activity is present, but no investigation "
                    "evidence is available for the entity in the "
                    "supplied assessment data."
                ),
                evidence={
                    "type": "missing_lifecycle_stage",
                    "upstream_stage": "alert",
                    "missing_stage": "investigation",
                    "alert_count": len(alert_records),
                },
                source_record_ids=source_ids,
            )
        )

    return signals


def detect_investigations_without_escalation(
    *,
    investigations: pd.DataFrame | None,
    escalations: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    """
    Identify investigations without escalation evidence.

    Absence of escalation is not automatically treated as an error.
    The signal is intended for supervisory examination.
    """

    signals = []

    for entity_id in _entities(investigations):

        investigation_records = _records_for_entity(
            investigations,
            entity_id,
        )

        escalation_records = _records_for_entity(
            escalations,
            entity_id,
        )

        if investigation_records.empty or not escalation_records.empty:
            continue

        source_ids = _source_ids(
            investigations,
            entity_id,
        )

        signals.append(
            _make_signal(
                entity_id=entity_id,
                rule_id="LIFE-002",
                priority="MEDIUM",
                reason=(
                    "Investigation activity is present, but no "
                    "escalation evidence is available in the "
                    "supplied assessment data."
                ),
                evidence={
                    "type": "lifecycle_transition_gap",
                    "upstream_stage": "investigation",
                    "next_stage": "escalation",
                    "investigation_count": len(
                        investigation_records
                    ),
                    "escalation_count": 0,
                },
                source_record_ids=source_ids,
            )
        )

    return signals


def detect_escalation_without_investigation(
    *,
    investigations: pd.DataFrame | None,
    escalations: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    """
    Identify escalation evidence without corresponding investigation
    evidence.
    """

    signals = []

    for entity_id in _entities(escalations):

        escalation_records = _records_for_entity(
            escalations,
            entity_id,
        )

        investigation_records = _records_for_entity(
            investigations,
            entity_id,
        )

        if escalation_records.empty or not investigation_records.empty:
            continue

        source_ids = _source_ids(
            escalations,
            entity_id,
        )

        signals.append(
            _make_signal(
                entity_id=entity_id,
                rule_id="LIFE-003",
                priority="HIGH",
                reason=(
                    "Escalation evidence is present, but no "
                    "corresponding investigation evidence is "
                    "available for the entity."
                ),
                evidence={
                    "type": "orphan_lifecycle_stage",
                    "stage": "escalation",
                    "missing_preceding_stage": "investigation",
                    "escalation_count": len(
                        escalation_records
                    ),
                },
                source_record_ids=source_ids,
            )
        )

    return signals


def detect_cases_without_investigation(
    *,
    cases: pd.DataFrame | None,
    investigations: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    """
    Identify case-management activity without investigation evidence.
    """

    signals = []

    for entity_id in _entities(cases):

        case_records = _records_for_entity(
            cases,
            entity_id,
        )

        investigation_records = _records_for_entity(
            investigations,
            entity_id,
        )

        if case_records.empty or not investigation_records.empty:
            continue

        source_ids = _source_ids(
            cases,
            entity_id,
        )

        signals.append(
            _make_signal(
                entity_id=entity_id,
                rule_id="LIFE-004",
                priority="MEDIUM",
                reason=(
                    "Case-management activity is present, but "
                    "no investigation evidence is available "
                    "for the entity."
                ),
                evidence={
                    "type": "case_investigation_gap",
                    "case_count": len(case_records),
                    "investigation_count": 0,
                },
                source_record_ids=source_ids,
            )
        )

    return signals


def detect_closed_without_resolution_evidence(
    *,
    cases: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    """
    Identify closed/resolved cases where no supporting resolution
    or response evidence is visible in the supplied records.
    """

    signals = []

    for entity_id in _entities(cases):

        case_records = _records_for_entity(
            cases,
            entity_id,
        )

        if case_records.empty:
            continue

        status_column = next(
            (
                column
                for column in (
                    "status",
                    "case_status",
                    "state",
                )
                if column in case_records.columns
            ),
            None,
        )

        if status_column is None:
            continue

        closed_mask = (
            case_records[status_column]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(
                [
                    "closed",
                    "resolved",
                    "completed",
                ]
            )
        )

        closed_records = case_records[closed_mask]

        if closed_records.empty:
            continue

        resolution_columns = [
            "resolution",
            "resolution_reason",
            "response_action",
            "response_actions",
            "remediation_action",
            "closed_at",
            "resolved_at",
        ]

        available_resolution = False

        for column in resolution_columns:

            if column not in closed_records.columns:
                continue

            if closed_records[column].notna().any():
                available_resolution = True
                break

        if available_resolution:
            continue

        source_ids = _source_ids(
            cases,
            entity_id,
        )

        signals.append(
            _make_signal(
                entity_id=entity_id,
                rule_id="LIFE-005",
                priority="HIGH",
                reason=(
                    "Closed or resolved case activity is present, "
                    "but supporting resolution or response evidence "
                    "is not visible in the supplied records."
                ),
                evidence={
                    "type": "closure_without_resolution_evidence",
                    "closed_case_count": len(closed_records),
                    "resolution_evidence_found": False,
                },
                source_record_ids=source_ids,
            )
        )

    return signals


def detect_lifecycle_intelligence(
    *,
    alerts: pd.DataFrame | None = None,
    cases: pd.DataFrame | None = None,
    investigations: pd.DataFrame | None = None,
    escalations: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """
    Run all SOC lifecycle intelligence checks.
    """

    signals: list[dict[str, Any]] = []

    signals.extend(
        detect_alerts_without_investigation(
            alerts=alerts,
            investigations=investigations,
        )
    )

    signals.extend(
        detect_investigations_without_escalation(
            investigations=investigations,
            escalations=escalations,
        )
    )

    signals.extend(
        detect_escalation_without_investigation(
            investigations=investigations,
            escalations=escalations,
        )
    )

    signals.extend(
        detect_cases_without_investigation(
            cases=cases,
            investigations=investigations,
        )
    )

    signals.extend(
        detect_closed_without_resolution_evidence(
            cases=cases,
        )
    )

    return signals


# Integration aliases.
run_lifecycle_intelligence = detect_lifecycle_intelligence
build_lifecycle_signals = detect_lifecycle_intelligence