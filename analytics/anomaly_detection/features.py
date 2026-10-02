"""
CyberLens - Phase 4
Feature Engineering / Feature Extraction
=========================================

Purpose:
    Convert normalized SOC/CSE operational records into entity-level
    numerical features suitable for statistical anomaly detection
    and Isolation Forest.

Important:
    These features describe operational behaviour.
    They do NOT determine whether an entity has committed a violation
    or whether a cyberattack has occurred.

Design principles:
    - Fully offline
    - Deterministic
    - Explainable
    - Compatible with statistical anomaly detection
    - Compatible with Isolation Forest
    - Missing source evidence is not automatically treated as a
      confirmed operational zero when the source population is unknown
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Supported entity identifiers
# ---------------------------------------------------------------------

ENTITY_KEYS = (
    "entity_id",
    "cse_id",
    "cse",
    "organization_id",
)


# ---------------------------------------------------------------------
# Final features passed to the anomaly / ML layer
# ---------------------------------------------------------------------

FEATURE_COLUMNS = [
    # Volume
    "alert_count",
    "case_count",
    "investigation_count",
    "escalation_count",

    # Alert behaviour
    "alert_closure_rate",
    "open_alert_rate",
    "high_severity_alert_rate",
    "median_acknowledgement_hours",
    "mean_acknowledgement_hours",
    "median_alert_closure_hours",
    "mean_alert_closure_hours",
    "alert_closure_time_std",

    # Investigation behaviour
    "investigation_completion_rate",
    "median_investigation_hours",
    "mean_investigation_hours",
    "investigation_time_std",

    # Case behaviour
    "case_closure_rate",
    "median_case_closure_hours",
    "mean_case_closure_hours",

    # Escalation behaviour
    "escalation_rate",
    "non_escalation_rate",
    "escalation_per_investigation",

    # Relationship / workload metrics
    "investigations_per_alert",
    "investigations_per_case",
    "cases_per_alert",

    # Assets
    "asset_count",
    "critical_asset_count",
    "critical_asset_rate",
    "monitored_asset_count",
    "asset_monitoring_rate",
    "critical_asset_monitoring_rate",

    # Monitoring / telemetry
    "monitoring_coverage",
    "telemetry_availability_rate",

    # Data quality
    "feature_data_completeness",
]


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------


def _empty() -> pd.DataFrame:
    """Return an empty DataFrame."""
    return pd.DataFrame()


def _entity_col(df: pd.DataFrame) -> Optional[str]:
    """Find the entity identifier used by a normalized input table."""

    for column in ENTITY_KEYS:
        if column in df.columns:
            return column

    return None


def _numeric(series: pd.Series) -> pd.Series:
    """Safely convert a Series to numeric."""

    return pd.to_numeric(
        series,
        errors="coerce",
    )


def _safe_rate(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """
    Safe division.

    Zero or unavailable denominators return 0.0.

    Note:
        The resulting value is an operational feature, not a statement
        that the underlying evidence was explicitly observed as zero.
    """

    numerator = _numeric(numerator)
    denominator = _numeric(denominator)

    denominator = denominator.replace(
        0,
        np.nan,
    )

    return (
        numerator
        .div(denominator)
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0.0)
    )


def _duration_hours(
    df: pd.DataFrame,
    start_column: str,
    end_column: str,
) -> pd.Series:
    """
    Calculate duration between two timestamps in hours.

    Invalid timestamps and negative durations become NaN.
    """

    if (
        start_column not in df.columns
        or end_column not in df.columns
    ):
        return pd.Series(
            np.nan,
            index=df.index,
            dtype=float,
        )

    start = pd.to_datetime(
        df[start_column],
        errors="coerce",
        utc=True,
    )

    end = pd.to_datetime(
        df[end_column],
        errors="coerce",
        utc=True,
    )

    duration = (
        end - start
    ).dt.total_seconds() / 3600.0

    return duration.where(
        duration >= 0
    )


def _group_count(
    df: pd.DataFrame,
    feature_name: str,
) -> pd.Series:
    """Count records for every entity."""

    entity = _entity_col(df)

    if entity is None or df.empty:
        return pd.Series(
            dtype=float,
            name=feature_name,
        )

    return (
        df.groupby(entity)
        .size()
        .astype(float)
        .rename(feature_name)
    )


def _status_mask(
    df: pd.DataFrame,
    statuses: tuple[str, ...],
) -> pd.Series:
    """Create a case-insensitive status mask."""

    if "status" not in df.columns:
        return pd.Series(
            False,
            index=df.index,
        )

    return (
        df["status"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(statuses)
    )


def _normalise_coverage(
    series: pd.Series,
) -> pd.Series:
    """
    Normalize monitoring coverage to 0..1.

    Accepts:
        0.95
    or:
        95
    """

    values = _numeric(series)

    values = values.where(
        values <= 1,
        values / 100.0,
    )

    return values.clip(
        0,
        1,
    )


def _join(
    result: pd.DataFrame,
    series: pd.Series,
) -> pd.DataFrame:
    """Join an entity-indexed Series safely."""

    if series.empty:
        return result

    series = series.copy()
    series.index.name = "entity_id"

    return result.join(
        series,
        how="left",
    )


def _normalise_entity_values(
    series: pd.Series,
) -> pd.Series:
    """
    Normalize entity identifiers to strings.

    Empty identifiers become 'unknown-entity'.
    """

    values = (
        series.astype(str)
        .str.strip()
    )

    return values.replace(
        {
            "": "unknown-entity",
            "nan": "unknown-entity",
            "None": "unknown-entity",
        }
    )


# ---------------------------------------------------------------------
# Main feature extraction function
# ---------------------------------------------------------------------


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
    """
    Build entity-level CyberLens operational features.

    Parameters
    ----------
    alerts:
        Alert-level records.

    cases:
        Case-level records.

    investigations:
        Investigation-level records.

    escalations:
        Escalation-level records.

    assets:
        Asset inventory / monitoring records.

    monitoring:
        Monitoring and telemetry records.

    period_start / period_end:
        Optional assessment-window boundaries.

    Returns
    -------
    pandas.DataFrame
        One row per entity with numerical operational features.
    """

    # -------------------------------------------------------------
    # Copy inputs so the caller's data is never modified.
    # -------------------------------------------------------------

    tables = {
        "alerts": (
            alerts.copy()
            if alerts is not None
            else _empty()
        ),
        "cases": (
            cases.copy()
            if cases is not None
            else _empty()
        ),
        "investigations": (
            investigations.copy()
            if investigations is not None
            else _empty()
        ),
        "escalations": (
            escalations.copy()
            if escalations is not None
            else _empty()
        ),
        "assets": (
            assets.copy()
            if assets is not None
            else _empty()
        ),
        "monitoring": (
            monitoring.copy()
            if monitoring is not None
            else _empty()
        ),
    }

    # -------------------------------------------------------------
    # Timestamp candidates for optional assessment filtering.
    # -------------------------------------------------------------

    time_candidates = {
        "alerts": (
            "created_at",
            "alert_timestamp",
            "timestamp",
        ),
        "cases": (
            "created_at",
            "case_created_at",
            "timestamp",
        ),
        "investigations": (
            "started_at",
            "investigation_start",
            "timestamp",
        ),
        "escalations": (
            "escalated_at",
            "escalation_timestamp",
            "timestamp",
        ),
        "assets": (),
        "monitoring": (
            "evidence_timestamp",
            "timestamp",
        ),
    }

    # -------------------------------------------------------------
    # Validate supplied tables.
    # -------------------------------------------------------------

    for table_name, df in tables.items():

        if df.empty:
            continue

        entity = _entity_col(df)

        if entity is None:
            raise ValueError(
                f"{table_name} must contain one of "
                f"{ENTITY_KEYS}"
            )

        # Normalize the entity identifier while preserving
        # the original input DataFrame through our copied table.
        df[entity] = _normalise_entity_values(
            df[entity]
        )

    # -------------------------------------------------------------
    # Apply assessment period if supplied.
    # -------------------------------------------------------------

    if period_start or period_end:

        for table_name, df in tables.items():

            if df.empty:
                continue

            timestamp_column = next(
                (
                    column
                    for column in time_candidates[
                        table_name
                    ]
                    if column in df.columns
                ),
                None,
            )

            # Do not fabricate timestamps.
            if timestamp_column is None:
                continue

            timestamps = pd.to_datetime(
                df[timestamp_column],
                errors="coerce",
                utc=True,
            )

            keep = pd.Series(
                True,
                index=df.index,
            )

            if period_start:
                start = pd.Timestamp(
                    period_start,
                    tz="UTC",
                )

                keep &= timestamps >= start

            if period_end:
                end = pd.Timestamp(
                    period_end,
                    tz="UTC",
                )

                keep &= timestamps <= end

            tables[table_name] = (
                df.loc[keep].copy()
            )

    # -------------------------------------------------------------
    # Recover tables.
    # -------------------------------------------------------------

    alerts = tables["alerts"]
    cases = tables["cases"]
    investigations = tables["investigations"]
    escalations = tables["escalations"]
    assets = tables["assets"]
    monitoring = tables["monitoring"]

    # -------------------------------------------------------------
    # Find every entity represented in supplied data.
    # -------------------------------------------------------------

    entity_values = []

    for df in tables.values():

        entity = _entity_col(df)

        if entity is None or df.empty:
            continue

        entity_values.extend(
            df[entity]
            .dropna()
            .unique()
            .tolist()
        )

    if not entity_values:
        return pd.DataFrame(
            columns=[
                "entity_id"
            ] + FEATURE_COLUMNS
        )

    entity_index = pd.Index(
        sorted(
            set(entity_values),
            key=str,
        ),
        name="entity_id",
    )

    result = pd.DataFrame(
        index=entity_index
    )

    # =============================================================
    # 1. VOLUME FEATURES
    # =============================================================

    for feature_name, table in [
        ("alert_count", alerts),
        ("case_count", cases),
        ("investigation_count", investigations),
        ("escalation_count", escalations),
        ("asset_count", assets),
    ]:
        result = _join(
            result,
            _group_count(
                table,
                feature_name,
            ),
        )

    # =============================================================
    # 2. ALERT FEATURES
    # =============================================================

    if not alerts.empty:

        entity = _entity_col(alerts)

        # ---------------------------------------------------------
        # Closed alerts
        # ---------------------------------------------------------

        closed_mask = _status_mask(
            alerts,
            (
                "closed",
                "resolved",
                "complete",
                "completed",
            ),
        )

        closed_counts = (
            alerts.loc[closed_mask]
            .groupby(entity)
            .size()
            .astype(float)
            .rename("closed_alert_count")
        )

        result = _join(
            result,
            closed_counts,
        )

        # ---------------------------------------------------------
        # Open alerts
        # ---------------------------------------------------------

        open_mask = _status_mask(
            alerts,
            (
                "open",
                "new",
                "pending",
                "in_progress",
                "investigating",
            ),
        )

        open_counts = (
            alerts.loc[open_mask]
            .groupby(entity)
            .size()
            .astype(float)
            .rename("open_alert_count")
        )

        result = _join(
            result,
            open_counts,
        )

        # ---------------------------------------------------------
        # High / critical severity
        # ---------------------------------------------------------

        if "severity" in alerts.columns:

            severity = (
                alerts["severity"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            high_mask = severity.isin(
                (
                    "high",
                    "critical",
                    "1",
                    "p1",
                    "p2",
                )
            )

            high_counts = (
                alerts.loc[high_mask]
                .groupby(entity)
                .size()
                .astype(float)
                .rename(
                    "high_severity_alert_count"
                )
            )

            result = _join(
                result,
                high_counts,
            )

        # ---------------------------------------------------------
        # Alert acknowledgement time
        # ---------------------------------------------------------

        if {
            "created_at",
            "acknowledged_at",
        }.issubset(alerts.columns):

            temp = alerts.copy()

            temp["_ack_hours"] = (
                _duration_hours(
                    temp,
                    "created_at",
                    "acknowledged_at",
                )
            )

            grouped = temp.groupby(
                entity
            )["_ack_hours"]

            result = _join(
                result,
                grouped.median().rename(
                    "median_acknowledgement_hours"
                ),
            )

            result = _join(
                result,
                grouped.mean().rename(
                    "mean_acknowledgement_hours"
                ),
            )

        # ---------------------------------------------------------
        # Alert closure time
        # ---------------------------------------------------------

        if {
            "created_at",
            "closed_at",
        }.issubset(alerts.columns):

            temp = alerts.copy()

            temp["_closure_hours"] = (
                _duration_hours(
                    temp,
                    "created_at",
                    "closed_at",
                )
            )

            grouped = temp.groupby(
                entity
            )["_closure_hours"]

            result = _join(
                result,
                grouped.median().rename(
                    "median_alert_closure_hours"
                ),
            )

            result = _join(
                result,
                grouped.mean().rename(
                    "mean_alert_closure_hours"
                ),
            )

            result = _join(
                result,
                grouped.std(
                    ddof=0
                ).rename(
                    "alert_closure_time_std"
                ),
            )

    # =============================================================
    # 3. CASE FEATURES
    # =============================================================

    if not cases.empty:

        entity = _entity_col(cases)

        closed_mask = _status_mask(
            cases,
            (
                "closed",
                "resolved",
                "complete",
                "completed",
            ),
        )

        closed_cases = (
            cases.loc[closed_mask]
            .groupby(entity)
            .size()
            .astype(float)
            .rename("closed_case_count")
        )

        result = _join(
            result,
            closed_cases,
        )

        if {
            "created_at",
            "closed_at",
        }.issubset(cases.columns):

            temp = cases.copy()

            temp["_case_duration"] = (
                _duration_hours(
                    temp,
                    "created_at",
                    "closed_at",
                )
            )

            grouped = temp.groupby(
                entity
            )["_case_duration"]

            result = _join(
                result,
                grouped.median().rename(
                    "median_case_closure_hours"
                ),
            )

            result = _join(
                result,
                grouped.mean().rename(
                    "mean_case_closure_hours"
                ),
            )

    # =============================================================
    # 4. INVESTIGATION FEATURES
    # =============================================================

    if not investigations.empty:

        entity = _entity_col(
            investigations
        )

        completed_mask = _status_mask(
            investigations,
            (
                "completed",
                "complete",
                "closed",
                "resolved",
            ),
        )

        completed = (
            investigations.loc[
                completed_mask
            ]
            .groupby(entity)
            .size()
            .astype(float)
            .rename(
                "completed_investigation_count"
            )
        )

        result = _join(
            result,
            completed,
        )

        if {
            "started_at",
            "completed_at",
        }.issubset(
            investigations.columns
        ):

            temp = investigations.copy()

            temp[
                "_investigation_duration"
            ] = _duration_hours(
                temp,
                "started_at",
                "completed_at",
            )

            grouped = temp.groupby(
                entity
            )["_investigation_duration"]

            result = _join(
                result,
                grouped.median().rename(
                    "median_investigation_hours"
                ),
            )

            result = _join(
                result,
                grouped.mean().rename(
                    "mean_investigation_hours"
                ),
            )

            result = _join(
                result,
                grouped.std(
                    ddof=0
                ).rename(
                    "investigation_time_std"
                ),
            )

    # =============================================================
    # 5. ASSET FEATURES
    # =============================================================

    if not assets.empty:

        entity = _entity_col(assets)

        # ---------------------------------------------------------
        # Critical assets
        # ---------------------------------------------------------

        if "criticality" in assets.columns:

            criticality = (
                assets["criticality"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            critical_mask = criticality.isin(
                (
                    "critical",
                    "high",
                    "1",
                    "p1",
                )
            )

            critical = (
                assets.loc[critical_mask]
                .groupby(entity)
                .size()
                .astype(float)
                .rename(
                    "critical_asset_count"
                )
            )

            result = _join(
                result,
                critical,
            )

        # ---------------------------------------------------------
        # Monitored assets
        # ---------------------------------------------------------

        if "monitoring_status" in assets.columns:

            monitoring_status = (
                assets["monitoring_status"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            monitored_mask = (
                monitoring_status.isin(
                    (
                        "active",
                        "monitored",
                        "enabled",
                        "healthy",
                    )
                )
            )

            monitored = (
                assets.loc[monitored_mask]
                .groupby(entity)
                .size()
                .astype(float)
                .rename(
                    "monitored_asset_count"
                )
            )

            result = _join(
                result,
                monitored,
            )

        # ---------------------------------------------------------
        # Critical assets that are monitored
        # ---------------------------------------------------------

        if {
            "criticality",
            "monitoring_status",
        }.issubset(
            assets.columns
        ):

            criticality = (
                assets["criticality"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            status = (
                assets["monitoring_status"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            critical_mask = criticality.isin(
                (
                    "critical",
                    "high",
                    "1",
                    "p1",
                )
            )

            monitored_mask = status.isin(
                (
                    "active",
                    "monitored",
                    "enabled",
                    "healthy",
                )
            )

            critical_monitored = (
                assets.loc[
                    critical_mask
                    & monitored_mask
                ]
                .groupby(entity)
                .size()
                .astype(float)
                .rename(
                    "critical_monitored_asset_count"
                )
            )

            result = _join(
                result,
                critical_monitored,
            )

    # =============================================================
    # 6. MONITORING / TELEMETRY FEATURES
    # =============================================================

    if not monitoring.empty:

        entity = _entity_col(
            monitoring
        )

        if "coverage" in monitoring.columns:

            coverage = _normalise_coverage(
                monitoring["coverage"]
            )

            result = _join(
                result,
                monitoring.assign(
                    _coverage=coverage
                )
                .groupby(entity)["_coverage"]
                .mean()
                .rename(
                    "monitoring_coverage"
                ),
            )

        if "telemetry_available" in monitoring.columns:

            telemetry = (
                monitoring[
                    "telemetry_available"
                ]
                .astype(str)
                .str.strip()
                .str.lower()
                .isin(
                    (
                        "true",
                        "1",
                        "yes",
                        "available",
                    )
                )
            )

            result = _join(
                result,
                monitoring.assign(
                    _telemetry=telemetry
                )
                .groupby(entity)["_telemetry"]
                .mean()
                .rename(
                    "telemetry_availability_rate"
                ),
            )

    # =============================================================
    # 7. FILL MISSING BASE COUNTS
    # =============================================================

    base_count_columns = [
        "alert_count",
        "case_count",
        "investigation_count",
        "escalation_count",
        "asset_count",
        "closed_alert_count",
        "open_alert_count",
        "high_severity_alert_count",
        "closed_case_count",
        "completed_investigation_count",
        "critical_asset_count",
        "monitored_asset_count",
        "critical_monitored_asset_count",
    ]

    for column in base_count_columns:

        if column not in result.columns:
            result[column] = 0.0

    # =============================================================
    # 8. DERIVED BEHAVIOURAL FEATURES
    # =============================================================

    result["alert_closure_rate"] = _safe_rate(
        result["closed_alert_count"],
        result["alert_count"],
    )

    result["open_alert_rate"] = _safe_rate(
        result["open_alert_count"],
        result["alert_count"],
    )

    result["high_severity_alert_rate"] = (
        _safe_rate(
            result[
                "high_severity_alert_count"
            ],
            result["alert_count"],
        )
    )

    result["case_closure_rate"] = _safe_rate(
        result["closed_case_count"],
        result["case_count"],
    )

    result["investigation_completion_rate"] = (
        _safe_rate(
            result[
                "completed_investigation_count"
            ],
            result["investigation_count"],
        )
    )

    result["escalation_rate"] = _safe_rate(
        result["escalation_count"],
        result["alert_count"],
    )

    # -------------------------------------------------------------
    # NEW: Non-escalation rate
    # -------------------------------------------------------------

    result["non_escalation_rate"] = (
        1.0
        - result["escalation_rate"]
    ).clip(0.0, 1.0)

    result["escalation_per_investigation"] = (
        _safe_rate(
            result["escalation_count"],
            result["investigation_count"],
        )
    )

    result["investigations_per_alert"] = (
        _safe_rate(
            result["investigation_count"],
            result["alert_count"],
        )
    )

    # -------------------------------------------------------------
    # NEW: Investigations per case
    # -------------------------------------------------------------

    result["investigations_per_case"] = (
        _safe_rate(
            result["investigation_count"],
            result["case_count"],
        )
    )

    result["cases_per_alert"] = _safe_rate(
        result["case_count"],
        result["alert_count"],
    )

    result["critical_asset_rate"] = _safe_rate(
        result["critical_asset_count"],
        result["asset_count"],
    )

    result["asset_monitoring_rate"] = (
        _safe_rate(
            result["monitored_asset_count"],
            result["asset_count"],
        )
    )

    result[
        "critical_asset_monitoring_rate"
    ] = _safe_rate(
        result[
            "critical_monitored_asset_count"
        ],
        result[
            "critical_asset_count"
        ],
    )

    # =============================================================
    # 9. DATA COMPLETENESS
    # =============================================================

    # Calculate completeness before ML-oriented missing-value
    # imputation. This prevents imputation from hiding missing evidence.
    completeness_values = []

    for column in FEATURE_COLUMNS:

        if column in result.columns:
            completeness_values.append(
                result[column].notna().astype(int)
            )
        else:
            completeness_values.append(
                pd.Series(
                    0,
                    index=result.index,
                    dtype=int,
                )
            )

    if completeness_values:

        completeness_frame = pd.concat(
            completeness_values,
            axis=1,
        )

        result[
            "feature_data_completeness"
        ] = completeness_frame.mean(
            axis=1
        )

    else:
        result[
            "feature_data_completeness"
        ] = 0.0

    # =============================================================
    # 10. CLEAN NUMERICAL VALUES
    # =============================================================

    numeric_columns = result.select_dtypes(
        include=[np.number]
    ).columns

    result[numeric_columns] = (
        result[numeric_columns]
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
    )

    # ML algorithms need finite numerical values.
    # At this stage missing numerical values are converted to 0
    # only for the final ML-ready representation.
    result[numeric_columns] = (
        result[numeric_columns]
        .fillna(0.0)
    )

    # =============================================================
    # 11. ENSURE FINAL FEATURE SET
    # =============================================================

    for column in FEATURE_COLUMNS:

        if column not in result.columns:
            result[column] = 0.0

    # Stable output order.
    result = result.reset_index()

    result = result[
        ["entity_id"] + FEATURE_COLUMNS
    ]

    return result


# ---------------------------------------------------------------------
# Compatibility alias
# ---------------------------------------------------------------------

extract_features = build_entity_features