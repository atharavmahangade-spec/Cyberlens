"""Robust statistical anomaly detection for CyberLens features."""
from __future__ import annotations
import numpy as np
import pandas as pd

DEFAULT_FEATURES = None


def _mad(values: pd.Series) -> float:
    median = values.median()
    return float((values - median).abs().median())


def detect_statistical_anomalies(
    features: pd.DataFrame,
    feature_columns: list[str] | None = None,
    z_threshold: float = 3.0,
    iqr_multiplier: float = 1.5,
    min_group_size: int = 5,
) -> pd.DataFrame:
    """Flag feature values outside robust peer distribution.

    Computes median/MAD modified Z-score and IQR fences per feature across entities.
    For fewer than min_group_size valid entities, it uses the available population
    but still requires at least 3 values; smaller groups are not statistically flagged.
    Returns one row per entity-feature anomaly, including direction and evidence.
    """
    if features.empty:
        return pd.DataFrame(columns=["entity_id", "feature", "value", "median", "modified_z", "lower_fence", "upper_fence", "direction", "method"])
    id_col = "entity_id" if "entity_id" in features else ("cse_id" if "cse_id" in features else None)
    if id_col is None:
        raise ValueError("features must contain entity_id or cse_id")
    if feature_columns is None:
        feature_columns = [c for c in features.select_dtypes(include=[np.number]).columns]
    findings = []
    for feature in feature_columns:
        if feature not in features:
            continue
        values = pd.to_numeric(features[feature], errors="coerce")
        valid = values.dropna()
        if len(valid) < 3 or valid.nunique() < 2:
            continue
        median = float(valid.median())
        q1, q3 = valid.quantile([0.25, 0.75])
        iqr = float(q3 - q1)
        lower, upper = float(q1 - iqr_multiplier * iqr), float(q3 + iqr_multiplier * iqr)
        mad = _mad(valid)
        # 0.6745 makes MAD-based score comparable to standard Z under normality.
        if mad > 0:
            modified_z = 0.6745 * (values - median) / mad
        else:
            std = float(valid.std(ddof=0))
            modified_z = (values - median) / std if std > 0 else values * 0
        enough = len(valid) >= min_group_size
        for idx, value in values.items():
            if pd.isna(value):
                continue
            z = float(modified_z.loc[idx])
            iqr_flag = value < lower or value > upper
            z_flag = abs(z) >= z_threshold
            if enough and (iqr_flag or z_flag):
                direction = "low" if value < median else "high"
                methods = "+".join(m for m, flag in [("IQR", iqr_flag), ("MAD_Z", z_flag)] if flag)
                findings.append({
                    "entity_id": features.loc[idx, id_col], "feature": feature,
                    "value": float(value), "median": median, "modified_z": z,
                    "lower_fence": lower, "upper_fence": upper,
                    "direction": direction, "method": methods,
                    "peer_count": int(len(valid)),
                })
    return pd.DataFrame(findings, columns=["entity_id", "feature", "value", "median", "modified_z", "lower_fence", "upper_fence", "direction", "method", "peer_count"])


# Compatibility alias.
find_statistical_anomalies = detect_statistical_anomalies
