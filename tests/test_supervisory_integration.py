import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
import pandas as pd

from analytics.supervisory_pipeline import (
    run_supervisory_assessment,
)


def build_test_data():
    entities = [
        "CSE-001",
        "CSE-002",
        "CSE-003",
        "CSE-004",
        "CSE-005",
        "CSE-006",
    ]

    # ---------------------------------------------------------
    # ALERTS
    # ---------------------------------------------------------

    alerts = pd.DataFrame(
        [
            {
                "alert_id": "A-001",
                "entity_id": "CSE-001",
                "severity": "CRITICAL",
                "status": "CLOSED",
                "closure_hours": 1.0,
            },
            {
                "alert_id": "A-002",
                "entity_id": "CSE-001",
                "severity": "HIGH",
                "status": "OPEN",
                "closure_hours": None,
            },
            {
                "alert_id": "A-003",
                "entity_id": "CSE-002",
                "severity": "HIGH",
                "status": "CLOSED",
                "closure_hours": 20.0,
            },
            {
                "alert_id": "A-004",
                "entity_id": "CSE-003",
                "severity": "MEDIUM",
                "status": "CLOSED",
                "closure_hours": 15.0,
            },
            {
                "alert_id": "A-005",
                "entity_id": "CSE-004",
                "severity": "HIGH",
                "status": "CLOSED",
                "closure_hours": 18.0,
            },
            {
                "alert_id": "A-006",
                "entity_id": "CSE-005",
                "severity": "MEDIUM",
                "status": "CLOSED",
                "closure_hours": 17.0,
            },
            {
                "alert_id": "A-007",
                "entity_id": "CSE-006",
                "severity": "MEDIUM",
                "status": "CLOSED",
                "closure_hours": 16.0,
            },
        ]
    )

    # ---------------------------------------------------------
    # INVESTIGATIONS
    # ---------------------------------------------------------

    investigations = pd.DataFrame(
        [
            {
                "investigation_id": "I-001",
                "entity_id": "CSE-001",
                "alert_id": "A-001",
                "status": "COMPLETED",
            },
            {
                "investigation_id": "I-002",
                "entity_id": "CSE-002",
                "alert_id": "A-003",
                "status": "COMPLETED",
            },
            {
                "investigation_id": "I-003",
                "entity_id": "CSE-003",
                "alert_id": "A-004",
                "status": "COMPLETED",
            },
            {
                "investigation_id": "I-004",
                "entity_id": "CSE-004",
                "alert_id": "A-005",
                "status": "COMPLETED",
            },
            {
                "investigation_id": "I-005",
                "entity_id": "CSE-005",
                "alert_id": "A-006",
                "status": "COMPLETED",
            },
            {
                "investigation_id": "I-006",
                "entity_id": "CSE-006",
                "alert_id": "A-007",
                "status": "COMPLETED",
            },
        ]
    )

    # ---------------------------------------------------------
    # ESCALATIONS
    # ---------------------------------------------------------

    escalations = pd.DataFrame(
        [
            {
                "escalation_id": "E-001",
                "entity_id": "CSE-001",
                "investigation_id": "I-001",
                "status": "ESCALATED",
            },
            {
                "escalation_id": "E-002",
                "entity_id": "CSE-002",
                "investigation_id": "I-002",
                "status": "ESCALATED",
            },
            {
                "escalation_id": "E-003",
                "entity_id": "CSE-004",
                "investigation_id": "I-004",
                "status": "ESCALATED",
            },
            {
                "escalation_id": "E-004",
                "entity_id": "CSE-005",
                "investigation_id": "I-005",
                "status": "ESCALATED",
            },
            {
                "escalation_id": "E-005",
                "entity_id": "CSE-006",
                "investigation_id": "I-006",
                "status": "ESCALATED",
            },
        ]
    )

    # ---------------------------------------------------------
    # CASES
    # ---------------------------------------------------------

    cases = pd.DataFrame(
        [
            {
                "case_id": "CASE-001",
                "entity_id": "CSE-001",
                "investigation_id": "I-001",
                "status": "OPEN",
            },
            {
                "case_id": "CASE-002",
                "entity_id": "CSE-002",
                "investigation_id": "I-002",
                "status": "CLOSED",
                "resolution": "Remediated",
            },
            {
                "case_id": "CASE-003",
                "entity_id": "CSE-003",
                "investigation_id": "I-003",
                "status": "CLOSED",
                "resolution": "Remediated",
            },
        ]
    )

    # ---------------------------------------------------------
    # ASSETS
    # ---------------------------------------------------------

    assets = pd.DataFrame(
        [
            {
                "asset_id": "ASSET-001",
                "entity_id": "CSE-001",
                "criticality": "CRITICAL",
                "monitored": False,
            },
            {
                "asset_id": "ASSET-002",
                "entity_id": "CSE-001",
                "criticality": "HIGH",
                "monitored": False,
            },
            {
                "asset_id": "ASSET-003",
                "entity_id": "CSE-002",
                "criticality": "HIGH",
                "monitored": True,
            },
            {
                "asset_id": "ASSET-004",
                "entity_id": "CSE-003",
                "criticality": "MEDIUM",
                "monitored": True,
            },
            {
                "asset_id": "ASSET-005",
                "entity_id": "CSE-004",
                "criticality": "HIGH",
                "monitored": True,
            },
            {
                "asset_id": "ASSET-006",
                "entity_id": "CSE-005",
                "criticality": "HIGH",
                "monitored": True,
            },
            {
                "asset_id": "ASSET-007",
                "entity_id": "CSE-006",
                "criticality": "HIGH",
                "monitored": True,
            },
        ]
    )

    # ---------------------------------------------------------
    # MONITORING
    # ---------------------------------------------------------

    monitoring = pd.DataFrame(
        [
            {
                "entity_id": "CSE-001",
                "monitoring_coverage": 0.20,
            },
            {
                "entity_id": "CSE-002",
                "monitoring_coverage": 0.85,
            },
            {
                "entity_id": "CSE-003",
                "monitoring_coverage": 0.82,
            },
            {
                "entity_id": "CSE-004",
                "monitoring_coverage": 0.88,
            },
            {
                "entity_id": "CSE-005",
                "monitoring_coverage": 0.86,
            },
            {
                "entity_id": "CSE-006",
                "monitoring_coverage": 0.87,
            },
        ]
    )

    # ---------------------------------------------------------
    # CURRENT FEATURES + HISTORICAL PERIODS
    # ---------------------------------------------------------

    feature_rows = []

    historical_values = {
        "CSE-001": [
            (70, 65, 90),
            (72, 66, 91),
            (69, 67, 90),
            (71, 66, 91),
            (95, 5, 89),
        ],
        "CSE-002": [
            (70, 60, 85),
            (71, 61, 86),
            (69, 59, 84),
            (70, 60, 85),
            (71, 61, 86),
        ],
        "CSE-003": [
            (68, 62, 82),
            (69, 63, 83),
            (70, 64, 82),
            (69, 63, 83),
            (70, 64, 82),
        ],
        "CSE-004": [
            (72, 65, 88),
            (71, 66, 87),
            (73, 64, 89),
            (72, 65, 88),
            (71, 66, 88),
        ],
        "CSE-005": [
            (69, 61, 86),
            (70, 62, 87),
            (68, 60, 85),
            (69, 61, 86),
            (70, 62, 86),
        ],
        "CSE-006": [
            (71, 63, 87),
            (70, 64, 88),
            (72, 62, 87),
            (71, 63, 88),
            (70, 64, 87),
        ],
    }

    for entity_id, values in historical_values.items():
        for index, (closure, escalation, coverage) in enumerate(
            values,
            start=1,
        ):
            feature_rows.append(
                {
                    "entity_id": entity_id,
                    "assessment_period": f"2026-Q{index}",
                    "alert_closure_rate": closure,
                    "escalation_rate": escalation,
                    "monitoring_coverage": coverage,
                }
            )

    features = pd.DataFrame(feature_rows)

    # ---------------------------------------------------------
    # CAPABILITY / EVIDENCE
    # ---------------------------------------------------------

    capabilities = [
        {
            "entity_id": "CSE-001",
            "capability": "critical_asset_monitoring",
            "declared": True,
            "expected_value": 100,
            "observed_value": 20,
            "source_record_ids": [
                "CAP-001",
                "MON-001",
            ],
        },
        {
            "entity_id": "CSE-002",
            "capability": "incident_response",
            "declared": True,
            "expected_value": 100,
            "observed_value": 40,
            "source_record_ids": [
                "CAP-002",
                "IR-002",
            ],
        },
        {
            "entity_id": "CSE-003",
            "capability": "escalation_process",
            "declared": True,
            "expected_value": 100,
            "observed_value": None,
            "source_record_ids": [
                "CAP-003",
            ],
        },
    ]

    return {
        "alerts": alerts,
        "cases": cases,
        "investigations": investigations,
        "escalations": escalations,
        "assets": assets,
        "monitoring": monitoring,
        "features": features,
        "capabilities": capabilities,
    }


