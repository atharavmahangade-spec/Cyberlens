"""
CyberLens - Statistical Anomaly Detection
==========================================

Phase 4: Anomaly & Behaviour Analytics

Detects unusual operational behaviour by comparing entity-level
features against the assessed peer distribution.

Methods:
- Median / MAD modified Z-score
- IQR fences

Important:
- Findings are supervisory indicators, not confirmed violations.
- Findings are not attack classifications.
- Statistical findings are passed to signal_fusion.py.
- Processing is fully offline.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


DEFAULT_Z_THRESHOLD = 3.0
DEFAULT_IQR_MULTIPLIER = 1.5
DEFAULT_MIN_GROUP_SIZE = 5
MIN_STATISTICAL_GROUP_SIZE = 3


OUTPUT_COLUMNS = [
    "entity_id",
    "feature",
    "value",
    "median",
    "modified_z",
    "lower_fence",
    "upper_fence",
    "direction",
    "method",
    "peer_count",
]


def _mad(values: pd.Series) -> float:
    """Calculate Median Absolute Deviation."""
    median = float(values.median())

    return float(
        (values - median).abs().median()
    )


def _resolve_entity_column(
    features: pd.DataFrame,
) -> str:
    """Resolve the supported entity identifier column."""
    if "entity_id" in features.columns:
        return "entity_id"

    if "cse_id" in features.columns:
        return "cse_id"

    raise ValueError(
        "features must contain either 'entity_id' or 'cse_id'"
    )


def _resolve_feature_columns(
    features: pd.DataFrame,
    feature_columns: list[str] | None,
    id_column: str,
) -> list[str]:
    """Resolve and validate numeric feature columns."""

    if feature_columns is None:
        columns = features.select_dtypes(
            include=[np.number]
        ).columns.tolist()
    else:
        columns = list(feature_columns)

    resolved: list[str] = []

    for column in columns:
        if column == id_column:
            continue

        if column not in features.columns:
            continue

        numeric_values = pd.to_numeric(
            features[column],
            errors="coerce",
        )

        if numeric_values.notna().any():
            resolved.append(column)

    return resolved


def _calculate_modified_z(
    values: pd.Series,
    median: float,
    mad: float,
) -> pd.Series:
    """
    Calculate robust modified Z-scores.

    If MAD is zero, fall back to population standard deviation.
    """
    if mad > 0:
        return (
            0.6745
            * (values - median)
            / mad
        )

    std = float(values.std(ddof=0))

    if std > 0:
        return (values - median) / std

    # All valid values are effectively identical.
    return pd.Series(
        0.0,
        index=values.index,
    )


def _build_method(
    iqr_flag: bool,
    z_flag: bool,
) -> str:
    """Describe which statistical method detected the anomaly."""
    methods = []

    if iqr_flag:
        methods.append("IQR")

    if z_flag:
        methods.append("MAD_Z")

    return "+".join(methods)


def detect_statistical_anomalies(
    features: pd.DataFrame,
    feature_columns: list[str] | None = None,
    z_threshold: float = DEFAULT_Z_THRESHOLD,
    iqr_multiplier: float = DEFAULT_IQR_MULTIPLIER,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
) -> pd.DataFrame:
    """
    Detect statistically unusual operational behaviour.

    For each numeric feature, the function compares entity values
    against the assessed peer distribution.

    An entity-feature observation is flagged when:

        IQR fence violation
                OR
        modified Z-score >= z_threshold

    Statistical findings are only generated when the peer group
    contains at least min_group_size valid observations.

    Returns:
        One row per entity-feature statistical anomaly.
    """

    if not isinstance(features, pd.DataFrame):
        raise TypeError(
            "features must be a pandas DataFrame"
        )

    if z_threshold <= 0:
        raise ValueError(
            "z_threshold must be greater than 0"
        )

    if iqr_multiplier <= 0:
        raise ValueError(
            "iqr_multiplier must be greater than 0"
        )

    if min_group_size < MIN_STATISTICAL_GROUP_SIZE:
        raise ValueError(
            "min_group_size must be at least 3"
        )

    if features.empty:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    id_column = _resolve_entity_column(
        features
    )

    resolved_features = _resolve_feature_columns(
        features,
        feature_columns,
        id_column,
    )

    if not resolved_features:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    findings: list[dict[str, Any]] = []

    for feature in resolved_features:

        values = pd.to_numeric(
            features[feature],
            errors="coerce",
        )

        valid = values.dropna()

        # Not enough observations for a meaningful
        # statistical comparison.
        if len(valid) < MIN_STATISTICAL_GROUP_SIZE:
            continue

        # A constant population has no meaningful
        # statistical deviation.
        if valid.nunique() < 2:
            continue

        median = float(valid.median())

        q1 = float(
            valid.quantile(0.25)
        )

        q3 = float(
            valid.quantile(0.75)
        )

        iqr = q3 - q1

        lower_fence = (
            q1
            - iqr_multiplier * iqr
        )

        upper_fence = (
            q3
            + iqr_multiplier * iqr
        )

        mad = _mad(valid)

        modified_z = _calculate_modified_z(
            values,
            median,
            mad,
        )

        # Statistical thresholds can be configured by
        # the assessment methodology.
        enough_peers = (
            len(valid) >= min_group_size
        )

        if not enough_peers:
            continue

        for index, value in values.items():

            if pd.isna(value):
                continue

            numeric_value = float(value)

            z_score = float(
                modified_z.loc[index]
            )

            iqr_flag = (
                numeric_value < lower_fence
                or numeric_value > upper_fence
            )

            z_flag = (
                abs(z_score)
                >= z_threshold
            )

            if not (iqr_flag or z_flag):
                continue

            direction = (
                "low"
                if numeric_value < median
                else "high"
            )

            method = _build_method(
                iqr_flag,
                z_flag,
            )

            entity_id = str(
                features.loc[
                    index,
                    id_column,
                ]
            )

            findings.append(
                {
                    "entity_id": entity_id,
                    "feature": feature,
                    "value": numeric_value,
                    "median": median,
                    "modified_z": z_score,
                    "lower_fence": float(
                        lower_fence
                    ),
                    "upper_fence": float(
                        upper_fence
                    ),
                    "direction": direction,
                    "method": method,
                    "peer_count": int(
                        len(valid)
                    ),
                }
            )

    return pd.DataFrame(
        findings,
        columns=OUTPUT_COLUMNS,
    )


# Compatibility alias used by existing CyberLens code.
find_statistical_anomalies = (
    detect_statistical_anomalies
)