# CyberLens

## Supervisory Analytics Tool for SOC Assessment (SAT-SA)

CyberLens is an **offline, evidence-driven supervisory analytics platform** designed to support NCIIPC-style assessment of Security Operations Centre (SOC) capabilities across Cyber Security Entities (CSEs).

It analyses periodic SOC and case-management data to help supervisors identify:

- Entities requiring supervisory attention
- Execution gaps between reported capability and operational evidence
- Missing or unexpected evidence
- Anomalous operational behaviour
- Peer-level deviations
- Historical changes
- Cases and alerts requiring prioritized manual review

CyberLens is a **supervisory decision-support system**. It is not a SIEM, SOC, real-time monitoring platform, or centralized national cyber-monitoring system.

---

# 1. Problem Statement

Traditional SOC assessments rely heavily on manual examination of samples of alerts, investigations, escalation records, case-management information, and supporting evidence.

As the number of CSEs and operational records increases, manual assessment becomes:

- Time-consuming
- Difficult to scale
- Dependent on sampling
- Difficult to compare consistently
- Limited in its ability to identify hidden operational patterns

CyberLens addresses this problem by transforming periodic SOC/CSE records into **explainable supervisory signals** that help human examiners decide where deeper investigation is required.

---

# 2. Objectives

CyberLens is designed to:

1. Analyse structured SOC and case-management data at scale.
2. Identify entities requiring supervisory attention.
3. Prioritize alerts, investigations and cases for manual review.
4. Detect execution gaps.
5. Detect negative-space and missing-evidence conditions.
6. Identify anomalous and unusual operational behaviour.
7. Compare entities against peers.
8. Compare current performance against historical behaviour.
9. Provide evidence-backed explanations for findings.
10. Maintain traceability from findings to source records.
11. Support human-in-the-loop supervisory decisions.
12. Operate completely offline in controlled environments.

---

# 3. Core Supervisory Questions

CyberLens is designed around questions such as:

### Are reported capabilities supported by operational evidence?

Detect potential **capability–evidence contradictions**.

### Are expected activities actually occurring?

Identify execution gaps between expected operational behaviour and observed evidence.

### What evidence is missing?

Detect negative-space conditions where expected evidence is absent or unusually low.

### Is an entity behaving differently from its peers?

Use peer comparison and benchmarking to identify unusual deviations.

### Has the entity changed compared with its own history?

Use historical self-benchmarking to identify meaningful changes.

### Which entities or cases deserve attention first?

Fuse multiple supervisory signals into a prioritized review queue.

### Why was something flagged?

Provide evidence, rationale, context and traceability for every finding.

---

# 4. Key Innovations

## 4.1 SOC Operational Lifecycle Intelligence

CyberLens analyses operational activity across the SOC lifecycle:

