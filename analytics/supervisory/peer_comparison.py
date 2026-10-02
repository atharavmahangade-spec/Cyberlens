"""
CyberLens - Peer Comparison & Benchmarking

Compares an entity's operational behaviour against its assessed
peer group using measurable supervisory features.

The module identifies statistically meaningful peer deviations.
A deviation is a supervisory indicator for human examination,
not an automatic finding of control failure.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


MODEL_VERSION = "cyberlens-phase3-peer-comparison-0.1.0"


DEFAULT_FEATURES = [
    "alert_count",
    "case_count",
    "investigation_count",
    "escalation_count",
    "alert_closure_rate",
    "non_escalation_rate",
    "investigations_per_alert",
    "investigations_per_case",
    "escalation_rate",
    "median_acknowledgement_hours",
    "mean_acknowledgement_hours",
    "median_alert_closure_hours",
    "mean_alert_closure_hours",
    "monitoring_coverage",
    "telemetry_availability_rate",
    "critical_asset_rate",
    "critical_asset_monitoring_rate",
]


def _safe_string(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _safe_float(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _entity_column(features: pd.DataFrame) -> str | None:
    for column in (
        "entity_id",
        "cse_id",
        "organization_id",
    ):
        if column in features.columns:
            return column

    return None


def _percent_difference(
    value: float,
    reference: float,
) -> float:
    if reference == 0:
        if value == 0:
            return 0.0
        return 100.0

    return abs((value - reference) / reference) * 100.0


def _direction(
    value: float,
    reference: float,
) -> str:
    if value > reference:
        return "above_peer_baseline"

    if value < reference:
        return "below_peer_baseline"

    return "aligned_with_peer_baseline"


def _make_signal(
    *,
    entity_id: str,
    feature: str,
    value: float,
    peer_median: float,
    peer_mean: float,
    peer_count: int,
    deviation_percent: float,
    direction: str,
    priority: str,
) -> dict[str, Any]:

    return {
        "signal_id": (
            f"PEER-001-{feature.upper()}-{entity_id}"
        ),
        "signal_type": "PEER_COMPARISON",
        "rule_id": "PEER-001",
        "category": "PEER_DEVIATION",
        "priority": priority,
        "reason": (
            f"{feature} deviates materially from the "
            "peer-group baseline."
        ),
        "evidence": [
            {
                "type": "peer_deviation",
                "feature": feature,
                "entity_value": value,
                "peer_median": peer_median,
                "peer_mean": peer_mean,
                "deviation_percent": round(
                    deviation_percent,
                    2,
                ),
                "direction": direction,
                "peer_count": peer_count,
            }
        ],
        "source_record_ids": [],
        "historical_context": {},
        "peer_context": {
            "peer_count": peer_count,
            "peer_median": peer_median,
            "peer_mean": peer_mean,
        },
        "evidence_confidence": (
            "HIGH" if peer_count >= 10 else "MEDIUM"
        ),
        "rule_model_version": MODEL_VERSION,
        "entity_id": entity_id,
        "human_review_required": True,
    }


def detect_peer_deviations(
    features: pd.DataFrame,
    *,
    feature_columns: list[str] | None = None,
    min_peer_group_size: int = 5,
    deviation_threshold_percent: float = 25.0,
) -> list[dict[str, Any]]:
    """
    Compare each entity against the median and mean of its peer group.

    The current implementation treats all entities in the supplied
    assessment dataset as the peer group.

    A feature is flagged when the entity differs from the peer median
    by at least deviation_threshold_percent.

    The entity itself is excluded from the peer baseline.
    """

    if features.empty:
        return []

    entity_column = _entity_column(features)

    if entity_column is None:
        raise ValueError(
            "Features must contain an entity identifier column."
        )

    selected_features = (
        feature_columns
        if feature_columns is not None
        else DEFAULT_FEATURES
    )

    available_features = [
        feature
        for feature in selected_features
        if feature in features.columns
    ]

    if not available_features:
        return []

    working = features.copy()

    signals: list[dict[str, Any]] = []

    for index, row in working.iterrows():

        entity_id = _safe_string(
            row[entity_column]
        )

        if not entity_id:
            continue

        for feature in available_features:

            entity_value = _safe_float(
                row[feature]
            )

            if entity_value is None:
                continue

            peer_values = pd.to_numeric(
                working.loc[
                    working.index != index,
                    feature,
                ],
                errors="coerce",
            ).dropna()

            peer_count = len(peer_values)

            if peer_count < min_peer_group_size:
                continue

            peer_median = float(
                peer_values.median()
            )

            peer_mean = float(
                peer_values.mean()
            )

            deviation_percent = _percent_difference(
                entity_value,
                peer_median,
            )

            if deviation_percent < deviation_threshold_percent:
                continue

            direction = _direction(
                entity_value,
                peer_median,
            )

            if deviation_percent >= 50:
                priority = "HIGH"
            else:
                priority = "MEDIUM"

            signals.append(
                _make_signal(
                    entity_id=entity_id,
                    feature=feature,
                    value=entity_value,
                    peer_median=peer_median,
                    peer_mean=peer_mean,
                    peer_count=peer_count,
                    deviation_percent=deviation_percent,
                    direction=direction,
                    priority=priority,
                )
            )

    return signals


def build_peer_comparison_signals(
    features: pd.DataFrame,
    *,
    feature_columns: list[str] | None = None,
    min_peer_group_size: int = 5,
    deviation_threshold_percent: float = 25.0,
) -> list[dict[str, Any]]:
    """Integration wrapper for peer comparison."""

    return detect_peer_deviations(
        features,
        feature_columns=feature_columns,
        min_peer_group_size=min_peer_group_size,
        deviation_threshold_percent=deviation_threshold_percent,
    )


# Convenient integration alias.
run_peer_comparison = detect_peer_deviations