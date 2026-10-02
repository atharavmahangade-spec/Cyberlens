Input: normalized pandas DataFrames from the upstream ingestion/normalization phase.
Each input should contain entity_id (or cse_id). Timestamps should be parseable by pandas.
Output: one numerical feature row per entity for the supplied assessment window.

This module deliberately aggregates operational behaviour; it does not infer attacks.
"""
from __future__ import annotations

from typing import Optional
import numpy as np
import pandas as pd

ENTITY_KEYS = ("entity_id", "cse_id", "cse", "organization_id")


def _empty() -> pd.DataFrame:
    return pd.DataFrame()


def _entity_col(df: pd.DataFrame) -> Optional[str]:
    return next((c for c in ENTITY_KEYS if c in df.columns), None)


def _num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _duration_hours(df: pd.DataFrame, start: str, end: str) -> pd.Series:
    if start not in df.columns or end not in df.columns:
        return pd.Series(np.nan, index=df.index, dtype=float)
    a = pd.to_datetime(df[start], errors="coerce", utc=True)
    b = pd.to_datetime(df[end], errors="coerce", utc=True)
    result = (b - a).dt.total_seconds() / 3600.0
    return result.where(result >= 0)


def _safe_rate(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.replace(0, np.nan)).fillna(0.0)


def _group_count(df: pd.DataFrame, name: str) -> pd.Series:
    col = _entity_col(df)
    if col is None or df.empty:
        return pd.Series(dtype=float, name=name)
    return df.groupby(col).size().astype(float).rename(name)


def _status_count(df: pd.DataFrame, name: str, accepted: tuple[str, ...]) -> pd.Series:
    col = _entity_col(df)
    if col is None or df.empty or "status" not in df.columns:
        return pd.Series(dtype=float, name=name)
    mask = df["status"].astype(str).str.strip().str.lower().isin(accepted)
    return df.loc[mask].groupby(col).size().astype(float).rename(name)


def build_entity_features(
    alerts: Optional[pd.DataFrame] = None,
    cases: Optional[pd.DataFrame] = None,
    investigations: Optional[pd.DataFrame] = None,
    escalations: Optional[pd.DataFrame] = None,
    assets: Optional[pd.DataFrame] = None,
    monitoring: Optional[pd.DataFrame] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> pd.DataFrame:
    """Build entity-level features from normalized SOC/CSE tables.

    Expected useful columns (all optional except an entity key):
      alerts: alert_id, severity, status, acknowledged_at, closed_at, created_at
      cases: case_id, status, created_at, closed_at
      investigations: status, started_at, completed_at
      escalations: status, escalated_at
      assets: asset_id, criticality, monitoring_status
      monitoring: coverage (0..1 or 0..100), telemetry_available, evidence_timestamp

    If period bounds are provided, records with a recognizable event timestamp are
    filtered inclusively. Tables without a suitable timestamp are left untouched.
    """
    tables = {
        "alerts": alerts.copy() if alerts is not None else _empty(),
        "cases": cases.copy() if cases is not None else _empty(),
        "investigations": investigations.copy() if investigations is not None else _empty(),
        "escalations": escalations.copy() if escalations is not None else _empty(),
        "assets": assets.copy() if assets is not None else _empty(),
        "monitoring": monitoring.copy() if monitoring is not None else _empty(),
    }
    time_candidates = {
        "alerts": ("created_at", "alert_timestamp", "timestamp"),
        "cases": ("created_at", "case_created_at"),
        "investigations": ("started_at", "investigation_start"),
        "escalations": ("escalated_at", "escalation_timestamp"),
        "assets": (),
        "monitoring": ("evidence_timestamp", "timestamp"),
    }
    for name, df in tables.items():
        if df.empty:
            continue
        key = _entity_col(df)
        if key is None:
            raise ValueError(f"{name} must contain one of {ENTITY_KEYS}")
        if period_start or period_end:
            ts = next((c for c in time_candidates[name] if c in df.columns), None)
            if ts:
                parsed = pd.to_datetime(df[ts], errors="coerce", utc=True)
                keep = pd.Series(True, index=df.index)
                if period_start:
                    keep &= parsed >= pd.Timestamp(period_start, tz="UTC") if pd.Timestamp(period_start).tzinfo is None else parsed >= pd.Timestamp(period_start)
                if period_end:
                    keep &= parsed <= pd.Timestamp(period_end, tz="UTC") if pd.Timestamp(period_end).tzinfo is None else parsed <= pd.Timestamp(period_end)
                tables[name] = df.loc[keep].copy()

    alerts, cases = tables["alerts"], tables["cases"]
    investigations, escalations = tables["investigations"], tables["escalations"]
    assets, monitoring = tables["assets"], tables["monitoring"]

    indexes = []
    for df in tables.values():
        col = _entity_col(df)
        if col and not df.empty:
            indexes.extend(df[col].dropna().unique().tolist())
    if not indexes:
        return pd.DataFrame(columns=["entity_id"])
    result = pd.DataFrame(index=pd.Index(sorted(set(indexes), key=str), name="entity_id"))

    sources = {
        "alert_count": alerts,
        "case_count": cases,
        "investigation_count": investigations,
        "escalation_count": escalations,
        "asset_count": assets,
    }
    for feature, df in sources.items():
        s = _group_count(df, feature)
        result = result.join(s.rename_axis("entity_id"), how="left")

    # Alert status, severity and lifecycle timings.
    if not alerts.empty:
        ac = _entity_col(alerts)
        if "status" in alerts:
            closed = alerts[alerts.status.astype(str).str.lower().isin(["closed", "resolved", "complete", "completed"])]
            result = result.join(closed.groupby(ac).size().rename("closed_alert_count"), how="left")
        if "severity" in alerts:
            sev = alerts["severity"].astype(str).str.lower()
            high = sev.isin(["critical", "high", "1", "p1", "p2"])
            result = result.join(alerts.loc[high].groupby(ac).size().rename("high_severity_alert_count"), how="left")
        if "acknowledged_at" in alerts and "created_at" in alerts:
            temp = alerts.assign(_ack_hours=_duration_hours(alerts, "created_at", "acknowledged_at"))
            result = result.join(temp.groupby(ac)._ack_hours.median().rename("median_acknowledgement_hours"), how="left")
        if "closed_at" in alerts and "created_at" in alerts:
            temp = alerts.assign(_close_hours=_duration_hours(alerts, "created_at", "closed_at"))
            result = result.join(temp.groupby(ac)._close_hours.median().rename("median_alert_closure_hours"), how="left")

    # Case closure rate and case duration.
    if not cases.empty:
        cc = _entity_col(cases)
        if "status" in cases:
            closed = cases.status.astype(str).str.lower().isin(["closed", "resolved", "complete", "completed"])
            result = result.join(cases.assign(_closed=closed).groupby(cc)._closed.sum().rename("closed_case_count"), how="left")
        if "created_at" in cases and "closed_at" in cases:
            temp = cases.assign(_duration=_duration_hours(cases, "created_at", "closed_at"))
            result = result.join(temp.groupby(cc)._duration.median().rename("median_case_closure_hours"), how="left")

    # Investigation completion and duration.
    if not investigations.empty:
        ic = _entity_col(investigations)
        if "status" in investigations:
            done = investigations.status.astype(str).str.lower().isin(["completed", "complete", "closed"])
            result = result.join(investigations.assign(_done=done).groupby(ic)._done.sum().rename("completed_investigation_count"), how="left")
        if "started_at" in investigations and "completed_at" in investigations:
            temp = investigations.assign(_duration=_duration_hours(investigations, "started_at", "completed_at"))
            result = result.join(temp.groupby(ic)._duration.median().rename("median_investigation_hours"), how="left")

    # Escalation rate and asset/monitoring coverage.
    if not assets.empty and "criticality" in assets:
        critical = assets.criticality.astype(str).str.lower().isin(["critical", "high", "1", "p1"])
        result = result.join(assets.assign(_critical=critical).groupby(_entity_col(assets))._critical.sum().rename("critical_asset_count"), how="left")
    if not assets.empty and "monitoring_status" in assets:
        monitored = assets.monitoring_status.astype(str).str.lower().isin(["active", "monitored", "enabled", "healthy"])
        result = result.join(assets.assign(_monitored=monitored).groupby(_entity_col(assets))._monitored.sum().rename("monitored_asset_count"), how="left")
    if not monitoring.empty:
        mc = _entity_col(monitoring)
        if "coverage" in monitoring:
            coverage = _num(monitoring.coverage)
            # Accept either fractional or percentage input; normalize to 0..1.
            coverage = coverage.where(coverage <= 1, coverage / 100.0).clip(0, 1)
            result = result.join(monitoring.assign(_coverage=coverage).groupby(mc)._coverage.mean().rename("monitoring_coverage"), how="left")
        if "telemetry_available" in monitoring:
            telemetry = monitoring.telemetry_available.astype(str).str.lower().isin(["true", "1", "yes", "available"])
            result = result.join(monitoring.assign(_telemetry=telemetry).groupby(mc)._telemetry.mean().rename("telemetry_availability_rate"), how="left")

    # Derived rates. Missing denominators produce 0, never division errors.
    for col in ["alert_count", "case_count", "investigation_count", "escalation_count", "asset_count",
                "closed_alert_count", "closed_case_count", "completed_investigation_count",
                "high_severity_alert_count", "critical_asset_count", "monitored_asset_count"]:
        if col not in result:
            result[col] = 0.0
    result["alert_closure_rate"] = _safe_rate(result.closed_alert_count, result.alert_count)
    result["case_closure_rate"] = _safe_rate(result.closed_case_count, result.case_count)
    result["investigation_completion_rate"] = _safe_rate(result.completed_investigation_count, result.investigation_count)
    result["escalation_rate"] = _safe_rate(result.escalation_count, result.alert_count)
    result["high_severity_alert_rate"] = _safe_rate(result.high_severity_alert_count, result.alert_count)
    result["critical_asset_rate"] = _safe_rate(result.critical_asset_count, result.asset_count)
    result["asset_monitoring_rate"] = _safe_rate(result.monitored_asset_count, result.asset_count)

    result = result.replace([np.inf, -np.inf], np.nan)
    numeric = result.select_dtypes(include=[np.number]).columns
    result[numeric] = result[numeric].fillna(0.0)
    result = result.reset_index().rename(columns={"index": "entity_id"})
    return result


# Friendly alias for callers that prefer a shorter name.
extract_features = build_entity_features
