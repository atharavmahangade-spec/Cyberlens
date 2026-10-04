# CyberLens

### Supervisory Analytics Tool for SOC Assessment (SAT-SA)

**CyberLens is an offline supervisory analytics platform that helps assess SOC operations across Cyber Security Entities (CSEs) and prioritize where human examiners should look first.**

Instead of manually going through large volumes of alerts, cases and investigations, CyberLens analyses periodic SOC/CSE data and highlights **execution gaps, missing evidence, unusual behaviour, peer deviations and historical changes**.

> **CyberLens does not replace the supervisor. It helps the supervisor know where to look first and why.**

---

## ⚡ At a Glance

| | |
|---|---:|
| **Cyber Security Entities** | 30 CSEs |
| **Assessment Periods** | 6 |
| **Core Records** | ~59,000 |
| **Deployment** | Offline / Air-Gapped |
| **Processing** | Local |
| **GPU Required** | No |
| **Decision Maker** | Human Examiner |

---

## 🎯 Problem

SOC assessments involve reviewing operational evidence such as:

- Security alerts
- Cases
- Investigations
- Escalations
- Monitoring evidence
- Asset information
- Capability declarations
- Historical assessment data

As the amount of data grows, manually finding the most important cases becomes difficult.

CyberLens helps answer four simple questions:

> **What looks unusual? What evidence is missing? Where does reported capability differ from actual evidence? Which entity should we review first?**

---

# 💡 What CyberLens Does

| Capability | What it means |
|---|---|
| **Execution Gap Detection** | Finds differences between reported capability and operational evidence |
| **Negative-Space Detection** | Finds evidence that should exist but is missing or unusually low |
| **Expected Evidence** | Checks whether expected operational evidence is actually present |
| **Lifecycle Intelligence** | Analyses the flow from detection to investigation, escalation and closure |
| **Anomaly Detection** | Finds unusual operational behaviour |
| **Statistical Analysis** | Identifies significant outliers and unusual patterns |
| **Peer Comparison** | Compares a CSE with similar entities |
| **Historical Benchmarking** | Compares a CSE with its own previous assessment periods |
| **Capability–Evidence Analysis** | Checks whether declared capabilities are supported by evidence |
| **Signal Fusion** | Combines multiple signals to identify stronger supervisory concerns |
| **Review Prioritization** | Ranks entities and findings for human review |

---

# ⭐ Three Core Ideas

### 1. SOC Operational Lifecycle Intelligence

CyberLens looks at how activity moves through the SOC lifecycle:

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
2. Expected Evidence Model
The system asks:
What evidence should exist?
          ↓
What evidence was actually observed?
          ↓
Is something missing or unusually low?

3. Supervisory Signal Fusion
A single unusual metric does not automatically mean a problem.
CyberLens combines signals from different analyses:
Execution Gap ────────┐
Negative Space ───────┤
Expected Evidence ────┤
Peer Comparison ──────┤
Historical Change ─────┤
Anomaly Detection ────┤
Statistical Analysis ─┤
                      ↓
              Signal Fusion
                      ↓
              Review Priority
                      ↓
              Human Examiner
              📊 Prototype Dataset
The current prototype uses structured assessment data representing 30 CSEs across 6 assessment periods.
Core datasets
Dataset	Records	Used For
alerts.csv	23,045	Alert activity and lifecycle
cases.csv	6,047	Case management
investigations.csv	15,090	Investigation workflow
escalations.csv	290	Escalation activity
assets.csv	2,131	Asset and criticality context
monitoring_evidence.csv	12,437	Monitoring and telemetry evidence
capabilities.csv	—	Declared capabilities
🔎 Evidence & Explainability
CyberLens follows an evidence-first approach.
A finding can contain:
Information	Purpose
Finding ID	Unique reference
Signal Type	Type of supervisory finding
Priority	High / Medium / Low
Reason	Why it was flagged
Evidence	Supporting analytical evidence
Source Records	Links to underlying records
Historical Context	Previous behaviour
Peer Context	Comparison with peers
Evidence Confidence	Strength of available evidence
Rule/Model Version	Reproducibility and auditability
🎯 Review Prioritization
CyberLens converts multiple findings into a ranked review queue.
The queue considers:
- Supervisory score
- Priority
- Number of signals
- Signal types
- Evidence confidence
- Historical context
- Peer context
- Human review requirement

🖥️ Dashboard
The frontend is organized around the supervisory workflow.
Section	Purpose
Overview	Assessment summary and key findings
Assessments	Assessment-level information
Review Queue	Prioritized entities and findings
Lifecycle Intelligence	Operational lifecycle analysis
Execution Gaps	Reported vs observed capability
Expected Evidence	Expected vs observed evidence
Negative Space	Missing or low expected evidence
Capability–Evidence	Capability/evidence analysis
Anomalies	Unusual operational behaviour
Statistical Analysis	Statistical findings
Peer Comparison	CSE-to-peer comparison
Historical Benchmarking	CSE-to-history comparison
Signal Fusion	Combined supervisory signals
Evidence Explorer	Evidence investigation
Source Records	Underlying records
Reports & Audit	Reporting and traceability
Expert Validation	Human validation