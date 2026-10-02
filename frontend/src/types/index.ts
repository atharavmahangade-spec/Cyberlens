export type Priority = 'High' | 'Medium' | 'Low';
export type Confidence = 'High' | 'Medium' | 'Low';
export type SignalType =
  | 'execution_gap' | 'negative_space' | 'anomaly' | 'peer_deviation'
  | 'lifecycle' | 'monitoring' | 'contradiction' | 'statistical';
export type ReviewStatus = 'Pending review' | 'Under examination' | 'Deferred' | 'Closed by examiner';

export interface Entity { entity_id: string; name: string; sector: string }
export interface ContextBlock { summary: string; metrics?: { label: string; value: string }[] }
export interface EvidenceItem { evidence_id: string; label: string; detail: string; source_record_ids: string[] }

/** PRD §27 Standard Supervisory Signal Schema + display fields. */
export interface Finding {
  finding_id: string;
  entity_id: string;
  entity_name: string;
  title: string;
  area: string;
  signal_type: SignalType;
  rule_id: string;
  rule_model_name: string;
  category: string;
  priority: Priority;
  reason: string;
  narrative: string;
  evidence: EvidenceItem[];
  source_record_ids: string[];
  historical_context: ContextBlock;
  peer_context: ContextBlock;
  lifecycle_context: ContextBlock | null;
  evidence_confidence: Confidence;
  evidence_availability: 'Complete' | 'Partial' | 'Limited';
  rule_model_version: string;
  asset_criticality: 'Critical' | 'High' | 'Medium' | 'Low';
  fusion_score: number;
  status: ReviewStatus;
  created_at: string;
}
export interface FindingFilter { types?: SignalType[]; entity_id?: string }

export interface OverviewData {
  period: string;
  entities_assessed: number;
  entities_requiring_review: number;
  total_findings: number;
  priority_distribution: Record<Priority, number>;
  findings_by_type: { signal_type: SignalType; count: number }[];
  entity_summaries: { entity_id: string; name: string; fused_score: number; findings: number; top_area: string; requires_review: boolean }[];
  review_workload: { records_in_scope: number; records_prioritized: number; estimated_sampling_reduction_pct: number };
}
export interface AssessmentRun {
  assessment_id: string; period: string; started_at: string; completed_at: string; entities: number;
  findings: number; rule_model_version: string; data_completeness_pct: number; status: 'Complete' | 'In examiner review';
}
export interface LifecycleSummary {
  entity_id: string;
  stages: { stage: string; count: number }[];
  indicators: { label: string; value: string }[];
  breakdowns: { description: string; finding_id?: string }[];
}
export interface ExpectedEvidenceModel {
  version: string;
  definitions: { process_type: string; expected_stages: string[]; expected_evidence: string[] }[];
  comparison: { entity_id: string; process_type: string; evidence_category: string; expected: number; observed: number; status: 'Complete' | 'Partial' | 'Missing'; finding_id?: string }[];
}
export interface Contradiction {
  id: string; entity_id: string; claim: string; claim_source: string; observed: string;
  confidence: Confidence; finding_id: string;
}
export interface AnomalyResult {
  model: string; model_version: string; threshold: number;
  points: { entity_id: string; entity_name: string; score: number; features: { name: string; z: number }[]; finding_id?: string }[];
}
export interface StatRow { entity_id: string; metric: string; value: number; median: number; iqr_low: number; iqr_high: number; z_score: number; percentile: number; flagged: boolean }
export interface PeerRow { entity_id: string; dimension: string; unit: string; value: number; peer_median: number; peer_p25: number; peer_p75: number; percentile: number }
export interface HistSeries { entity_id: string; metric: string; unit: string; periods: string[]; values: number[]; baseline: number; band_low: number; band_high: number }
export interface FusionItem {
  finding_id: string; entity_name: string; area: string; fused_score: number; converging_signals: number;
  contributions: { signal: string; weight: number }[]; narrative: string;
}
export interface SourceRecord {
  record_id: string; record_type: 'Alert' | 'Investigation' | 'Escalation' | 'Case' | 'Asset' | 'Monitoring' | 'Report';
  entity_id: string; timestamp: string; fields: Record<string, string | number | null>; linked_finding_ids: string[];
}
export interface EvidenceRow extends EvidenceItem { finding_id: string; entity_id: string; entity_name: string; signal_type: SignalType; confidence: Confidence }
export interface ReportItem {
  report_id: string;
  kind: 'Supervisory Assessment' | 'Finding Report' | 'Evidence Report' | 'Prioritized Review List' | 'Historical Finding Records' | 'Validation Metrics';
  title: string; generated_at: string; rule_model_version: string; item_count: number; formats: string[];
}
export interface AuditEvent { event_id: string; timestamp: string; actor: string; action: string; object: string; rule_model_version: string; detail: string }
export interface ValidationData {
  metrics: { label: string; value: string; note?: string }[];
  trend: { periods: string[]; precision: number[]; recall: number[] };
  comparisons: { finding_id: string; entity_name: string; cyberlens_priority: Priority; expert_assessment: 'Confirmed' | 'Partially confirmed' | 'Not confirmed'; agreement: boolean; note: string }[];
  missed_by_cyberlens: { description: string; entity_name: string }[];
}
export interface ReviewDecision { finding_id: string; decision: ReviewStatus; note: string }
export interface ExpertFeedback { finding_id: string; target: 'rule' | 'threshold' | 'feature' | 'model'; comment: string }
