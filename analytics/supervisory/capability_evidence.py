"""
Capability–Evidence Analysis
----------------------------

Compares documented/declared SOC capabilities with observed operational
evidence to identify capability–evidence contradictions.

This module is supervisory analytics only.
It does not replace SOC monitoring, SIEM, or real-time detection.

Version: cyberlens-phase3-capability-evidence-0.1.0
"""

from __future__ import annotations

from typing import Any, Dict, List


VERSION = "cyberlens-phase3-capability-evidence-0.1.0"


def _make_signal(
    entity_id: str,
    rule_id: str,
    category: str,
    priority: str,
    reason: str,
    capability: str,
    expected_value: Any,
    observed_value: Any,
    evidence: List[Dict[str, Any]],
    source_record_ids: List[str],
    confidence: str = "HIGH",
) -> Dict[str, Any]:
    return {
        "signal_id": f"{rule_id}-{entity_id}",
        "signal_type": "CAPABILITY_EVIDENCE_CONTRADICTION",
        "rule_id": rule_id,
        "category": category,
        "priority": priority,
        "reason": reason,
        "evidence": evidence,
        "source_record_ids": source_record_ids,
        "historical_context": {},
        "peer_context": {},
        "evidence_confidence": confidence,
        "rule_model_version": VERSION,
        "entity_id": entity_id,
        "human_review_required": True,
        "capability": capability,
        "expected_value": expected_value,
        "observed_value": observed_value,
    }


def detect_capability_evidence_contradictions(
    capabilities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Detect contradictions between documented SOC capabilities and
    observed operational evidence.

    Expected input format:

    [
        {
            "entity_id": "CSE-001",
            "capability": "critical_asset_monitoring",
            "declared": True,
            "expected_value": 100,
            "observed_value": 62,
            "source_record_ids": ["CAP-001", "MON-001"]
        }
    ]

    Returns standardized supervisory signals.
    """

    signals: List[Dict[str, Any]] = []

    for item in capabilities:
        entity_id = item.get("entity_id")
        capability = item.get("capability")

        if not entity_id or not capability:
            continue

        declared = item.get("declared")
        expected_value = item.get("expected_value")
        observed_value = item.get("observed_value")
        source_record_ids = item.get("source_record_ids", [])

        # ---------------------------------------------------------
        # CAP-001: Declared capability exists but observed evidence
        # is materially below the expected level.
        # ---------------------------------------------------------
        if (
            declared is True
            and isinstance(expected_value, (int, float))
            and isinstance(observed_value, (int, float))
            and expected_value > 0
            and observed_value < expected_value
        ):
            gap_percent = (
                (expected_value - observed_value) / expected_value
            ) * 100

            if gap_percent >= 50:
                priority = "HIGH"
            elif gap_percent >= 25:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            signals.append(
                _make_signal(
                    entity_id=entity_id,
                    rule_id="CAP-001",
                    category="CAPABILITY_EVIDENCE_GAP",
                    priority=priority,
                    reason=(
                        f"Documented capability '{capability}' indicates "
                        f"an expected value of {expected_value}, but observed "
                        f"evidence indicates {observed_value}."
                    ),
                    capability=capability,
                    expected_value=expected_value,
                    observed_value=observed_value,
                    evidence=[
                        {
                            "type": "capability_evidence_comparison",
                            "capability": capability,
                            "declared": declared,
                            "expected_value": expected_value,
                            "observed_value": observed_value,
                            "gap_percent": round(gap_percent, 2),
                        }
                    ],
                    source_record_ids=source_record_ids,
                )
            )

        # ---------------------------------------------------------
        # CAP-002: Capability is declared but no observed evidence
        # is available.
        # ---------------------------------------------------------
        elif declared is True and observed_value is None:
            signals.append(
                _make_signal(
                    entity_id=entity_id,
                    rule_id="CAP-002",
                    category="CAPABILITY_EVIDENCE_ABSENCE",
                    priority="HIGH",
                    reason=(
                        f"Capability '{capability}' is documented as "
                        "available, but corresponding operational evidence "
                        "was not observed."
                    ),
                    capability=capability,
                    expected_value=expected_value,
                    observed_value=None,
                    evidence=[
                        {
                            "type": "missing_capability_evidence",
                            "capability": capability,
                            "declared": declared,
                            "expected_value": expected_value,
                            "observed_value": None,
                        }
                    ],
                    source_record_ids=source_record_ids,
                )
            )

    return signals