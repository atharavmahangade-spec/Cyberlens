"""Unsupervised Isolation Forest detection for CyberLens entity features."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def run_isolation_forest(
    features: pd.DataFrame,
    feature_columns: list[str] | None = None,
    contamination: float | str = "auto",
    random_state: int = 42,
    n_estimators: int = 200,
) -> pd.DataFrame:
    """Fit Isolation Forest and return predictions/scores per entity.

    prediction=-1 means anomalous, +1 means inlier. anomaly_score is oriented so
    larger values indicate more unusual observations (negative sklearn score_samples).
    Scaling is included for a consistent preprocessing pipeline; Isolation Forest
    itself is tree-based and generally does not require scaling.
    """
    id_col = "entity_id" if "entity_id" in features else ("cse_id" if "cse_id" in features else None)
    if id_col is None:
        raise ValueError("features must contain entity_id or cse_id")
    if feature_columns is None:
        feature_columns = list(features.select_dtypes(include=[np.number]).columns)
    feature_columns = [c for c in feature_columns if c in features.columns]
    if not feature_columns:
        raise ValueError("No numeric feature columns available for Isolation Forest")
    output = features[[id_col]].copy().rename(columns={id_col: "entity_id"})
    if len(features) < 3:
        output["if_prediction"] = 1
        output["if_anomaly_score"] = 0.0
        output["if_anomaly"] = False
        output["if_model_status"] = "insufficient_entities"
        return output

    x = features[feature_columns].apply(pd.to_numeric, errors="coerce")
    # Drop columns with no usable values or no variation; they cannot help split rows.
    usable = [c for c in x.columns if x[c].notna().any() and x[c].nunique(dropna=True) > 1]
    if not usable:
        output["if_prediction"] = 1
        output["if_anomaly_score"] = 0.0
        output["if_anomaly"] = False
        output["if_model_status"] = "no_variable_features"
        return output
    x = x[usable]
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", IsolationForest(
            n_estimators=n_estimators, contamination=contamination,
            random_state=random_state, n_jobs=-1,
        )),
    ])
    model.fit(x)
    predictions = model.predict(x)
    scores = -model.named_steps["model"].score_samples(model.named_steps["scaler"].transform(model.named_steps["imputer"].transform(x)))
    output["if_prediction"] = predictions.astype(int)
    output["if_anomaly_score"] = scores.astype(float)
    output["if_anomaly"] = output.if_prediction.eq(-1)
    output["if_model_status"] = "fitted"
    return output


# Compatibility alias.
detect_with_isolation_forest = run_isolation_forest
