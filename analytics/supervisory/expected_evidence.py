"""
CyberLens - Expected Evidence Model

Defines evidence normally expected for common SOC operational
capabilities and compares expected evidence with observed data.

Missing evidence is treated as a supervisory indicator for
human review, not automatic proof of control failure.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


MODEL_VERSION = "cyberlens-phase3-expected-evidence-0.2.0"


EXPECTED_EVIDENCE_MODEL: dict[str, dict[str, Any]] = {
    "threat_detection": {
        "expected_evidence": [
            "alert_records",
            "monitoring_coverage",
            "severity_distribution",
        ],
    },
    "investigation": {
        "expected_evidence": [
            "investigation_records",
            "case_records",
            "investigation_outcomes",
        ],
    },
    "escalation": {
        "expected_evidence": [
            "escalation_records",
            "escalation_status",
            "escalation_timestamps",
        ],
    },
    "incident_response": {
        "expected_evidence": [
            "case_records",
            "response_actions",
            "closure_or_resolution_evidence",
        ],
    },
    "security_operations": {
        "expected_evidence": [
            "alert_records",
            "monitoring_coverage",
            "asset_inventory",
        ],
    },
    "governance_oversight": {
        "expected_evidence": [
            "case_records",
            "investigation_records",
            "escalation_records",
        ],
    },
    "operational_discipline": {
        "expected_evidence": [
            "timeliness_metrics",
            "closure_records",
            "investigation_records",
        ],
    },
    "cyber_resilience": {
        "expected_evidence": [
            "critical_asset_inventory",
            "monitoring_coverage",
            "incident_response_records",
        ],
    },
}


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


def _has_records(
    frame: pd.DataFrame | None,
    entity_id: str,
) -> bool:
    return not _records_for_entity(frame, entity_id).empty


def _has_any_column(
    frame: pd.DataFrame | None,
    entity_id: str,
    columns: list[str],
) -> bool:
    records = _records_for_entity(frame, entity_id)

    if records.empty:
        return False

    return any(
        column in records.columns
        for column in columns
    )


def _has_non_null_column(
    frame: pd.DataFrame | None,
    entity_id: str,
    columns: list[str],
) -> bool:
    records = _records_for_entity(frame, entity_id)

    if records.empty:
        return False

    for column in columns:
        if column not in records.columns:
            continue

        if records[column].notna().any():
            return True

    return False


def _evidence_available(
    evidence_type: str,
    entity_id: str,
    *,
    alerts: pd.DataFrame | None,
    cases: pd.DataFrame | None,
    investigations: pd.DataFrame | None,
    escalations: pd.DataFrame | None,
    assets: pd.DataFrame | None,
    monitoring: pd.DataFrame | None,
) -> tuple[bool, list[str]]:
    """
    Determine whether a specific expected evidence type is
    actually available.

    Returns:
        (available, source_record_ids)
    """

    if evidence_type == "alert_records":
        return (
            _has_records(alerts, entity_id),
            _source_ids(alerts, entity_id),
        )

    if evidence_type == "severity_distribution":
        available = _has_non_null_column(
            alerts,
            entity_id,
            ["severity", "priority", "alert_severity"],
        )

        return available, _source_ids(alerts, entity_id)

    if evidence_type == "monitoring_coverage":
        available = _has_non_null_column(
            monitoring,
            entity_id,
            [
                "coverage",
                "monitoring_coverage",
                "coverage_rate",
                "coverage_percent",
                "monitoring_status",
            ],
        )

        return available, _source_ids(monitoring, entity_id)

    if evidence_type == "investigation_records":
        return (
            _has_records(investigations, entity_id),
            _source_ids(investigations, entity_id),
        )

    if evidence_type == "case_records":
        return (
            _has_records(cases, entity_id),
            _source_ids(cases, entity_id),
        )

    if evidence_type == "investigation_outcomes":
        available = _has_non_null_column(
            investigations,
            entity_id,
            [
                "outcome",
                "investigation_outcome",
                "disposition",
                "result",
            ],
        )

        return available, _source_ids(investigations, entity_id)

    if evidence_type == "escalation_records":
        return (
            _has_records(escalations, entity_id),
            _source_ids(escalations, entity_id),
        )

    if evidence_type == "escalation_status":
        available = _has_non_null_column(
            escalations,
            entity_id,
            [
                "status",
                "escalation_status",
                "state",
            ],
        )

        return available, _source_ids(escalations, entity_id)

    if evidence_type == "escalation_timestamps":
        available = _has_non_null_column(
            escalations,
            entity_id,
            [
                "timestamp",
                "created_at",
                "escalated_at",
                "escalation_timestamp",
            ],
        )

        return available, _source_ids(escalations, entity_id)

    if evidence_type == "response_actions":
        available = _has_non_null_column(
            cases,
            entity_id,
            [
                "response_action",
                "response_actions",
                "action",
                "remediation_action",
            ],
        )

        return available, _source_ids(cases, entity_id)

    if evidence_type == "closure_or_resolution_evidence":
        available = _has_non_null_column(
            cases,
            entity_id,
            [
                "status",
                "closure_status",
                "closed_at",
                "resolution",
                "resolved_at",
            ],
        )

        return available, _source_ids(cases, entity_id)

    if evidence_type == "asset_inventory":
        return (
            _has_records(assets, entity_id),
            _source_ids(assets, entity_id),
        )

    if evidence_type == "critical_asset_inventory":
        records = _records_for_entity(assets, entity_id)

        if records.empty:
            return False, []

        critical_columns = [
            "criticality",
            "asset_criticality",
            "priority",
        ]

        for column in critical_columns:
            if column not in records.columns:
                continue

            values = (
                records[column]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            if values.isin(
                ["critical", "high", "criticality-high"]
            ).any():
                return True, _source_ids(assets, entity_id)

        return False, _source_ids(assets, entity_id)

    if evidence_type == "incident_response_records":
        available = (
            _has_records(cases, entity_id)
            or _has_records(investigations, entity_id)
        )

        source_ids = (
            _source_ids(cases, entity_id)
            + _source_ids(investigations, entity_id)
        )

        return available, sorted(set(source_ids))

    if evidence_type == "closure_records":
        alert_closure = _has_non_null_column(
            alerts,
            entity_id,
            [
                "closed_at",
                "closure_time",
                "closure_timestamp",
                "resolution",
                "resolved_at",
                "status",
            ],
        )

        case_closure = _has_non_null_column(
            cases,
            entity_id,
            [
                "closed_at",
                "closure_time",
                "closure_timestamp",
                "resolution",
                "resolved_at",
                "status",
            ],
        )

        source_ids = (
            _source_ids(alerts, entity_id)
            + _source_ids(cases, entity_id)
        )

        return (
            alert_closure or case_closure,
            sorted(set(source_ids)),
        )

    if evidence_type == "timeliness_metrics":
        timestamp_columns = [
            "created_at",
            "opened_at",
            "acknowledged_at",
            "closed_at",
            "resolved_at",
            "investigation_started_at",
            "investigation_completed_at",
        ]

        available = (
            _has_any_column(
                alerts,
                entity_id,
                timestamp_columns,
            )
            or _has_any_column(
                cases,
                entity_id,
                timestamp_columns,
            )
            or _has_any_column(
                investigations,
                entity_id,
                timestamp_columns,
            )
        )

        source_ids = (
            _source_ids(alerts, entity_id)
            + _source_ids(cases, entity_id)
            + _source_ids(investigations, entity_id)
        )

        return available, sorted(set(source_ids))

    return False, []


def _make_signal(
    *,
    entity_id: str,
    capability: str,
    expected: list[str],
    observed: list[str],
    missing: list[str],
    source_record_ids: list[str],
) -> dict[str, Any]:

    if len(missing) == len(expected):
        priority = "HIGH"
    else:
        priority = "MEDIUM"

    return {
        "signal_id": (
            f"EE-{capability.upper().replace('_', '-')}-{entity_id}"
        ),
        "signal_type": "EXPECTED_EVIDENCE",
        "rule_id": "EE-001",
        "category": "EVIDENCE_EXPECTATION",
        "priority": priority,
        "reason": (
            f"Expected evidence for "
            f"{capability.replace('_', ' ')} "
            "is partially or fully absent from the supplied "
            "assessment data."
        ),
        "evidence": [
            {
                "type": "expected_evidence",
                "capability": capability,
                "expected": expected,
                "observed": observed,
                "missing": missing,
            }
        ],
        "source_record_ids": sorted(set(source_record_ids)),
        "historical_context": {},
        "peer_context": {},
        "evidence_confidence": (
            "HIGH" if observed else "MEDIUM"
        ),
        "rule_model_version": MODEL_VERSION,
        "entity_id": entity_id,
        "human_review_required": True,
    }


def evaluate_expected_evidence(
    *,
    alerts: pd.DataFrame | None = None,
    cases: pd.DataFrame | None = None,
    investigations: pd.DataFrame | None = None,
    escalations: pd.DataFrame | None = None,
    assets: pd.DataFrame | None = None,
    monitoring: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """
    Compare expected evidence with observed evidence.

    Missing evidence is surfaced as a supervisory signal for
    human examination.
    """

    frames = [
        alerts,
        cases,
        investigations,
        escalations,
        assets,
        monitoring,
    ]

    entity_ids = _entities(*frames)

    signals: list[dict[str, Any]] = []

    for entity_id in entity_ids:

        for capability, specification in EXPECTED_EVIDENCE_MODEL.items():

            expected = specification["expected_evidence"]

            observed: list[str] = []
            missing: list[str] = []
            source_record_ids: list[str] = []

            for evidence_type in expected:

                available, evidence_source_ids = _evidence_available(
                    evidence_type,
                    entity_id,
                    alerts=alerts,
                    cases=cases,
                    investigations=investigations,
                    escalations=escalations,
                    assets=assets,
                    monitoring=monitoring,
                )

                if available:
                    observed.append(evidence_type)
                else:
                    missing.append(evidence_type)

                source_record_ids.extend(
                    evidence_source_ids
                )

            if not missing:
                continue

            signals.append(
                _make_signal(
                    entity_id=entity_id,
                    capability=capability,
                    expected=expected,
                    observed=observed,
                    missing=missing,
                    source_record_ids=source_record_ids,
                )
            )

    return signals


def get_expected_evidence_model() -> dict[str, dict[str, Any]]:
    """Return the configured expected evidence model."""

    return EXPECTED_EVIDENCE_MODEL.copy()


# Integration aliases.
build_expected_evidence_signals = evaluate_expected_evidence
run_expected_evidence_model = evaluate_expected_evidence