def test_full_supervisory_pipeline():
    data = build_test_data()

    result = run_supervisory_assessment(
        **data,
        assessment_id="CYBERLENS-PHASE3-4-E2E",
        period_start="2026-01-01",
        period_end="2026-12-31",
    )

    print("\n========================================")
    print("CYBERLENS PHASE 3 + 4 E2E TEST")
    print("========================================")

    print(
        "Pipeline:",
        result["pipeline_version"],
    )

    print(
        "Entities:",
        result["entity_count"],
    )

    print("\nSIGNAL COUNTS")

    for key, value in result["signal_counts"].items():
        print(f"{key}: {value}")

    print("\nSUPERVISORY SIGNALS")

    for signal in result["supervisory_signals"]:
        print(
            signal["entity_id"],
            "|",
            signal["priority"],
            "| score:",
            signal["supervisory_score"],
            "| contributing:",
            signal["contributing_signal_count"],
        )

    print("\nREVIEW QUEUE")

    for item in result["review_queue"]:
        print(
            f"#{item['review_rank']}",
            item["entity_id"],
            item["priority"],
            item["supervisory_score"],
        )

    # ---------------------------------------------------------
    # CORE ASSERTIONS
    # ---------------------------------------------------------

    assert result["entity_count"] == 6

    assert result["signal_counts"]["negative_space"] > 0

    assert result["signal_counts"]["expected_evidence"] > 0

    assert result["signal_counts"]["lifecycle"] > 0

    assert result["signal_counts"]["peer_comparison"] > 0

    assert result["signal_counts"]["historical_benchmarking"] > 0

    assert result["signal_counts"]["capability_evidence"] == 3

    assert result["signal_counts"]["combined"] > 0

    assert result["signal_counts"]["fused"] > 0

    assert len(result["review_queue"]) > 0

    # CSE-001 was deliberately constructed with
    # multiple independent supervisory weaknesses.
    cse001 = next(
        signal
        for signal in result["supervisory_signals"]
        if signal["entity_id"] == "CSE-001"
    )

    assert cse001["contributing_signal_count"] >= 2

    assert cse001["priority"] == "HIGH"

    assert cse001["human_review_required"] is True

    assert len(cse001["source_record_ids"]) > 0

    # Verify the complete evidence chain survives fusion.
    assert len(cse001["evidence"]) >= 2

    # Verify offline architecture metadata.
    assert result["metadata"]["offline_processing"] is True

    assert result["metadata"]["external_ai_required"] is False

    assert result["metadata"]["cloud_dependency"] is False

    print("\n========================================")
    print("PHASE 3 + 4 E2E TEST: PASSED")
    print("========================================")


if __name__ == "__main__":
    test_full_supervisory_pipeline()