"""
CyberLens Supervisory Assessment Pipeline
------------------------------------------

Integrates Phase 3 Supervisory Intelligence and Phase 4
Anomaly & Behaviour Analytics into one offline assessment flow.

Flow:

SOC/CSE Data
    ↓
Supervisory Intelligence
    ├── Negative Space
    ├── Expected Evidence
    ├── Lifecycle Intelligence
    ├── Peer Comparison
    ├── Historical Benchmarking
    └── Capability–Evidence Analysis
    ↓
Anomaly & Behaviour Analytics
    ↓
Supervisory Signal Fusion
    ↓
Review Prioritization
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from analytics.supervisory.negative_space import (
    detect_negative_space,
)

from analytics.supervisory.expected_evidence import (
    build_expected_evidence_signals,
)

from analytics.supervisory.lifecycle_intelligence import (
    build_lifecycle_signals,
)

from analytics.supervisory.peer_comparison import (
    build_peer_comparison_signals,
)

from analytics.supervisory.historical_benchmarking import (
    build_historical_benchmark_signals,
)

from analytics.supervisory.capability_evidence import (
    detect_capability_evidence_contradictions,
)

from analytics.supervisory.signal_fusion import (
    build_supervisory_signals,
)

from analytics.anomaly_detection.pipeline import (
    run_anomaly_pipeline,
)


VERSION = "cyberlens-integrated-pipeline-0.1.0"


def _empty_frame() -> pd.DataFrame:
    """Return an empty dataframe for optional datasets."""

    return pd.DataFrame()


def _combine_signals(
    *signal_groups: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Combine signal groups while preserving every underlying signal."""

    combined: List[Dict[str, Any]] = []

    for group in signal_groups:
        if group:
            combined.extend(group)

    return combined


def _extract_entity_ids(
    *frames: Optional[pd.DataFrame],
) -> List[str]:
    """Collect entity IDs from all available input frames."""

    entity_ids = set()

    for frame in frames:
        if frame is None or frame.empty:
            continue

        if "entity_id" in frame.columns:
            values = frame["entity_id"].dropna().astype(str)
            entity_ids.update(values.tolist())

    return sorted(entity_ids)


