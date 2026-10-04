from collections import Counter, defaultdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analytics.real_data_adapter import prepare_real_dataset
from analytics.supervisory_pipeline import run_supervisory_assessment


app = FastAPI(title="CyberLens API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory cache for the current demo assessment.
_assessment_cache = None


# Raw analytics signal -> frontend signal type.
SIGNAL_TYPE_MAP = {
    "EXECUTION_GAP": "execution_gap",
    "NEGATIVE_SPACE": "negative_space",
    "OPERATIONAL_ANOMALY": "anomaly",
    "ANOMALY": "anomaly",
    "PEER_COMPARISON": "peer_deviation",
    "HISTORICAL_DEVIATION": "statistical",
    "EXPECTED_EVIDENCE": "monitoring",
    "LIFECYCLE": "lifecycle",
    "CAPABILITY_EVIDENCE": "contradiction",

    # Compatibility with lowercase/internal names
    "execution_gap": "execution_gap",
    "negative_space": "negative_space",
    "operational_anomaly": "anomaly",
    "anomaly": "anomaly",
    "peer_comparison": "peer_deviation",
    "historical_benchmarking": "statistical",
    "historical_deviation": "statistical",
    "expected_evidence": "monitoring",
    "lifecycle": "lifecycle",
    "capability_evidence": "contradiction",
    "monitoring": "monitoring",
    "statistical": "statistical",
}


def frontend_signal_type(raw_type: str) -> str:
    value = str(raw_type or "")

    return SIGNAL_TYPE_MAP.get(
        value,
        SIGNAL_TYPE_MAP.get(value.upper(), "statistical"),
    )


def normalize_priority(priority: str) -> str:
    value = str(priority or "").upper()

    if value == "HIGH":
        return "High"

    if value == "MEDIUM":
        return "Medium"

    return "Low"


def run_real_assessment():
    global _assessment_cache

    if _assessment_cache is not None:
        return _assessment_cache

    data = prepare_real_dataset()

    periods = (
        data["current_features"]["assessment_period"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
    )

    if len(periods) == 0:
        raise ValueError("No assessment periods found.")

    current_period = periods[-1]

    result = run_supervisory_assessment(
        alerts=data["alerts"],
        cases=data["cases"],
        investigations=data["investigations"],
        escalations=data["escalations"],
        assets=data["assets"],
        monitoring=data["monitoring"],
        features=data["historical_features"],
        capabilities=data["capability_records"],
        assessment_id=f"REAL-{current_period}",
    )

    _assessment_cache = (data, result, current_period)

    return _assessment_cache


def build_overview(data, result, current_period):
    signals = result["signals"]

    # ---------------------------------------------------------
    # Priority distribution
    # ---------------------------------------------------------
    priority_counts = Counter(
        normalize_priority(signal.get("priority"))
        for signal in signals
    )

    priority_distribution = {
        "High": priority_counts.get("High", 0),
        "Medium": priority_counts.get("Medium", 0),
        "Low": priority_counts.get("Low", 0),
    }

    # ---------------------------------------------------------
    # Findings by frontend signal type
    # ---------------------------------------------------------
    signal_counts = Counter(
        frontend_signal_type(signal.get("signal_type", ""))
        for signal in signals
    )

    findings_by_type = [
        {
            "signal_type": signal_type,
            "count": count,
        }
        for signal_type, count in signal_counts.items()
    ]

    # ---------------------------------------------------------
    # Entity-level summaries
    # Use the actual Supervisory Signal Fusion review queue
    # because it contains the authoritative fused score.
    # ---------------------------------------------------------
    entity_data = defaultdict(
        lambda: {
            "findings": 0,
            "areas": Counter(),
        }
    )

    for signal in signals:
        entity_id = signal.get("entity_id", "UNKNOWN")

        entity_data[entity_id]["findings"] += 1

        entity_data[entity_id]["areas"][
            frontend_signal_type(signal.get("signal_type", ""))
        ] += 1

    # Actual fused supervisory scores come from the review queue.
    review_by_entity = {
        item["entity_id"]: item
        for item in result["review_queue"]
    }

    entity_summaries = []

    for entity_id, values in entity_data.items():
        areas = values["areas"]
        review = review_by_entity.get(entity_id, {})

        top_area = (
            areas.most_common(1)[0][0]
            if areas
            else "No dominant signal"
        )

        # Authoritative Supervisory Signal Fusion score.
        score = float(
            review.get("supervisory_score", 0)
        )

        entity_summaries.append(
            {
                "entity_id": entity_id,
                "name": entity_id,
                "fused_score": score,
                "findings": values["findings"],
                "top_area": top_area,
                "requires_review": bool(
                    review.get(
                        "human_review_required",
                        False,
                    )
                ),
            }
        )

    # Highest supervisory risk first.
    entity_summaries.sort(
        key=lambda x: x["fused_score"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # Review workload
    # ---------------------------------------------------------
    records_in_scope = len(data["alerts"])
    records_prioritized = len(result["review_queue"])

    sampling_reduction = (
        round(
            (1 - records_prioritized / records_in_scope) * 100,
            1,
        )
        if records_in_scope
        else 0
    )

    # ---------------------------------------------------------
    # Final frontend-compatible overview response
    # ---------------------------------------------------------
    return {
        "period": current_period,
        "entities_assessed": result["entity_count"],
        "entities_requiring_review": len(
            result["review_queue"]
        ),
        "total_findings": len(signals),
        "priority_distribution": priority_distribution,
        "findings_by_type": findings_by_type,
        "entity_summaries": entity_summaries,
        "review_workload": {
            "records_in_scope": records_in_scope,
            "records_prioritized": records_prioritized,
            "estimated_sampling_reduction_pct": sampling_reduction,
        },
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "CyberLens API",
    }


# ============================================================
# OVERVIEW
# ============================================================

@app.get("/overview")
def overview():
    data, result, current_period = run_real_assessment()

    return build_overview(
        data,
        result,
        current_period,
    )


# ============================================================
# FINDING BUILDER
# ============================================================

def build_frontend_finding(signal, review_by_entity):
    entity_id = signal.get(
        "entity_id",
        "UNKNOWN",
    )

    raw_type = signal.get(
        "signal_type",
        "",
    )

    frontend_type = frontend_signal_type(raw_type)

    priority = normalize_priority(
        signal.get("priority")
    )

    reason = signal.get(
        "reason",
        "Supervisory signal identified for review.",
    )

    evidence = signal.get("evidence") or []

    review = review_by_entity.get(
        entity_id,
        {},
    )

    score = float(
        review.get("supervisory_score", 0)
    )

    return {
        "finding_id": signal.get(
            "signal_id",
            f"FINDING-{entity_id}",
        ),

        "entity_id": entity_id,
        "entity_name": entity_id,

        "signal_type": frontend_type,
        "area": frontend_type,

        "priority": priority,

        "title": reason,

        "narrative": reason,

        "rule_model_name": signal.get(
            "rule_id",
            "CyberLens Analytics",
        ),

        "rule_model_version": signal.get(
            "rule_model_version",
            signal.get(
                "pipeline_version",
                "",
            ),
        ),

        "evidence": evidence,

        "source_record_ids": signal.get(
            "source_record_ids",
            [],
        ),

        "historical_context": signal.get(
            "historical_context",
            {},
        ),

        "peer_context": signal.get(
            "peer_context",
            {},
        ),

        "evidence_confidence": (
            str(
                signal.get(
                    "evidence_confidence",
                    "LOW",
                )
            ).title()
        ),

        "evidence_availability": (
            "Available"
            if evidence
            else "Limited"
        ),

        "fusion_score": score,

        "human_review_required": bool(
            signal.get(
                "human_review_required",
                review.get(
                    "human_review_required",
                    False,
                ),
            )
        ),

        "status": "Pending review",

        "assessment_id": signal.get(
            "assessment_id",
            "",
        ),

        "created_at": signal.get(
            "generated_at",
            "",
        ),
    }


# ============================================================
# FINDINGS
# ============================================================

@app.get("/findings")
def findings(entity_id: str | None = None):
    _, result, _ = run_real_assessment()

    review_by_entity = {
        item["entity_id"]: item
        for item in result["review_queue"]
    }

    findings = [
        build_frontend_finding(
            signal,
            review_by_entity,
        )
        for signal in result["signals"]
    ]

    if entity_id:
        findings = [
            finding
            for finding in findings
            if finding["entity_id"] == entity_id
        ]

    return findings


# ============================================================
# SIGNAL FUSION
# ============================================================

@app.get("/fusion")
def fusion(entity_id: str | None = None):
    _, result, current_period = run_real_assessment()

    review_queue = result.get(
        "review_queue",
        [],
    )

    review_by_entity = {
        item.get("entity_id"): item
        for item in review_queue
    }

    rows = []

    for entity_id_key, review in review_by_entity.items():

        if entity_id and str(entity_id_key) != str(entity_id):
            continue

        contributing_signals = [
            signal
            for signal in result.get("signals", [])
            if str(signal.get("entity_id", "")) == str(entity_id_key)
        ]

        signal_types = [
            frontend_signal_type(
                signal.get("signal_type", "")
            )
            for signal in contributing_signals
        ]

        rows.append(
            {
                "entity_id": entity_id_key,

                "assessment_period": current_period,

                "supervisory_score": float(
                    review.get(
                        "supervisory_score",
                        0,
                    )
                ),

                "priority": normalize_priority(
                    review.get("priority")
                ),

                "human_review_required": bool(
                    review.get(
                        "human_review_required",
                        False,
                    )
                ),

                "reason": review.get(
                    "reason",
                    "Supervisory signal fusion identified this entity for review.",
                ),

                "signal_count": len(
                    contributing_signals
                ),

                "signal_types": sorted(
                    set(signal_types)
                ),

                "contributing_signals": [
                    {
                        "finding_id": signal.get(
                            "signal_id",
                            f"FINDING-{entity_id_key}",
                        ),

                        "signal_type": frontend_signal_type(
                            signal.get(
                                "signal_type",
                                "",
                            )
                        ),

                        "priority": normalize_priority(
                            signal.get("priority")
                        ),

                        "reason": signal.get(
                            "reason",
                            "",
                        ),

                        "evidence": signal.get(
                            "evidence",
                            [],
                        ),

                        "evidence_confidence": str(
                            signal.get(
                                "evidence_confidence",
                                "LOW",
                            )
                        ).title(),
                    }
                    for signal in contributing_signals
                ],

                "historical_context": review.get(
                    "historical_context",
                    {},
                ),

                "peer_context": review.get(
                    "peer_context",
                    {},
                ),

                "evidence_confidence": str(
                    review.get(
                        "evidence_confidence",
                        "LOW",
                    )
                ).title(),

                "rule_model_version": result.get(
                    "pipeline_version",
                    "",
                ),
            }
        )

    rows.sort(
        key=lambda item: item["supervisory_score"],
        reverse=True,
    )

    return rows


# ============================================================
# EVIDENCE EXPLORER
# ============================================================

@app.get("/evidence")
def evidence():
    _, result, _ = run_real_assessment()

    rows = []

    for signal in result.get("signals", []):

        entity_id = signal.get(
            "entity_id",
            "UNKNOWN",
        )

        finding_id = signal.get(
            "signal_id",
            f"FINDING-{entity_id}",
        )

        signal_type = frontend_signal_type(
            signal.get(
                "signal_type",
                "",
            )
        )

        confidence = str(
            signal.get(
                "evidence_confidence",
                "LOW",
            )
        ).title()

        evidence_items = signal.get(
            "evidence"
        ) or []

        for index, item in enumerate(
            evidence_items,
            start=1,
        ):

            if not isinstance(item, dict):
                item = {
                    "value": item
                }

            evidence_type = str(
                item.get(
                    "type",
                    "Supporting evidence",
                )
            )

            detail_parts = []

            for key, value in item.items():

                if key == "type":
                    continue

                if value is None:
                    continue

                if isinstance(
                    value,
                    (dict, list),
                ):
                    value = str(value)

                detail_parts.append(
                    f"{key}: {value}"
                )

            detail = (
                " · ".join(detail_parts)
                if detail_parts
                else "Supporting evidence linked to this supervisory signal."
            )

            # -------------------------------------------------
            # IMPORTANT:
            # Frontend expects source_record_ids: string[]
            # Some analytics modules may return dict/set/scalar.
            # Normalize everything to a string list.
            # -------------------------------------------------

            source_record_ids = signal.get(
                "source_record_ids",
                [],
            ) or []

            if isinstance(
                source_record_ids,
                dict,
            ):
                source_record_ids = list(
                    source_record_ids.keys()
                )

            elif isinstance(
                source_record_ids,
                (set, tuple),
            ):
                source_record_ids = list(
                    source_record_ids
                )

            elif not isinstance(
                source_record_ids,
                list,
            ):
                source_record_ids = [
                    source_record_ids
                ]

            source_record_ids = [
                str(record_id)
                for record_id in source_record_ids
                if record_id is not None
            ]

            rows.append(
                {
                    "evidence_id": (
                        f"{finding_id}-E{index}"
                    ),

                    "finding_id": finding_id,

                    "entity_id": entity_id,

                    "entity_name": entity_id,

                    "signal_type": signal_type,

                    "label": evidence_type,

                    "detail": detail,

                    "confidence": confidence,

                    "source_record_ids": source_record_ids,
                }
            )

    return rows


# ============================================================
# ASSESSMENTS
# ============================================================

@app.get("/assessments")
def assessments():
    _, result, current_period = run_real_assessment()

    return [
        {
            "assessment_id": f"REAL-{current_period}",

            "period": current_period,

            "started_at": result["metadata"].get(
                "started_at",
                "",
            ),

            "completed_at": result["metadata"].get(
                "completed_at",
                "",
            ),

            "entities": result["entity_count"],

            "findings": len(
                result["signals"]
            ),

            "rule_model_version": result[
                "pipeline_version"
            ],

            "data_completeness_pct": 100,

            "status": "Complete",
        }
    ]


# ============================================================
# STATISTICS
# ============================================================

@app.get("/statistics/{entity_id}")
def statistics(entity_id: str):
    data, result, current_period = run_real_assessment()

    features = data[
        "historical_features"
    ].copy()

    entity_rows = features[
        features["cse_id"].astype(str)
        == str(entity_id)
    ]

    if entity_rows.empty:
        return []

    numeric_columns = [
        column
        for column in entity_rows.columns
        if column not in {
            "cse_id",
            "assessment_period",
        }
        and entity_rows[column].dtype.kind
        in "biufc"
    ]

    results = []

    for metric in numeric_columns:

        entity_values = (
            entity_rows[metric]
            .dropna()
            .astype(float)
        )

        if entity_values.empty:
            continue

        value = float(
            entity_values.iloc[-1]
        )

        all_values = (
            features[metric]
            .dropna()
            .astype(float)
        )

        if all_values.empty:
            continue

        median = float(
            all_values.median()
        )

        q1 = float(
            all_values.quantile(0.25)
        )

        q3 = float(
            all_values.quantile(0.75)
        )

        iqr = q3 - q1

        if iqr == 0:
            z_score = 0.0
        else:
            z_score = float(
                (value - median) / iqr
            )

        percentile = float(
            (all_values <= value).mean()
            * 100
        )

        flagged = bool(
            value < q1 - 1.5 * iqr
            or value > q3 + 1.5 * iqr
        )

        results.append(
            {
                "metric": metric,

                "value": round(
                    value,
                    4,
                ),

                "median": round(
                    median,
                    4,
                ),

                "iqr_low": round(
                    q1,
                    4,
                ),

                "iqr_high": round(
                    q3,
                    4,
                ),

                "z_score": round(
                    z_score,
                    4,
                ),

                "percentile": round(
                    percentile,
                    2,
                ),

                "flagged": flagged,
            }
        )

    return results


# ============================================================
# PEER COMPARISON
# ============================================================

@app.get("/peer-comparison")
def peer_comparison(
    entity_id: str = "CSE-001",
):
    data, result, current_period = run_real_assessment()

    rows = []

    for signal in result["signals"]:

        if frontend_signal_type(
            signal.get(
                "signal_type",
                "",
            )
        ) != "peer_deviation":
            continue

        if str(
            signal.get(
                "entity_id",
                "",
            )
        ) != str(entity_id):
            continue

        evidence_items = (
            signal.get("evidence")
            or []
        )

        for evidence in evidence_items:

            if evidence.get(
                "type"
            ) != "peer_deviation":
                continue

            entity_value = evidence.get(
                "entity_value"
            )

            peer_median = evidence.get(
                "peer_median"
            )

            if (
                entity_value is None
                or peer_median is None
            ):
                continue

            peer_mean = evidence.get(
                "peer_mean"
            )

            deviation_percent = evidence.get(
                "deviation_percent"
            )

            peer_count = evidence.get(
                "peer_count",
                signal.get(
                    "peer_context",
                    {}
                ).get(
                    "peer_count",
                    0,
                ),
            )

            rows.append(
                {
                    "entity_id": entity_id,

                    "assessment_period": current_period,

                    "metric": evidence.get(
                        "feature",
                        "Unknown metric",
                    ),

                    "entity_value": entity_value,

                    "peer_median": peer_median,

                    "peer_mean": peer_mean,

                    "peer_p25": None,

                    "peer_p75": None,

                    "percentile": None,

                    "deviation_percent": deviation_percent,

                    "direction": evidence.get(
                        "direction",
                        "",
                    ),

                    "peer_count": peer_count,

                    "unit": "",

                    "priority": normalize_priority(
                        signal.get(
                            "priority"
                        )
                    ),

                    "reason": signal.get(
                        "reason",
                        "Peer deviation identified.",
                    ),

                    "evidence_confidence": str(
                        signal.get(
                            "evidence_confidence",
                            "LOW",
                        )
                    ).title(),
                }
            )

    return rows


# ============================================================
# HISTORICAL BENCHMARKING
# ============================================================

@app.get("/history")
def history(
    entity_id: str = "CSE-001",
):
    data, result, current_period = run_real_assessment()

    features = data[
        "historical_features"
    ].copy()

    entity_rows = features[
        features["cse_id"].astype(str)
        == str(entity_id)
    ].copy()

    if entity_rows.empty:
        return []

    entity_rows = entity_rows.sort_values(
        "assessment_period"
    )

    numeric_columns = [
        column
        for column in entity_rows.columns
        if column not in {
            "cse_id",
            "assessment_period",
        }
        and entity_rows[column].dtype.kind
        in "biufc"
    ]

    rows = []

    for metric in numeric_columns:

        values = entity_rows[
            [
                "assessment_period",
                metric,
            ]
        ].dropna()

        if values.empty:
            continue

        history = [
            {
                "period": str(
                    row["assessment_period"]
                ),
                "value": float(
                    row[metric]
                ),
            }
            for _, row in values.iterrows()
        ]

        current_value = history[-1]["value"]

        previous_value = (
            history[-2]["value"]
            if len(history) >= 2
            else None
        )

        change_percent = None

        if previous_value not in (
            None,
            0,
        ):
            change_percent = (
                (
                    current_value
                    - previous_value
                )
                / abs(previous_value)
            ) * 100

        rows.append(
            {
                "entity_id": entity_id,

                "metric": metric,

                "current_value": current_value,

                "previous_value": previous_value,

                "change_percent": (
                    round(
                        change_percent,
                        2,
                    )
                    if change_percent is not None
                    else None
                ),

                "history": history,

                "assessment_period": current_period,
            }
        )

    return rows