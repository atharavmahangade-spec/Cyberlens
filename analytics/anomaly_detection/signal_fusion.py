"""
CyberLens - Anomaly Signal Fusion
=================================

Phase 4: Anomaly & Behaviour Analytics

Combines statistical anomaly findings and Isolation Forest results
into explainable supervisory signals.

Important:
- These signals support supervisory review.
- They are NOT attack classifications.
- They are NOT probabilities of compromise.
- Every signal should be traceable to available evidence.
- Processing is fully offline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


MODEL_VERSION = "cyberlens-phase4-0.2.0"

# Transparent review-support scoring weights.
STATISTICAL_WEIGHT = 0.65
ISOLATION_FOREST_WEIGHT = 0.35

# Review-priority thresholds.
HIGH_PRIORITY_THRESHOLD = 75.0
MEDIUM_PRIORITY_THRESHOLD = 40.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float safely."""
    try:
        result = float(value)

        if pd.isna(result):
            return default

        return result

    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    """Convert common boolean representations safely."""
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "y",
        }

    if isinstance(value, (int, float)):
        return bool(value)

    return False


def _normalize_entity_id(entity: Any) -> str:
    """Create a stable, readable entity identifier."""
    value = str(entity).strip()

    if not value:
        return "unknown-entity"

    return value


def _collect_source_ids(row: dict[str, Any]) -> list[str]:
    """
    Extract source record identifiers from a feature row.

    Supports:
    - source_record_ids
    - record_ids
    - a single string ID
    - lists/tuples/sets of IDs
    """
    source_ids: list[str] = []

    for column in ("source_record_ids", "record_ids"):
        value = row.get(column)

        if value is None:
            continue

        if isinstance(value, (list, tuple, set)):
            source_ids.extend(
                str(item).strip()
                for item in value
                if str(item).strip()
            )
        else:
            value_str = str(value).strip()

            if value_str:
                source_ids.append(value_str)

    return sorted(set(source_ids))


def _validate_features(features: pd.DataFrame) -> str:
    """Validate the minimum feature schema."""
    if not isinstance(features, pd.DataFrame):
        raise TypeError("features must be a pandas DataFrame")

    if features.empty:
        return "entity_id"

    if "entity_id" in features.columns:
        return "entity_id"

    if "cse_id" in features.columns:
        return "cse_id"

    raise ValueError(
        "features must contain either 'entity_id' or 'cse_id'"
    )


def _build_statistical_index(
    statistical_findings: pd.DataFrame | None,
) -> dict[str, list[dict[str, Any]]]:
    """Group statistical findings by entity."""
    if (
        statistical_findings is None
        or not isinstance(statistical_findings, pd.DataFrame)
        or statistical_findings.empty
    ):
        return {}

    if "entity_id" not in statistical_findings.columns:
        return {}

    grouped: dict[str, list[dict[str, Any]]] = {}

    for row in statistical_findings.to_dict(orient="records"):
        entity = _normalize_entity_id(row.get("entity_id"))

        grouped.setdefault(entity, []).append(row)

    return grouped


def _build_isolation_forest_index(
    isolation_results: pd.DataFrame | None,
) -> dict[str, dict[str, Any]]:
    """Index Isolation Forest results by entity."""
    if (
        isolation_results is None
        or not isinstance(isolation_results, pd.DataFrame)
        or isolation_results.empty
    ):
        return {}

    if "entity_id" not in isolation_results.columns:
        return {}

    indexed: dict[str, dict[str, Any]] = {}

    for row in isolation_results.to_dict(orient="records"):
        entity = _normalize_entity_id(row.get("entity_id"))
        indexed[entity] = row

    return indexed


def _priority_from_score(score: float) -> str:
    """Convert review-support score into a transparent priority."""
    if score >= HIGH_PRIORITY_THRESHOLD:
        return "HIGH"

    if score >= MEDIUM_PRIORITY_THRESHOLD:
        return "MEDIUM"

    return "LOW"


