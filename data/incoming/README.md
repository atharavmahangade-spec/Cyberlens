# CyberLens Filtered Synthetic SOC/CSE Dataset

This dataset is designed for the CyberLens project mapped to Smart India Hackathon Problem Statement 26157 (Supervisory Analytics Tool for SOC Assessment).

## What is included

### Core PS-aligned operational evidence
- cse_entities.csv
- alerts.csv
- investigations.csv
- escalations.csv
- cases.csv
- assets.csv

### CyberLens supporting analytical data
- assessment_periods.csv
- monitoring_evidence.csv
- historical_assessments.csv
- capabilities.csv
- kpis.csv
- evidence_records.csv
- control_mappings.csv
- expected_evidence.csv

### Validation-only material
- ground_truth.csv — DO NOT give this file to CyberLens during normal inference.
- scenario_catalogue.csv
- data_quality_test_cases.csv
- validation_report.txt

### Documentation / generation
- data_dictionary.csv
- dataset_manifest.json
- generate_cyberlens_dataset.py

## Design principle
Operational data contains evidence, not conclusions. There are no fields such as `risk_score`, `execution_gap=true`, or `negative_space=true` in the core evidence tables. CyberLens should derive signals from the relationships, timing, missingness, baselines, peer context and evidence availability.

## Dataset scale
- 30 fictional CSEs
- 6 quarterly assessment periods
- Tens of thousands of alert records plus linked investigations, escalations and cases
- Asset and monitoring evidence supporting negative-space and coverage analysis

## Intended analytics
The dataset is structured to exercise:
1. Lifecycle intelligence
2. Expected evidence comparison
3. Negative-space detection
4. Execution-gap detection
5. Peer comparison
6. Historical self-benchmarking
7. Capability/evidence contradiction analysis
8. Statistical anomaly detection
9. Isolation Forest or other unsupervised anomaly methods
10. Supervisory signal fusion
11. Review prioritization
12. Explainability and source-record traceability

## Important
All records are synthetic and fictional. This dataset does not represent real CSE infrastructure, real credentials, real customers, or real raw telemetry. It is intended for offline prototype development and validation.
