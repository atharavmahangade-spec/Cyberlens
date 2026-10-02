"""
CyberLens - Historical Self-Benchmarking

Compares an entity's current operational behaviour against its
own historical assessment periods.

Historical deviation is treated as a supervisory indicator for
human examination, not automatic proof of control failure.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


MODEL_VERSION = "cyberlens-phase3-historical-benchmarking-0.1.0"


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


def _period_column(features: pd.DataFrame) -> str | None:
    for column in (
        "assessment_period",
        "assessment_id",
        "period",
        "period_id",
        "assessment_date",
    ):
        if column in features.columns:
            return column

    return None


def _make_signal(
    *,
    entity_id: str,
    feature: str,
    current_value: float,
    historical_mean: float,
    historical_median: float,
    historical_period_count: int,
    change_percent: float,
    direction: str,
    priority: str,
    current_period: str,
) -> dict[str, Any]:

    return {
        "signal_id": (
            f"HIST-001-{feature.upper()}-{entity_id}"
            f"-{current_period}"
        ),
        "signal_type": "HISTORICAL_DEVIATION",
        "rule_id": "HIST-001",
        "category": "HISTORICAL_BENCHMARK",
        "priority": priority,
        "reason": (
            f"{feature} has changed materially relative "
            "to the entity's historical baseline."
        ),
        "evidence": [
            {
                "type": "historical_deviation",
                "feature": feature,
                "current_value": current_value,
                "historical_mean": historical_mean,
                "historical_median": historical_median,
                "change_percent": round(
                    change_percent,
                    2,
                ),
                "direction": direction,
                "historical_period_count": historical_period_count,
                "current_period": current_period,
            }
        ],
        "source_record_ids": [],
        "historical_context": {
            "historical_period_count": historical_period_count,
            "historical_mean": historical_mean,
            "historical_median": historical_median,
        },
        "peer_context": {},
        "evidence_confidence": (
            "HIGH"
            if historical_period_count >= 4
            else "MEDIUM"
        ),
        "rule_model_version": MODEL_VERSION,
        "entity_id": entity_id,
        "human_review_required": True,
    }


def detect_historical_deviations(
    features: pd.DataFrame,
    *,
    feature_columns: list[str] | None = None,
    min_historical_periods: int = 3,
    deviation_threshold_percent: float = 25.0,
) -> list[dict[str, Any]]:
    """
    Compare each entity's current period against its own
    historical periods.

    Expected input:
        One row per entity per assessment period.

    Required columns:
        entity_id
        assessment_period (or supported period column)

    The current period is determined by the latest period value
    within each entity.
    """

    if features.empty:
        return []

    entity_column = _entity_column(features)

    if entity_column is None:
        raise ValueError(
            "Features must contain an entity identifier column."
        )

    period_column = _period_column(features)

    if period_column is None:
        raise ValueError(
            "Features must contain an assessment period column."
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

    working["_period_sort"] = working[
        period_column
    ].astype(str)

    signals: list[dict[str, Any]] = []

    for entity_id, entity_group in working.groupby(
        entity_column,
        sort=False,
    ):

        entity_id = _safe_string(entity_id)

        if not entity_id:
            continue

        entity_group = entity_group.sort_values(
            "_period_sort"
        )

        if len(entity_group) < min_historical_periods + 1:
            continue

        current_row = entity_group.iloc[-1]

        historical_rows = entity_group.iloc[:-1]

        current_period = _safe_string(
            current_row[period_column]
        )

        for feature in available_features:

            current_value = _safe_float(
                current_row[feature]
            )

            if current_value is None:
                continue

            historical_values = pd.to_numeric(
                historical_rows[feature],
                errors="coerce",
            ).dropna()

            historical_period_count = len(
                historical_values
            )

            if historical_period_count < min_historical_periods:
                continue

            historical_mean = float(
                historical_values.mean()
            )

            historical_median = float(
                historical_values.median()
            )

            if historical_median == 0:

                if current_value == 0:
                    change_percent = 0.0
                else:
                    change_percent = 100.0

            else:

                change_percent = abs(
                    (
                        current_value
                        - historical_median
                    )
                    / historical_median
                ) * 100.0

            if change_percent < deviation_threshold_percent:
                continue

            if current_value > historical_median:
                direction = "above_historical_baseline"
            elif current_value < historical_median:
                direction = "below_historical_baseline"
            else:
                direction = "aligned_with_historical_baseline"

            if change_percent >= 50:
                priority = "HIGH"
            else:
                priority = "MEDIUM"

            signals.append(
                _make_signal(
                    entity_id=entity_id,
                    feature=feature,
                    current_value=current_value,
                    historical_mean=historical_mean,
                    historical_median=historical_median,
                    historical_period_count=(
                        historical_period_count
                    ),
                    change_percent=change_percent,
                    direction=direction,
                    priority=priority,
                    current_period=current_period,
                )
            )

    return signals


def build_historical_benchmark_signals(
    features: pd.DataFrame,
    *,
    feature_columns: list[str] | None = None,
    min_historical_periods: int = 3,
    deviation_threshold_percent: float = 25.0,
) -> list[dict[str, Any]]:
    """Integration wrapper for historical benchmarking."""

    return detect_historical_deviations(
        features,
        feature_columns=feature_columns,
        min_historical_periods=min_historical_periods,
        deviation_threshold_percent=deviation_threshold_percent,
    )


# Convenient integration alias.
run_historical_benchmarking = detect_historical_deviations