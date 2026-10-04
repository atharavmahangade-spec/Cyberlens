


# CyberLens — System Architecture

## 1. Complete System Architecture

CyberLens is an offline, evidence-driven supervisory analytics platform for periodic SOC/CSE assessment. It converts structured operational evidence into explainable supervisory findings and a prioritized human-review queue.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                 NCIIPC CONTROLLED OFFLINE / AIR-GAPPED ENVIRONMENT          │
│                                                                             │
│  ┌──────────────────────┐                                                   │
│  │  PERIODIC SOC / CSE  │                                                   │
│  │        DATA          │                                                   │
│  │                      │                                                   │
│  │ Alerts • Cases       │                                                   │
│  │ Investigations       │                                                   │
│  │ Escalations • Assets │                                                   │
│  │ Monitoring           │                                                   │
│  │ Capabilities • KPIs  │                                                   │
│  │ Historical Data      │                                                   │
│  └──────────┬───────────┘                                                   │
│             │                                                               │
│             ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                 DATA VALIDATION & NORMALIZATION                      │   │
│  │ Schema Validation • Cleaning • Standardization • Feature Preparation│   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    SUPERVISORY INTELLIGENCE                         │   │
│  │                                                                      │   │
│  │ Lifecycle Intelligence     Execution Gap Detection                  │   │
│  │ Expected Evidence          Negative-Space Detection                 │   │
│  │ Peer Comparison             Historical Benchmarking                  │   │
│  │ Capability–Evidence Analysis                                      │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                  ANOMALY & BEHAVIOUR ANALYTICS                     │   │
│  │                                                                      │   │
│  │ Statistical Analysis • Outliers • IQR/MAD • Isolation Forest        │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    EVIDENCE & EXPLAINABILITY                       │   │
│  │                                                                      │   │
│  │ Rationale • Evidence • Source Records • Confidence                  │   │
│  │ Historical Context • Peer Context • Rule/Model Version               │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    SUPERVISORY SIGNAL FUSION                       │   │
│  │                                                                      │   │
│  │ Combines multiple independent signals into contextual findings      │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    REVIEW PRIORITIZATION                           │   │
│  │                                                                      │   │
│  │ Supervisory Score • Priority • Risk Context • Human Review          │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       CYBERLENS DASHBOARD                          │   │
│  │                                                                      │   │
│  │ Findings • Review Queue • Trends • Peer Comparison • Evidence       │   │
│  │ Entity Drill-down • Reports • Audit                                 │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                                 ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                  NCIIPC SUPERVISOR / HUMAN EXAMINER                │   │
│  │                                                                      │   │
│  │ Evidence Review → Expert Validation → Supervisory Decision          │   │
│  └──────────────────────────────┬───────────────────────────────────────┘   │
│                                 │                                           │
│                    ┌────────────┴─────────────┐                             │
│                    ▼                          ▼                             │
│          ┌──────────────────┐       ┌──────────────────────┐                │
│          │ REPORTING &      │       │ EXPERT VALIDATION &  │                │
│          │ AUDIT            │──────►│ CONTINUOUS           │                │
│          │                  │       │ IMPROVEMENT          │                │
│          └──────────────────┘       └──────────┬───────────┘                │
│                                               │                             │
│                                               ▼                             │
│                                   Rules / Models / Thresholds               │
│                                               │                             │
│                                               └──────────────► Analytics    │
│                                                                             │
│  Local Processing • Local Storage • Local ML • No Cloud • No SaaS          │
│  No External AI APIs • No Internet Dependency                              │
└─────────────────────────────────────────────────────────────────────────────┘

                         CYBERLENS APPLICATION
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
        ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
        │  FRONTEND   │   │   BACKEND   │   │  ANALYTICS  │
        │             │   │             │   │             │
        │ React       │   │ FastAPI     │   │ Python      │
        │ TypeScript  │◄─►│ Pydantic    │◄─►│ Pandas      │
        │ Vite        │   │ SQLAlchemy  │   │ Polars      │
        │ MUI         │   │             │   │ NumPy/SciPy │
        │ ECharts     │   │             │   │ Scikit-learn│
        └─────────────┘   └──────┬──────┘   └──────┬──────┘
                                 │                 │
                                 └────────┬────────┘
                                          ▼
                               ┌─────────────────────┐
                               │ LOCAL DATA LAYER    │
                               │                     │
                               │ PostgreSQL           │
                               │ Parquet              │
                               └─────────────────────┘

               OFFLINE / AIR-GAPPED ENVIRONMENT
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
      Frontend             Backend            Analytics
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                       Local Storage
                    PostgreSQL / Parquet
                              │
                              ▼
                       Reports / Audit