def _build_review_queue(
    fused_signals: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert fused supervisory signals into a simple review queue.

    The queue retains the full fused signal for auditability.
    """

    priority_order = {
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    queue = []

    for rank, signal in enumerate(
        sorted(
            fused_signals,
            key=lambda item: (
                priority_order.get(item.get("priority"), 0),
                item.get("supervisory_score", 0),
            ),
            reverse=True,
        ),
        start=1,
    ):
        queue.append(
            {
                "review_rank": rank,
                "entity_id": signal.get("entity_id"),
                "priority": signal.get("priority"),
                "supervisory_score": signal.get(
                    "supervisory_score",
                    0,
                ),
                "contributing_signal_count": signal.get(
                    "contributing_signal_count",
                    0,
                ),
                "signal_id": signal.get("signal_id"),
                "reason": signal.get("reason"),
                "human_review_required": signal.get(
                    "human_review_required",
                    True,
                ),
            }
        )

    return queue


def run_supervisory_assessment(
    *,
    alerts: Optional[pd.DataFrame] = None,
    cases: Optional[pd.DataFrame] = None,
    investigations: Optional[pd.DataFrame] = None,
    escalations: Optional[pd.DataFrame] = None,
    assets: Optional[pd.DataFrame] = None,
    monitoring: Optional[pd.DataFrame] = None,
    features: Optional[pd.DataFrame] = None,
    capabilities: Optional[List[Dict[str, Any]]] = None,
    assessment_id: str = "ASSESSMENT-001",
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the complete CyberLens supervisory assessment.

    This function does not connect to a database, API, cloud service,
    SIEM, or external AI system. All processing is local.
    """

    alerts = alerts if alerts is not None else _empty_frame()
    cases = cases if cases is not None else _empty_frame()
    investigations = (
        investigations
        if investigations is not None
        else _empty_frame()
    )
    escalations = (
        escalations
        if escalations is not None
        else _empty_frame()
    )
    assets = assets if assets is not None else _empty_frame()
    monitoring = (
        monitoring
        if monitoring is not None
        else _empty_frame()
    )

    # ---------------------------------------------------------
    # PHASE 3 — SUPERVISORY INTELLIGENCE
    # ---------------------------------------------------------

    negative_space_signals = detect_negative_space(
        alerts=alerts,
        cases=cases,
        investigations=investigations,
        escalations=escalations,
        assets=assets,
        monitoring=monitoring,
    )

    expected_evidence_signals = build_expected_evidence_signals(
        alerts=alerts,
        cases=cases,
        investigations=investigations,
        escalations=escalations,
        assets=assets,
        monitoring=monitoring,
    )

    lifecycle_signals = build_lifecycle_signals(
        alerts=alerts,
        cases=cases,
        investigations=investigations,
        escalations=escalations,
    )

    # Peer / historical analysis requires feature data.
    peer_signals: List[Dict[str, Any]] = []
    historical_signals: List[Dict[str, Any]] = []

    if features is not None and not features.empty:
        peer_signals = build_peer_comparison_signals(
            features
        )

        # Historical benchmarking only runs when a period column
        # is available.
        if any(
            column in features.columns
            for column in [
                "assessment_period",
                "assessment_id",
                "period",
                "period_id",
                "assessment_date",
            ]
        ):
            historical_signals = (
                build_historical_benchmark_signals(
                    features
                )
            )

    capability_signals: List[Dict[str, Any]] = []

    if capabilities:
        capability_signals = (
            detect_capability_evidence_contradictions(
                capabilities
            )
        )

    # ---------------------------------------------------------
    # PHASE 4 — ANOMALY & BEHAVIOUR ANALYTICS
    # ---------------------------------------------------------

    anomaly_result = run_anomaly_pipeline(
        alerts=alerts,
        cases=cases,
        investigations=investigations,
        escalations=escalations,
        assets=assets,
        monitoring=monitoring,
        assessment_id=assessment_id,
        period_start=period_start,
        period_end=period_end,
    )

    anomaly_signals = anomaly_result.get(
        "signals",
        [],
    )

    # ---------------------------------------------------------
    # COMBINE ALL ANALYTICAL SIGNALS
    # ---------------------------------------------------------

    all_signals = _combine_signals(
        negative_space_signals,
        expected_evidence_signals,
        lifecycle_signals,
        peer_signals,
        historical_signals,
        capability_signals,
        anomaly_signals,
    )

    # ---------------------------------------------------------
    # FINAL SUPERVISORY SIGNAL FUSION
    # ---------------------------------------------------------

    fused_signals = build_supervisory_signals(
        all_signals,
        assessment_id=assessment_id,
    )

    # ---------------------------------------------------------
    # REVIEW PRIORITIZATION
    # ---------------------------------------------------------

    review_queue = _build_review_queue(
        fused_signals
    )

    # ---------------------------------------------------------
    # METADATA
    # ---------------------------------------------------------

    entity_ids = _extract_entity_ids(
        alerts,
        cases,
        investigations,
        escalations,
        assets,
        monitoring,
        features,
    )

    return {
        "pipeline_version": VERSION,
        "assessment_id": assessment_id,
        "entity_count": len(entity_ids),
        "entity_ids": entity_ids,

        "signal_counts": {
            "negative_space": len(
                negative_space_signals
            ),
            "expected_evidence": len(
                expected_evidence_signals
            ),
            "lifecycle": len(
                lifecycle_signals
            ),
            "peer_comparison": len(
                peer_signals
            ),
            "historical_benchmarking": len(
                historical_signals
            ),
            "capability_evidence": len(
                capability_signals
            ),
            "anomaly": len(
                anomaly_signals
            ),
            "combined": len(
                all_signals
            ),
            "fused": len(
                fused_signals
            ),
        },

        "signals": all_signals,

        "supervisory_signals": fused_signals,

        "review_queue": review_queue,

        "anomaly_result": anomaly_result,

        "metadata": {
            "period_start": period_start,
            "period_end": period_end,
            "offline_processing": True,
            "external_ai_required": False,
            "cloud_dependency": False,
        },
    }


def run_pipeline(
    **kwargs: Any,
) -> Dict[str, Any]:
    """Convenience wrapper."""

    return run_supervisory_assessment(**kwargs)