def _build_evidence(
    statistical_rows: list[dict[str, Any]],
    isolation_row: dict[str, Any] | None,
    isolation_flag: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build explainable evidence and human-readable reasons."""
    evidence: list[dict[str, Any]] = []
    reasons: list[str] = []

    for item in statistical_rows:
        feature = str(item.get("feature", "unknown_feature"))

        direction = str(
            item.get("direction", "unusual")
        ).lower()

        evidence.append(
            {
                "feature": feature,
                "observed_value": item.get("value"),
                "peer_median": item.get("median"),
                "modified_z": item.get("modified_z"),
                "lower_fence": item.get("lower_fence"),
                "upper_fence": item.get("upper_fence"),
                "direction": direction,
                "method": item.get(
                    "method",
                    "statistical_analysis",
                ),
            }
        )

        reasons.append(
            f"{feature} is unusually {direction} "
            "versus the assessed peer group"
        )

    if isolation_flag and isolation_row is not None:
        evidence.append(
            {
                "method": "IsolationForest",
                "anomaly_score": _safe_float(
                    isolation_row.get("if_anomaly_score")
                ),
                "prediction": isolation_row.get(
                    "if_prediction"
                ),
            }
        )

        reasons.append(
            "Isolation Forest identified an unusual "
            "combination of operational features"
        )

    return evidence, reasons


def build_anomaly_signals(
    features: pd.DataFrame,
    statistical_findings: pd.DataFrame | None,
    isolation_results: pd.DataFrame | None,
    assessment_id: str = "assessment-unknown",
    version: str = MODEL_VERSION,
) -> list[dict[str, Any]]:
    """
    Create one explainable supervisory anomaly signal per entity.

    The score is a review-support indicator, not a probability,
    confidence percentage, attack score, or compromise prediction.

    Statistical findings contribute up to 65%.
    Isolation Forest contributes up to 35%.
    """

    if not isinstance(features, pd.DataFrame):
        raise TypeError("features must be a pandas DataFrame")

    if features.empty:
        return []

    id_column = _validate_features(features)

    statistical_index = _build_statistical_index(
        statistical_findings
    )

    isolation_index = _build_isolation_forest_index(
        isolation_results
    )

    signals: list[dict[str, Any]] = []

    for row in features.to_dict(orient="records"):
        entity = _normalize_entity_id(row.get(id_column))

        statistical_rows = statistical_index.get(
            entity,
            [],
        )

        isolation_row = isolation_index.get(entity)

        statistical_count = len(statistical_rows)

        isolation_flag = False

        if isolation_row is not None:
            isolation_flag = _safe_bool(
                isolation_row.get("if_anomaly")
            )

        # No anomaly signal from either analytical method.
        if statistical_count == 0 and not isolation_flag:
            continue

        # Statistical contribution is capped at 100%.
        statistical_component = min(
            statistical_count / 3.0,
            1.0,
        )

        isolation_component = (
            1.0 if isolation_flag else 0.0
        )

        score = round(
            100.0
            * (
                STATISTICAL_WEIGHT
                * statistical_component
                + ISOLATION_FOREST_WEIGHT
                * isolation_component
            ),
            2,
        )

        priority = _priority_from_score(score)

        evidence, reasons = _build_evidence(
            statistical_rows,
            isolation_row,
            isolation_flag,
        )

        reason = (
            "; ".join(dict.fromkeys(reasons))
            if reasons
            else "Unusual operational behaviour detected"
        )

        source_record_ids = _collect_source_ids(row)

        # Confidence describes evidence availability/agreement,
        # not model probability.
        if statistical_count > 0 and isolation_flag:
            evidence_confidence = "MEDIUM"
        elif statistical_count > 0:
            evidence_confidence = "LOW"
        elif isolation_flag:
            evidence_confidence = "LOW"
        else:
            evidence_confidence = "INSUFFICIENT"

        signal_id = (
            f"ANOM-{assessment_id}-{entity}"
        )

        signals.append(
            {
                "signal_id": signal_id,
                "signal_type": "OPERATIONAL_ANOMALY",
                "rule_id": "ML-STAT-001",
                "category": "ANOMALY_BEHAVIOUR",
                "priority": priority,
                "anomaly_score": score,
                "reason": reason,
                "evidence": evidence,
                "source_record_ids": source_record_ids,
                "historical_context": {},
                "peer_context": {
                    "statistical_anomaly_count": (
                        statistical_count
                    )
                },
                "evidence_confidence": evidence_confidence,
                "rule_model_version": version,
                "assessment_id": assessment_id,
                "entity_id": entity,
                "generated_at": (
                    datetime.now(timezone.utc)
                    .isoformat()
                ),
                "human_review_required": True,
            }
        )

    return signals


def score_anomalies(
    features: pd.DataFrame,
    statistical_findings: pd.DataFrame | None,
    isolation_results: pd.DataFrame | None,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    DataFrame wrapper around build_anomaly_signals.

    Useful for exporting anomaly signals to CSV/Parquet
    or passing them to later CyberLens modules.
    """
    signals = build_anomaly_signals(
        features=features,
        statistical_findings=statistical_findings,
        isolation_results=isolation_results,
        **kwargs,
    )

    return pd.DataFrame(signals)