```text
Detection
   ↓
Alert Handling
   ↓
Investigation
   ↓
Escalation
   ↓
Response / Remediation
   ↓
Closure
4.2 Expected Evidence Model
CyberLens defines what evidence should reasonably exist for a particular operational activity.
The system compares:
Expected Evidence
       ↓
Observed Evidence
       ↓
Evidence Availability
       ↓
Supervisory Signal

This supports detection of:
- Missing investigations
- Missing escalation evidence
- Missing monitoring evidence
- Unexpectedly low activity
- Monitoring blind spots
- Incomplete operational records
4.3 Supervisory Signal Fusion
Individual analytics can produce isolated findings.
CyberLens combines multiple independent signals to provide stronger supervisory context.
Lifecycle
Execution Gap
Negative Space
Expected Evidence
Peer Comparison
Historical Benchmark
Anomaly Detection
Statistical Analysis
        ↓
Supervisory Signal Fusion
        ↓
Review Priority
        ↓
Human Examination

This helps distinguish isolated deviations from patterns requiring supervisory attention.
5. Core Analytics
Execution Gap Detection
Identifies differences between:
- Reported capability
- Expected operational behaviour
- Observed operational evidence
Example:
Reported capability: Continuous monitoring

Observed evidence:
Low monitoring coverage
Reduced telemetry availability
Limited alert activity

→ Potential execution gap

Negative-Space Detection
Looks for evidence that is expected but missing or unusually low.
Examples include:
- Critical assets with limited monitoring evidence
- Missing investigation activity
- Missing escalation records
- Unexpectedly low alert categories
- Missing remediation evidence
Negative-space analysis is particularly useful because the absence of expected evidence can itself be a supervisory signal.
Anomaly & Behaviour Analytics
CyberLens uses statistical methods and machine learning to identify unusual operational behaviour.
Methods include:
- Statistical analysis
- Outlier detection
- IQR-based analysis
- MAD-based analysis
- Isolation Forest
The system does not treat an anomaly as automatic proof of a control failure.
Instead, anomalies become explainable supervisory signals requiring contextual examination.
Peer Comparison
Entities can be compared against peer entities using operational metrics such as:
- Alert volume
- Investigation activity
- Escalation behaviour
- Closure behaviour
- Monitoring coverage
- Investigation time
- Closure time
Example:
Entity Value
     ↓
Peer Median
     ↓
Deviation
     ↓
Percentile
     ↓
Supervisory Signal

Historical Self-Benchmarking
CyberLens compares an entity with its own historical behaviour.
This helps identify:
- Sudden drops in activity
- Significant changes in closure behaviour
- Changes in monitoring coverage
- Unusual investigation patterns
- Operational deterioration or improvement
Capability–Evidence Analysis
Reported capability is compared with available operational evidence.
The objective is to identify cases where:
Declared Capability
        ≠
Operational Evidence

Such cases can be prioritized for human examination.
6. Data Model
CyberLens is designed around structured periodic SOC/CSE data.
Primary datasets
Dataset	Purpose
alerts.csv	Alert metadata and alert lifecycle
cases.csv	Case-management records
investigations.csv	Investigation workflow and outcomes
escalations.csv	Escalation activity
assets.csv	Asset and criticality information
monitoring_evidence.csv	Monitoring and telemetry evidence
capabilities.csv	Declared SOC capabilities


Supporting datasets
Additional datasets include:
- Assessment periods
- CSE entities
- Expected evidence
- Historical assessments
- KPIs
- Evidence records
- Control mappings
- Scenario catalogue
- Ground truth
- Data-quality test cases
7. Prototype Dataset
The current CyberLens prototype operates on simulated assessment data representing:
- 30 CSEs
- 6 assessment periods
- Approximately 59,000 core operational records
Core dataset scale:
Dataset	Records
Alerts	23,045
Cases	6,047
Investigations	15,090
Escalations	290
Assets	2,131
Monitoring Evidence	12,437


The dataset is structured to represent periodic SOC assessment evidence rather than continuous raw telemetry.
8. Data Processing Pipeline
SOC / CSE Data
      ↓
Data Validation
      ↓
Schema Normalization
      ↓
Feature Engineering
      ↓
Supervisory Analytics
      ↓
Anomaly & Behaviour Analytics
      ↓
Evidence & Explainability
      ↓
Signal Fusion
      ↓
Review Prioritization
      ↓
Supervisor Dashboard

The pipeline supports structured CSV/JSON inputs and is designed to accommodate database exports and APIs in future deployments.
9. Supervisory Signal Model
Each finding follows a structured representation:
{
  "signal_type": "anomaly",
  "rule_id": "ANOM-001",
  "category": "Monitoring",
  "priority": "High",
  "reason": "Monitoring coverage is significantly below peer levels.",
  "evidence": [],
  "source_record_ids": [],
  "historical_context": {},
  "peer_context": {},
  "evidence_confidence": "Medium",
  "rule_model_version": "v1.0"
}

This common structure makes findings easier to:
- Explain
- Compare
- Audit
- Display
- Validate
- Trace back to evidence
10. Evidence & Explainability
CyberLens follows an evidence-first approach.
Every supervisory finding should provide, where available:
- Finding identifier
- Signal type
- Priority
- Reason
- Supporting evidence
- Source record identifiers
- Historical context
- Peer context
- Evidence confidence
- Rule/model version
Evidence Traceability
Finding
   ↓
Rule / Model
   ↓
Reason / Rationale
   ↓
Supporting Evidence
   ↓
Source Record
   ↓
Historical / Peer Context
   ↓
Rule / Model Version

This allows a supervisor to answer:
Why was this entity or record flagged?

11. Evidence Confidence
CyberLens distinguishes between the strength of available evidence.
Typical confidence levels:
- High
- Medium
- Low
Confidence can depend on factors such as:
- Evidence availability
- Supporting record count
- Source quality
- Statistical strength
- Peer comparison strength
- Historical consistency
Confidence is used as context for human review rather than as an automatic decision.
12. Review Prioritization
CyberLens converts multiple findings into a supervisory review queue.
The queue considers factors such as:
- Supervisory score
- Priority
- Signal count
- Signal types
- Evidence confidence
- Peer context
- Historical context
- Human review requirement
Example:
CSE-004
Score: 68
Priority: HIGH
Signals: 30
Human Review: REQUIRED

The purpose is not to automatically declare an entity non-compliant.
The purpose is to help the examiner decide where to look first.
13. Human-in-the-Loop Validation
CyberLens is designed to assist, not replace, human supervisory judgement.
The workflow is:
Analytics
   ↓
Finding
   ↓
Evidence Review
   ↓
Human Examiner
   ↓
Validation
   ↓
Supervisory Decision

Expert feedback can be used to improve:
- Rules
- Thresholds
- Expected evidence definitions
- Signal weighting
- Detection scenarios
- Model validation
14. Dashboard
The CyberLens dashboard provides supervisory views including:
Overview
- Assessment summary
- Finding distribution
- Priority distribution
- Entity-level signals
- Review queue
Supervisory Intelligence
- Lifecycle Intelligence
- Execution Gaps
- Expected Evidence
- Negative Space
- Capability–Evidence Analysis
Behaviour Analytics
- Anomalies
- Statistical Analysis
Context & Comparison
- Peer Comparison
- Historical Benchmarking
- Supervisory Signal Fusion
Evidence
- Evidence Explorer
- Source Records
Reporting & Audit
- Reports
- Audit Trail
Validation
- Expert Validation
15. Technology Stack
Layer	Technology
Frontend	React.js, TypeScript, Vite
UI	Material UI
Visualization	Apache ECharts
Backend	Python, FastAPI
Validation	Pydantic
Database Layer	SQLAlchemy
Data Processing	Pandas, Polars
Numerical Analysis	NumPy, SciPy
Analytics	Python Rule-Based Analytics
Machine Learning	Scikit-learn, Isolation Forest
Storage	PostgreSQL, Parquet
Testing	Pytest
Code Quality	Ruff
Deployment	Docker, Docker Compose
Version Control	Git, GitHub