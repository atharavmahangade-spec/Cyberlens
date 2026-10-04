"""
CyberLens - Real Dataset Adapter

Converts the real CyberLens assessment dataset into the canonical
feature structures expected by the existing supervisory analytics.

The incoming CSV files are treated as immutable source data.
No analytics module is rewritten here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_DATA_DIR = Path("data/incoming")


def load_real_dataset(
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> dict[str, pd.DataFrame]:
    """Load the real CyberLens assessment datasets."""

    data_dir = Path(data_dir)

    filenames = {
        "alerts": "alerts.csv",
        "cases": "cases.csv",
        "investigations": "investigations.csv",
        "escalations": "escalations.csv",
        "assets": "assets.csv",
        "monitoring": "monitoring_evidence.csv",
        "historical": "historical_assessments.csv",
        "capabilities": "capabilities.csv",
        "evidence_records": "evidence_records.csv",
        "expected_evidence": "expected_evidence.csv",
        "kpis": "kpis.csv",
    }

    data = {
        name: pd.read_csv(data_dir / filename)
        for name, filename in filenames.items()
    }

    # ---------------------------------------------------------
    # Canonical aliases for existing supervisory rules
    # ---------------------------------------------------------
    #
    # The real dataset calls this field "alert_status",
    # while some existing Phase 3 rules expect "status".
    #
    # Keep the original field untouched and expose a canonical
    # alias for analytics compatibility.
    #
    if "alert_status" in data["alerts"].columns:
        data["alerts"]["status"] = data["alerts"]["alert_status"]

    return data


def _safe_divide(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """Safe element-wise division."""

    result = numerator.astype(float).div(
        denominator.astype(float)
    )

    return result.where(
        denominator.astype(float) != 0
    )


def build_current_features(
    *,
    alerts: pd.DataFrame,
    cases: pd.DataFrame,
    investigations: pd.DataFrame,
    escalations: pd.DataFrame,
    assets: pd.DataFrame,
    monitoring: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build one canonical operational feature row per
    CSE and assessment period.
    """

    entities = set()

    for frame in (
        alerts,
        cases,
        investigations,
        escalations,
        assets,
        monitoring,
    ):
        if "cse_id" in frame.columns:
            entities.update(
                frame["cse_id"]
                .dropna()
                .astype(str)
                .unique()
            )

    periods = set()

    for frame in (
        alerts,
        cases,
        investigations,
        escalations,
        monitoring,
    ):
        if "assessment_period" in frame.columns:
            periods.update(
                frame["assessment_period"]
                .dropna()
                .astype(str)
                .unique()
            )

    base = pd.MultiIndex.from_product(
        [
            sorted(entities),
            sorted(periods),
        ],
        names=[
            "cse_id",
            "assessment_period",
        ],
    ).to_frame(index=False)

    # ---------------------------------------------------------
    # Alert metrics
    # ---------------------------------------------------------

    alert_group = (
        alerts.groupby(
            ["cse_id", "assessment_period"],
            dropna=False,
        )
        .agg(
            alert_count=("alert_id", "count"),
            alert_closure_rate=(
                "closure_timestamp",
                lambda x: x.notna().mean(),
            ),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # Case metrics
    # ---------------------------------------------------------

    case_group = (
        cases.groupby(
            ["cse_id", "assessment_period"],
            dropna=False,
        )
        .agg(
            case_count=("case_id", "count"),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # Investigation metrics
    # ---------------------------------------------------------

    investigation_group = (
        investigations.groupby(
            ["cse_id", "assessment_period"],
            dropna=False,
        )
        .agg(
            investigation_count=(
                "investigation_id",
                "count",
            ),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # Escalation metrics
    # ---------------------------------------------------------

    escalation_group = (
        escalations.groupby(
            ["cse_id", "assessment_period"],
            dropna=False,
        )
        .agg(
            escalation_count=(
                "escalation_id",
                "count",
            ),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # Monitoring metrics
    # ---------------------------------------------------------

    monitoring_group = (
        monitoring.groupby(
            ["cse_id", "assessment_period"],
            dropna=False,
        )
        .agg(
            monitoring_coverage=(
                "coverage",
                "mean",
            ),
            telemetry_availability_rate=(
                "telemetry_availability",
                lambda x: (
                    x.astype(str)
                    .str.lower()
                    .isin(
                        [
                            "available",
                            "yes",
                            "true",
                        ]
                    )
                    .mean()
                ),
            ),
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # Merge
    # ---------------------------------------------------------

    features = base.copy()

    for frame in (
        alert_group,
        case_group,
        investigation_group,
        escalation_group,
        monitoring_group,
    ):
        features = features.merge(
            frame,
            on=[
                "cse_id",
                "assessment_period",
            ],
            how="left",
        )

    numeric_columns = [
        column
        for column in features.columns
        if column not in (
            "cse_id",
            "assessment_period",
        )
    ]

    features[numeric_columns] = (
        features[numeric_columns]
        .fillna(0)
    )

    # ---------------------------------------------------------
    # Derived operational rates
    # ---------------------------------------------------------

    features["non_escalation_rate"] = (
        1
        - _safe_divide(
            features["escalation_count"],
            features["alert_count"],
        )
    ).fillna(0)

    features["escalation_rate"] = (
        _safe_divide(
            features["escalation_count"],
            features["alert_count"],
        )
    ).fillna(0)

    features["investigations_per_alert"] = (
        _safe_divide(
            features["investigation_count"],
            features["alert_count"],
        )
    ).fillna(0)

    features["investigations_per_case"] = (
        _safe_divide(
            features["investigation_count"],
            features["case_count"],
        )
    ).fillna(0)

    # ---------------------------------------------------------
    # Critical asset metrics
    # ---------------------------------------------------------

    asset_group = assets.copy()

    critical = (
        asset_group["asset_criticality"]
        .astype(str)
        .str.lower()
        .eq("critical")
    )

    asset_group["_critical"] = critical.astype(int)

    critical_by_cse = (
        asset_group.groupby("cse_id")
        .agg(
            critical_asset_rate=(
                "_critical",
                "mean",
            ),
        )
        .reset_index()
    )

    monitored = (
        asset_group["monitoring_status"]
        .astype(str)
        .str.lower()
        .eq("monitored")
    )

    asset_group["_critical_monitored"] = (
        critical & monitored
    ).astype(int)

    critical_monitoring = (
        asset_group.groupby("cse_id")
        .agg(
            critical_asset_monitoring_rate=(
                "_critical_monitored",
                "sum",
            ),
        )
        .reset_index()
    )

    critical_counts = (
        asset_group.groupby("cse_id")
        .agg(
            critical_asset_count=(
                "_critical",
                "sum",
            ),
        )
        .reset_index()
    )

    total_assets = (
        asset_group.groupby("cse_id")
        .agg(
            total_asset_count=(
                "asset_id",
                "count",
            )
        )
        .reset_index()
    )

    asset_metrics = (
        critical_counts
        .merge(
            total_assets,
            on="cse_id",
            how="left",
        )
        .merge(
            critical_monitoring,
            on="cse_id",
            how="left",
        )
        .merge(
            critical_by_cse,
            on="cse_id",
            how="left",
        )
    )

    asset_metrics[
        "critical_asset_monitoring_rate"
    ] = _safe_divide(
        asset_metrics[
            "critical_asset_monitoring_rate"
        ],
        asset_metrics["critical_asset_count"],
    ).fillna(0)

    features = features.merge(
        asset_metrics[
            [
                "cse_id",
                "critical_asset_rate",
                "critical_asset_monitoring_rate",
            ]
        ],
        on="cse_id",
        how="left",
    )

    features[
        [
            "critical_asset_rate",
            "critical_asset_monitoring_rate",
        ]
    ] = features[
        [
            "critical_asset_rate",
            "critical_asset_monitoring_rate",
        ]
    ].fillna(0)

    # Canonical entity name used by the existing analytics.
    features["entity_id"] = features["cse_id"]

    return features


def build_historical_features(
    historical: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize the supplied historical assessment records
    into the common CyberLens feature schema.
    """

    features = historical.copy()

    features["entity_id"] = features["cse_id"]

    rename_map = {
        "alert_volume": "alert_count",
        "closure_rate": "alert_closure_rate",
        "investigation_rate": "investigations_per_alert",
    }

    features = features.rename(
        columns=rename_map
    )

    return features


def build_capability_records(
    *,
    capabilities: pd.DataFrame,
    evidence_records: pd.DataFrame | None = None,
) -> list[dict[str, Any]]:
    """
    Convert real capability/evidence records into the
    canonical capability structure.

    This intentionally does not invent expected or observed
    numeric values.
    """

    evidence_records = (
        evidence_records
        if evidence_records is not None
        else pd.DataFrame()
    )

    records: list[dict[str, Any]] = []

    for _, row in capabilities.iterrows():

        entity_id = str(
            row.get("cse_id", "")
        ).strip()

        capability = str(
            row.get("capability_family", "")
        ).strip()

        if not entity_id or not capability:
            continue

        declared_raw = str(
            row.get(
                "declared_capability",
                "",
            )
        ).strip().lower()

        declared = declared_raw in {
            "true",
            "yes",
            "1",
            "available",
            "enabled",
            "supported",
        }

        source_ids: list[str] = []

        if not evidence_records.empty:

            matching = evidence_records[
                evidence_records["cse_id"].astype(str)
                == entity_id
            ]

            if "assessment_period" in matching.columns:
                period = str(
                    row.get(
                        "assessment_period",
                        "",
                    )
                )

                matching = matching[
                    matching[
                        "assessment_period"
                    ].astype(str)
                    == period
                ]

            if "source_record_id" in matching.columns:
                source_ids = (
                    matching[
                        "source_record_id"
                    ]
                    .dropna()
                    .astype(str)
                    .tolist()
                )

        records.append(
            {
                "entity_id": entity_id,
                "capability": capability,
                "declared": declared,
                "expected_value": None,
                "observed_value": None,
                "source_record_ids": source_ids,
            }
        )

    return records


def prepare_real_dataset(
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> dict[str, Any]:
    """
    Complete real-data preparation entry point.
    """

    data = load_real_dataset(data_dir)

    current_features = build_current_features(
        alerts=data["alerts"],
        cases=data["cases"],
        investigations=data["investigations"],
        escalations=data["escalations"],
        assets=data["assets"],
        monitoring=data["monitoring"],
    )

    historical_features = build_historical_features(
        data["historical"]
    )

    capability_records = build_capability_records(
        capabilities=data["capabilities"],
        evidence_records=data["evidence_records"],
    )

    return {
        **data,
        "current_features": current_features,
        "historical_features": historical_features,
        "capability_records": capability_records,
    }