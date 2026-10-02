"""Fuse statistical and Isolation Forest outputs into explainable CyberLens signals."""
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, timezone

MODEL_VERSION = "cyberlens-phase4-0.1.0"


def build_anomaly_signals(
    features: pd.DataFrame,
    statistical_findings: pd.DataFrame,
    isolation_results: pd.DataFrame,
    assessment_id: str = "assessment-unknown",
    version: str = MODEL_VERSION,
) -> list[dict]:
    """Create PRD-compatible signal dictionaries, one per entity with any anomaly.

    Scores are review-support indicators, not probabilities or attack classifications.
    Priority thresholds are transparent defaults and should be calibrated with experts.
    """
    if features.empty:
        return []
    id_col = "entity_id" if "entity_id" in features else "cse_id"
    stat = statistical_findings.copy() if statistical_findings is not None else pd.DataFrame()
    iso = isolation_results.copy() if isolation_results is not None else pd.DataFrame()
    stat_by_entity = {}
    if not stat.empty and "entity_id" in stat:
        stat_by_entity = {k: g for k, g in stat.groupby("entity_id")}
    iso_by_entity = {}
    if not iso.empty and "entity_id" in iso:
        iso_by_entity = {r.entity_id: r for r in iso.itertuples(index=False)}

    signals = []
    for row in features.to_dict(orient="records"):
        entity = row[id_col]
        stat_rows = stat_by_entity.get(entity, pd.DataFrame())
        ml_row = iso_by_entity.get(entity)
        stat_count = len(stat_rows)
        ml_flag = bool(getattr(ml_row, "if_anomaly", False)) if ml_row is not None else False
        if stat_count == 0 and not ml_flag:
            continue

        # Normalize the count contribution and combine with ML score rank-free flag.
        stat_component = min(stat_count / 3.0, 1.0)
        ml_component = 1.0 if ml_flag else 0.0
        score = round(100.0 * (0.65 * stat_component + 0.35 * ml_component), 2)
        priority = "HIGH" if score >= 75 else "MEDIUM" if score >= 40 else "LOW"
        evidence = []
        reasons = []
        for item in stat_rows.to_dict(orient="records") if stat_count else []:
            evidence.append({
                "feature": item["feature"], "observed_value": item["value"],
                "peer_median": item["median"], "modified_z": item["modified_z"],
                "lower_fence": item["lower_fence"], "upper_fence": item["upper_fence"],
                "direction": item["direction"], "method": item["method"],
            })
            reasons.append(f"{item['feature']} is unusually {item['direction']} versus the assessed peer group")
        if ml_flag:
            evidence.append({"method": "IsolationForest", "anomaly_score": float(ml_row.if_anomaly_score), "prediction": int(ml_row.if_prediction)})
            reasons.append("Isolation Forest identified an unusual combination of operational features")
        reason = "; ".join(dict.fromkeys(reasons)) or "Unusual operational behaviour detected"
        source_ids = []
        for col in ("source_record_ids", "record_ids"):
            value = row.get(col)
            if isinstance(value, (list, tuple, set)):
                source_ids.extend(str(v) for v in value)
        signals.append({
            "signal_id": f"ANOM-{assessment_id}-{entity}",
            "signal_type": "OPERATIONAL_ANOMALY",
            "rule_id": "ML-STAT-001",
            "category": "ANOMALY_BEHAVIOUR",
            "priority": priority,
            "anomaly_score": score,
            "reason": reason,
            "evidence": evidence,
            "source_record_ids": sorted(set(source_ids)),
            "historical_context": {},
            "peer_context": {"statistical_anomaly_count": stat_count},
            "evidence_confidence": "MEDIUM" if stat_count and ml_flag else "LOW" if ml_flag or stat_count else "INSUFFICIENT",
            "rule_model_version": version,
            "assessment_id": assessment_id,
            "entity_id": entity,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "human_review_required": True,
        })
    return signals


def score_anomalies(features: pd.DataFrame, statistical_findings: pd.DataFrame, isolation_results: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """DataFrame wrapper around build_anomaly_signals for convenient export."""
    return pd.DataFrame(build_anomaly_signals(features, statistical_findings, isolation_results, **kwargs))
