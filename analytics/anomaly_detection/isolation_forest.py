"""
CyberLens - Isolation Forest Anomaly Detection
===============================================

Phase 4: Anomaly & Behaviour Analytics

Uses scikit-learn Isolation Forest to identify unusual combinations
of operational features across assessed entities.

Important:
- This identifies unusual operational behaviour.
- It does NOT classify cyber attacks.
- It does NOT produce a probability of compromise.
- Results are intended for supervisory review.
- Processing is fully offline.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


DEFAULT_CONTAMINATION = "auto"
DEFAULT_N_ESTIMATORS = 200
DEFAULT_RANDOM_STATE = 42


OUTPUT_COLUMNS = [
    "entity_id",
    "if_prediction",
    "if_anomaly",
    "if_anomaly_score",
]


def _resolve_entity_column(features: pd.DataFrame) -> str:
    """Resolve the supported entity identifier."""
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
    entity_column: str,
) -> list[str]:
    """Resolve numeric features used by Isolation Forest."""

    if feature_columns is None:
        columns = features.select_dtypes(
            include=[np.number]
        ).columns.tolist()
    else:
        columns = list(feature_columns)

    resolved = []

    for column in columns:
        if column == entity_column:
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


def detect_isolation_forest_anomalies(
    features: pd.DataFrame,
    feature_columns: list[str] | None = None,
    contamination: float | str = DEFAULT_CONTAMINATION,
    n_estimators: int = DEFAULT_N_ESTIMATORS,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> pd.DataFrame:
    """
    Detect unusual combinations of operational features.

    Isolation Forest produces:
        if_prediction:
            -1 = anomaly
             1 = normal

        if_anomaly:
            True  = anomaly
            False = normal

        if_anomaly_score:
            Higher values indicate more anomalous observations
            relative to the fitted population.

    The score is an analytical indicator and is NOT a probability
    or attack-risk score.
    """

    if not isinstance(features, pd.DataFrame):
        raise TypeError(
            "features must be a pandas DataFrame"
        )

    if features.empty:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    if n_estimators <= 0:
        raise ValueError(
            "n_estimators must be greater than 0"
        )

    entity_column = _resolve_entity_column(
        features
    )

    resolved_features = _resolve_feature_columns(
        features,
        feature_columns,
        entity_column,
    )

    if not resolved_features:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    # Build numeric feature matrix.
    matrix = features[
        resolved_features
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    # Median imputation keeps the detector deterministic and
    # avoids dropping entities because of isolated missing values.
    matrix = matrix.fillna(
        matrix.median()
    )

    # If an entire feature is missing, median remains NaN.
    # Replace those values with zero so sklearn receives
    # a valid matrix.
    matrix = matrix.fillna(0.0)

    # Isolation Forest requires more than one usable observation
    # for meaningful population-level comparison.
    if len(matrix) < 3:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(matrix)

    predictions = model.predict(matrix)

    # sklearn's decision_function:
    # larger = more normal.
    # Negate it so larger values represent more anomalous
    # behaviour for CyberLens explainability.
    anomaly_scores = -model.decision_function(
        matrix
    )

    results = pd.DataFrame(
        {
            "entity_id": features[
                entity_column
            ].astype(str),
            "if_prediction": predictions.astype(int),
            "if_anomaly": predictions == -1,
            "if_anomaly_score": anomaly_scores.astype(
                float
            ),
        }
    )

    return results.reset_index(drop=True)


# Compatibility aliases.
detect_anomalies = detect_isolation_forest_anomalies
run_isolation_forest = detect_isolation_forest_anomalies