// All mock data lives here. Replace with FastAPI responses via src/services/api.ts.
import type * as T from '../types';

export const entities: T.Entity[] = [
  { entity_id: 'CSE-07', name: 'CSE-07 Western Grid', sector: 'Power' },
  { entity_id: 'CSE-12', name: 'CSE-12 Port Telecom', sector: 'Telecom' },
  { entity_id: 'CSE-03', name: 'CSE-03 Metro Power', sector: 'Power' },
  { entity_id: 'CSE-15', name: 'CSE-15 Rail Signals', sector: 'Transport' },
  { entity_id: 'CSE-21', name: 'CSE-21 Aviation Net', sector: 'Transport' },
  { entity_id: 'CSE-09', name: 'CSE-09 Water Board', sector: 'Utilities' },
];
const en = (id: string) => entities.find((e) => e.entity_id === id)!.name;
const ctx = (summary: string, metrics?: { label: string; value: string }[]): T.ContextBlock => ({ summary, metrics });
type Seed = Omit<T.Finding, 'entity_name' | 'status' | 'created_at' | 'source_record_ids' | 'rule_model_version'> & { v?: string };
const mk = (s: Seed): T.Finding => {
  const { v, ...rest } = s;
  return { ...rest, entity_name: en(s.entity_id), status: 'Pending review', created_at: '2026-09-28T10:14:00Z',
    rule_model_version: v ?? '1.3.0', source_record_ids: [...new Set(s.evidence.flatMap((e) => e.source_record_ids))] };
};

export const findings: T.Finding[] = [
  mk({ finding_id: 'F-1042', entity_id: 'CSE-07', title: 'High-severity alerts closed without escalation', area: 'Escalation', signal_type: 'negative_space',
    rule_id: 'NS-ESC-004', rule_model_name: 'Missing Escalation (Expected Evidence)', category: 'Missing escalation', priority: 'High',
    reason: '41 High-severity alerts on Tier-1 assets were closed with no escalation record, although the Expected Evidence Model requires escalation evidence for severity ≥ High.',
    narrative: 'Negative-space, lifecycle and historical signals converge on escalation handling for critical assets. Absence of records may also indicate an upstream data gap — examiner to confirm.',
    evidence: [
      { evidence_id: 'EV-1042-1', label: 'Alert closed, escalation stage absent', detail: 'Alert → Acknowledgement → Closure; no Escalation record linked.', source_record_ids: ['ALR-88213', 'ALR-88240'] },
      { evidence_id: 'EV-1042-2', label: 'No case linked to alert', detail: 'Case lookup returned 0 rows for 33 of 41 alerts.', source_record_ids: ['ALR-88213'] },
      { evidence_id: 'EV-1042-3', label: 'Critical asset involved', detail: 'Asset criticality: Critical; monitoring active.', source_record_ids: ['AST-A0412'] }],
    historical_context: ctx('Escalation rate collapsed versus own six-period baseline.', [{ label: 'Current', value: '4%' }, { label: 'Baseline', value: '31%' }]),
    peer_context: ctx('Entity sits at the 4th percentile among comparable power-sector CSEs.', [{ label: 'Peer median', value: '28%' }]),
    lifecycle_context: ctx('Stage "Escalation" missing for 2,840 closures.', [{ label: 'Alerts reaching Escalation', value: '31%' }]),
    evidence_confidence: 'High', evidence_availability: 'Complete', asset_criticality: 'Critical', fusion_score: 92 }),
  mk({ finding_id: 'F-1038', entity_id: 'CSE-12', title: 'Alerts closed within seconds without investigation', area: 'Closure', signal_type: 'execution_gap',
    rule_id: 'EG-CLS-011', rule_model_name: 'Closure without Investigation', category: 'Closure/process', priority: 'High',
    reason: '112 alerts were closed in under 60 seconds with no investigation record, inconsistent with the documented triage process.',
    narrative: 'Compressed closure times coincide with a drop in investigation volume and a documented KPI claim of full triage.',
    evidence: [
      { evidence_id: 'EV-1038-1', label: 'Sub-minute closures', detail: '112 alerts closed in < 60 s; investigation = NULL.', source_record_ids: ['ALR-70114', 'ALR-70115'] },
      { evidence_id: 'EV-1038-2', label: 'KPI report claim', detail: 'Report states 100% of alerts triaged within 30 minutes.', source_record_ids: ['RPT-KPI-Q3'] }],
    historical_context: ctx('Median time-to-close fell sharply.', [{ label: 'Current', value: '0.4 h' }, { label: 'Baseline', value: '3.2 h' }]),
    peer_context: ctx('Peer median time-to-close is 2.7 h.'), lifecycle_context: ctx('Investigation stage reached by 33% of alerts.'),
    evidence_confidence: 'High', evidence_availability: 'Complete', asset_criticality: 'High', fusion_score: 86 }),
  mk({ finding_id: 'F-1027', entity_id: 'CSE-07', title: 'Tier-1 assets without telemetry', area: 'Monitoring coverage', signal_type: 'monitoring',
    rule_id: 'MON-COV-003', rule_model_name: 'Telemetry Gap', category: 'Monitoring coverage', priority: 'High',
    reason: '18 Tier-1 assets show no telemetry for 9 consecutive days.', narrative: 'Coverage loss on critical assets weakens the evidence base for other findings for this entity.',
    evidence: [{ evidence_id: 'EV-1027-1', label: 'Telemetry silence', detail: 'Last event seen 2026-09-12 for 18 assets.', source_record_ids: ['MON-0912', 'AST-A0412'] }],
    historical_context: ctx('Coverage declined.', [{ label: 'Current', value: '81%' }, { label: 'Baseline', value: '97%' }]),
    peer_context: ctx('Peer median coverage is 94%.'), lifecycle_context: null,
    evidence_confidence: 'High', evidence_availability: 'Complete', asset_criticality: 'Critical', fusion_score: 81 }),
  mk({ finding_id: 'F-1031', entity_id: 'CSE-03', title: 'Unusual combination of operational behaviours', area: 'Behaviour', signal_type: 'anomaly',
    rule_id: 'ML-IF-002', rule_model_name: 'Isolation Forest', category: 'Behaviour anomaly', priority: 'Medium', v: '0.9.1',
    reason: 'Anomaly score 0.71 (threshold 0.62): high alert volume with low investigation rate and compressed closure time.',
    narrative: 'Statistical outlier only; not rule-confirmed. Useful as a prompt for sampling, not as a conclusion.',
    evidence: [{ evidence_id: 'EV-1031-1', label: 'Feature deviations', detail: 'alert_vol z=2.8, investigation_rate z=−2.1, closure_time z=−1.9.', source_record_ids: ['ALR-91002'] }],
    historical_context: ctx('Alert volume well above own baseline.', [{ label: 'Change', value: '+62%' }]),
    peer_context: ctx('Profile differs from nearest 5 peers.'), lifecycle_context: null,
    evidence_confidence: 'Medium', evidence_availability: 'Partial', asset_criticality: 'Medium', fusion_score: 64 }),
  mk({ finding_id: 'F-1019', entity_id: 'CSE-15', title: 'Confirmed incidents closed without remediation', area: 'Remediation', signal_type: 'lifecycle',
    rule_id: 'LC-SEQ-006', rule_model_name: 'Lifecycle Sequence Check', category: 'Missing lifecycle stage', priority: 'Medium',
    reason: '27% of confirmed cases reach Closure with no Remediation stage.', narrative: 'Lifecycle gap is isolated to remediation; escalation and case stages are intact.',
    evidence: [{ evidence_id: 'EV-1019-1', label: 'Closure without remediation', detail: '27 cases, outcome = Confirmed, remediation = NULL.', source_record_ids: ['CASE-5521', 'CASE-5530'] }],
    historical_context: ctx('Rate rose from 6%.', [{ label: 'Current', value: '27%' }, { label: 'Baseline', value: '6%' }]),
    peer_context: ctx('Peer median 9%.'), lifecycle_context: ctx('Remediation stage reached by 22% of cases.'),
    evidence_confidence: 'Medium', evidence_availability: 'Partial', asset_criticality: 'High', fusion_score: 61 }),
  mk({ finding_id: 'F-1011', entity_id: 'CSE-12', title: '24×7 monitoring claim vs overnight activity', area: 'Capability vs evidence', signal_type: 'contradiction',
    rule_id: 'CE-CON-001', rule_model_name: 'Capability–Evidence Contradiction', category: 'Capability vs evidence', priority: 'Medium', v: '1.2.0',
    reason: 'Report claims 24×7 monitoring, but overnight (00:00–06:00) alert activity is near zero on 22 of 30 nights.',
    narrative: 'Possible reporting inconsistency or genuinely quiet overnight traffic; examiner review required.',
    evidence: [{ evidence_id: 'EV-1011-1', label: 'Overnight activity', detail: '14 alerts observed vs ≈410 expected for the window.', source_record_ids: ['RPT-KPI-Q3', 'ALR-70114'] }],
    historical_context: ctx('Overnight volume down 70% vs baseline.'), peer_context: ctx('Peers retain ≈18% of daily volume overnight.'), lifecycle_context: null,
    evidence_confidence: 'Medium', evidence_availability: 'Partial', asset_criticality: 'Medium', fusion_score: 58 }),
  mk({ finding_id: 'F-0988', entity_id: 'CSE-21', title: 'Expected investigations absent for severity ≥ Medium', area: 'Investigation', signal_type: 'negative_space',
    rule_id: 'NS-INV-002', rule_model_name: 'Missing Investigation (Expected Evidence)', category: 'Missing investigation', priority: 'Medium',
    reason: 'Investigation records exist for only 14% of Medium+ alerts; expected ≥ 60%.', narrative: 'Data completeness for this entity is limited; interpret conservatively.',
    evidence: [{ evidence_id: 'EV-0988-1', label: 'Investigation coverage', detail: '14% of Medium+ alerts have an investigation record.', source_record_ids: ['ALR-60001'] }],
    historical_context: ctx('Previously 55%.'), peer_context: ctx('Peer median 58%.'), lifecycle_context: ctx('Investigation stage largely absent.'),
    evidence_confidence: 'Low', evidence_availability: 'Limited', asset_criticality: 'Medium', fusion_score: 52 }),
  mk({ finding_id: 'F-0969', entity_id: 'CSE-15', title: 'Escalation delay beyond documented SLA', area: 'Escalation', signal_type: 'execution_gap',
    rule_id: 'EG-ESC-008', rule_model_name: 'Escalation SLA Deviation', category: 'Escalation', priority: 'Medium',
    reason: '38 escalations occurred more than 4 hours after acknowledgement against a 1-hour documented SLA.', narrative: 'Delay pattern is concentrated on weekends.',
    evidence: [{ evidence_id: 'EV-0969-1', label: 'Late escalations', detail: '38 records exceed SLA by > 3 h.', source_record_ids: ['ESC-2201'] }],
    historical_context: ctx('Delay increased.', [{ label: 'Current', value: '4.3 h' }, { label: 'Baseline', value: '1.1 h' }]), peer_context: ctx('Peer median 1.4 h.'), lifecycle_context: ctx('Acknowledgement → Escalation transition slow.'),
    evidence_confidence: 'Medium', evidence_availability: 'Complete', asset_criticality: 'High', fusion_score: 49 }),
  mk({ finding_id: 'F-0997', entity_id: 'CSE-03', title: 'Investigation rate below peer range', area: 'Investigation', signal_type: 'peer_deviation',
    rule_id: 'PR-INV-002', rule_model_name: 'Peer IQR Deviation', category: 'Investigation', priority: 'Low',
    reason: 'Investigation rate of 29% is below the peer lower fence of 31%.', narrative: 'Marginal peer deviation; within historical range for this entity.',
    evidence: [{ evidence_id: 'EV-0997-1', label: 'Peer comparison', detail: 'Peer IQR 34–52%; entity 29%.', source_record_ids: ['ALR-91002'] }],
    historical_context: ctx('Within normal historical range.'), peer_context: ctx('Peer IQR 34–52%.', [{ label: 'Entity', value: '29%' }]), lifecycle_context: null,
    evidence_confidence: 'Medium', evidence_availability: 'Complete', asset_criticality: 'Low', fusion_score: 33 }),
  mk({ finding_id: 'F-0976', entity_id: 'CSE-09', title: 'Closure duration statistical outlier', area: 'Closure', signal_type: 'statistical',
    rule_id: 'ST-IQR-001', rule_model_name: 'IQR / Z-score', category: 'Closure/process', priority: 'Low',
    reason: 'Median closure duration z-score of 2.4 versus own history.', narrative: 'Single-metric outlier without corroborating signals.',
    evidence: [{ evidence_id: 'EV-0976-1', label: 'Closure duration', detail: 'Median 9.8 h vs baseline 4.1 h.', source_record_ids: ['CASE-5530'] }],
    historical_context: ctx('Above own IQR upper fence.'), peer_context: ctx('Peer median 5.0 h.'), lifecycle_context: null,
    evidence_confidence: 'Low', evidence_availability: 'Partial', asset_criticality: 'Low', fusion_score: 27 }),
];

export const overview: T.OverviewData = {
  period: '2026-Q3', entities_assessed: 24, entities_requiring_review: 6, total_findings: 138,
  priority_distribution: { High: 19, Medium: 57, Low: 62 },
  findings_by_type: [
    { signal_type: 'execution_gap', count: 31 }, { signal_type: 'negative_space', count: 27 }, { signal_type: 'anomaly', count: 18 },
    { signal_type: 'peer_deviation', count: 22 }, { signal_type: 'lifecycle', count: 21 }, { signal_type: 'monitoring', count: 14 }, { signal_type: 'contradiction', count: 5 }],
  entity_summaries: [
    { entity_id: 'CSE-07', name: en('CSE-07'), fused_score: 92, findings: 2, top_area: 'Escalation', requires_review: true },
    { entity_id: 'CSE-12', name: en('CSE-12'), fused_score: 86, findings: 2, top_area: 'Closure', requires_review: true },
    { entity_id: 'CSE-03', name: en('CSE-03'), fused_score: 64, findings: 2, top_area: 'Behaviour', requires_review: true },
    { entity_id: 'CSE-15', name: en('CSE-15'), fused_score: 61, findings: 2, top_area: 'Remediation', requires_review: true },
    { entity_id: 'CSE-21', name: en('CSE-21'), fused_score: 52, findings: 1, top_area: 'Investigation', requires_review: true },
    { entity_id: 'CSE-09', name: en('CSE-09'), fused_score: 27, findings: 1, top_area: 'Closure', requires_review: false }],
  review_workload: { records_in_scope: 182400, records_prioritized: 1930, estimated_sampling_reduction_pct: 64 },
};
export const assessments: T.AssessmentRun[] = [
  { assessment_id: 'ASM-2026-Q3', period: '2026-Q3', started_at: '2026-09-27T20:00:00Z', completed_at: '2026-09-28T01:42:00Z', entities: 24, findings: 138, rule_model_version: '1.3.0 / IF 0.9.1', data_completeness_pct: 94, status: 'In examiner review' },
  { assessment_id: 'ASM-2026-Q2', period: '2026-Q2', started_at: '2026-06-28T20:00:00Z', completed_at: '2026-06-29T01:10:00Z', entities: 23, findings: 121, rule_model_version: '1.2.0 / IF 0.9.0', data_completeness_pct: 96, status: 'Complete' },
  { assessment_id: 'ASM-2026-Q1', period: '2026-Q1', started_at: '2026-03-28T20:00:00Z', completed_at: '2026-03-29T00:58:00Z', entities: 22, findings: 109, rule_model_version: '1.1.0 / IF 0.9.0', data_completeness_pct: 91, status: 'Complete' },
];
const STG = ['Alert', 'Acknowledged', 'Investigated', 'Escalated', 'Case opened', 'Remediated', 'Closed'];
const lc = (id: string, c: number[], indicators: [string, string][], b: [string, string?][]): T.LifecycleSummary => ({
  entity_id: id, stages: STG.map((stage, i) => ({ stage, count: c[i] })), indicators: indicators.map(([label, value]) => ({ label, value })),
  breakdowns: b.map(([description, finding_id]) => ({ description, finding_id })) });
export const lifecycles: T.LifecycleSummary[] = [
  lc('CSE-07', [4210, 4190, 3380, 1310, 1180, 960, 4150], [['Median alert→ack', '6 min'], ['Median alert→closure', '2.1 h'], ['Complete sequences', '28%']], [['Closures (4,150) exceed escalations by 2,840; 41 High-severity Tier-1 alerts have no escalation.', 'F-1042']]),
  lc('CSE-12', [3120, 3090, 1020, 140, 180, 120, 3100], [['Median alert→ack', '4 min'], ['Median alert→closure', '0.4 h'], ['Complete sequences', '4%']], [['3,100 closures vs 1,020 investigations: 2,080 closures lack an investigation stage.', 'F-1038']]),
  lc('CSE-15', [2640, 2610, 2210, 720, 690, 580, 2600], [['Median alert→ack', '9 min'], ['Median alert→closure', '5.4 h'], ['Complete sequences', '22%']], [['27% of confirmed cases closed without remediation.', 'F-1019']]),
];
export const expectedEvidence: T.ExpectedEvidenceModel = {
  version: '1.3.0',
  definitions: [
    { process_type: 'High-severity alert', expected_stages: ['Acknowledgement', 'Investigation', 'Escalation', 'Case', 'Closure'], expected_evidence: ['Ack timestamp', 'Investigation record', 'Escalation record', 'Case link', 'Closure disposition'] },
    { process_type: 'Confirmed incident', expected_stages: ['Investigation', 'Escalation', 'Case', 'Remediation', 'Closure'], expected_evidence: ['Investigation outcome', 'Escalation outcome', 'Remediation record', 'Closure evidence'] },
    { process_type: 'Critical asset monitoring', expected_stages: ['Telemetry', 'Coverage'], expected_evidence: ['Telemetry availability', 'Evidence timestamps', 'Asset-monitoring link'] }],
  comparison: [
    { entity_id: 'CSE-07', process_type: 'High-severity alert', evidence_category: 'Escalation record', expected: 1310, observed: 410, status: 'Partial', finding_id: 'F-1042' },
    { entity_id: 'CSE-07', process_type: 'High-severity alert', evidence_category: 'Case link', expected: 1310, observed: 1180, status: 'Partial' },
    { entity_id: 'CSE-07', process_type: 'High-severity alert', evidence_category: 'Investigation record', expected: 3380, observed: 3380, status: 'Complete' },
    { entity_id: 'CSE-07', process_type: 'Critical asset monitoring', evidence_category: 'Telemetry availability', expected: 120, observed: 102, status: 'Partial', finding_id: 'F-1027' },
    { entity_id: 'CSE-12', process_type: 'High-severity alert', evidence_category: 'Investigation record', expected: 3090, observed: 1020, status: 'Partial', finding_id: 'F-1038' },
    { entity_id: 'CSE-12', process_type: 'High-severity alert', evidence_category: 'Escalation record', expected: 900, observed: 140, status: 'Partial' },
    { entity_id: 'CSE-15', process_type: 'Confirmed incident', evidence_category: 'Remediation record', expected: 790, observed: 580, status: 'Partial', finding_id: 'F-1019' },
    { entity_id: 'CSE-21', process_type: 'High-severity alert', evidence_category: 'Investigation record', expected: 600, observed: 84, status: 'Missing', finding_id: 'F-0988' }],
};
export const contradictions: T.Contradiction[] = [
  { id: 'CX-01', entity_id: 'CSE-12', claim: '24×7 monitoring and triage', claim_source: 'SOC Report Q3 §2.1', observed: 'Overnight alert activity near zero on 22 of 30 nights', confidence: 'Medium', finding_id: 'F-1011' },
  { id: 'CX-02', entity_id: 'CSE-12', claim: '100% of alerts triaged within 30 minutes', claim_source: 'KPI Report Q3 §4.2', observed: '112 alerts closed < 60 s with no investigation record', confidence: 'High', finding_id: 'F-1038' },
  { id: 'CX-03', entity_id: 'CSE-07', claim: 'All Tier-1 assets under continuous monitoring', claim_source: 'Policy mapping CTL-14', observed: '18 Tier-1 assets silent for 9 days', confidence: 'High', finding_id: 'F-1027' }];
export const anomalies: T.AnomalyResult = {
  model: 'Isolation Forest', model_version: '0.9.1', threshold: 0.62,
  points: [
    { entity_id: 'CSE-03', entity_name: en('CSE-03'), score: 0.71, features: [{ name: 'Alert volume', z: 2.8 }, { name: 'Investigation rate', z: -2.1 }, { name: 'Closure time', z: -1.9 }], finding_id: 'F-1031' },
    { entity_id: 'CSE-12', entity_name: en('CSE-12'), score: 0.68, features: [{ name: 'Alert volume', z: -0.4 }, { name: 'Investigation rate', z: -2.6 }, { name: 'Closure time', z: -2.9 }] },
    { entity_id: 'CSE-07', entity_name: en('CSE-07'), score: 0.64, features: [{ name: 'Alert volume', z: 0.3 }, { name: 'Escalation rate', z: -2.7 }, { name: 'Coverage', z: -2.0 }] },
    { entity_id: 'CSE-15', entity_name: en('CSE-15'), score: 0.55, features: [{ name: 'Alert volume', z: 0.5 }, { name: 'Remediation rate', z: -1.7 }, { name: 'Closure time', z: 1.2 }] },
    { entity_id: 'CSE-21', entity_name: en('CSE-21'), score: 0.49, features: [{ name: 'Alert volume', z: -1.2 }, { name: 'Investigation rate', z: -1.8 }, { name: 'Closure time', z: 0.4 }] },
    { entity_id: 'CSE-09', entity_name: en('CSE-09'), score: 0.37, features: [{ name: 'Closure time', z: 2.4 }, { name: 'Alert volume', z: 0.1 }, { name: 'Escalation rate', z: 0.2 }] }],
};
const st = (e: string, rows: [string, number, number, number, number, number, number, boolean][]): T.StatRow[] =>
  rows.map(([metric, value, median, iqr_low, iqr_high, z_score, percentile, flagged]) => ({ entity_id: e, metric, value, median, iqr_low, iqr_high, z_score, percentile, flagged }));
export const statistics: T.StatRow[] = [
  ...st('CSE-07', [['Escalation rate (%)', 4, 28, 19, 37, -3.1, 4, true], ['Investigation rate (%)', 61, 58, 44, 70, 0.3, 58, false], ['Monitoring coverage (%)', 81, 94, 90, 98, -2.2, 9, true], ['Alerts per day', 412, 380, 300, 460, 0.4, 62, false]]),
  ...st('CSE-12', [['Escalation rate (%)', 5, 28, 19, 37, -2.9, 6, true], ['Investigation rate (%)', 33, 58, 44, 70, -2.4, 7, true], ['Time-to-close (h)', 0.4, 2.7, 1.5, 4.1, -2.0, 5, true], ['Alerts per day', 310, 380, 300, 460, -0.6, 35, false]]),
  ...st('CSE-03', [['Escalation rate (%)', 19, 28, 19, 37, -0.8, 25, false], ['Investigation rate (%)', 29, 58, 34, 52, -1.7, 12, true], ['Alerts per day', 610, 380, 300, 460, 2.8, 97, true]]),
];
const pr = (e: string, rows: [string, string, number, number, number, number, number][]): T.PeerRow[] =>
  rows.map(([dimension, unit, value, peer_median, peer_p25, peer_p75, percentile]) => ({ entity_id: e, dimension, unit, value, peer_median, peer_p25, peer_p75, percentile }));
export const peers: T.PeerRow[] = [
  ...pr('CSE-07', [['Escalation rate', '%', 4, 28, 19, 37, 4], ['Investigation rate', '%', 61, 58, 44, 70, 58], ['Closure ≤ 24 h', '%', 88, 84, 72, 93, 66], ['Monitoring coverage', '%', 81, 94, 90, 98, 9], ['Remediation rate', '%', 38, 41, 30, 52, 44]]),
  ...pr('CSE-12', [['Escalation rate', '%', 5, 28, 19, 37, 6], ['Investigation rate', '%', 33, 58, 44, 70, 7], ['Closure ≤ 24 h', '%', 99, 84, 72, 93, 99], ['Monitoring coverage', '%', 92, 94, 90, 98, 40], ['Remediation rate', '%', 35, 41, 30, 52, 36]]),
  ...pr('CSE-03', [['Escalation rate', '%', 19, 28, 19, 37, 25], ['Investigation rate', '%', 29, 58, 34, 52, 12], ['Closure ≤ 24 h', '%', 72, 84, 72, 93, 28], ['Monitoring coverage', '%', 90, 94, 90, 98, 25], ['Remediation rate', '%', 30, 41, 30, 52, 20]])];
const P = ['Q2-25', 'Q3-25', 'Q4-25', 'Q1-26', 'Q2-26', 'Q3-26'];
const hs = (e: string, metric: string, unit: string, values: number[], baseline: number, lo: number, hi: number): T.HistSeries => ({ entity_id: e, metric, unit, periods: P, values, baseline, band_low: lo, band_high: hi });
export const history: T.HistSeries[] = [
  hs('CSE-07', 'Escalation rate', '%', [30, 32, 29, 33, 28, 4], 31, 25, 37), hs('CSE-07', 'Monitoring coverage', '%', [97, 98, 96, 97, 95, 81], 97, 94, 99),
  hs('CSE-12', 'Time-to-close', 'h', [3.1, 3.4, 3.0, 3.3, 3.2, 0.4], 3.2, 2.5, 4.0), hs('CSE-12', 'Investigation rate', '%', [62, 60, 64, 61, 59, 33], 61, 54, 68),
  hs('CSE-03', 'Alerts per day', '', [370, 385, 360, 395, 380, 610], 378, 330, 430), hs('CSE-03', 'Investigation rate', '%', [48, 50, 47, 49, 46, 29], 48, 42, 54)];
const FW: [string, number][][] = [
  [['Negative space', 24], ['Lifecycle', 18], ['Historical deviation', 17], ['Peer deviation', 12], ['Asset criticality', 12], ['Evidence strength', 9]],
  [['Execution gap', 22], ['Lifecycle', 16], ['Historical deviation', 16], ['Contradiction', 12], ['Asset criticality', 10], ['Evidence strength', 10]],
  [['Monitoring', 24], ['Historical deviation', 18], ['Asset criticality', 15], ['Peer deviation', 14], ['Evidence strength', 10]],
  [['Anomaly', 20], ['Statistical', 14], ['Historical deviation', 12], ['Peer deviation', 10], ['Evidence strength', 8]],
  [['Lifecycle', 18], ['Execution gap', 14], ['Historical deviation', 13], ['Asset criticality', 10], ['Evidence strength', 6]],
  [['Contradiction', 16], ['Historical deviation', 14], ['Peer deviation', 12], ['Evidence strength', 8], ['Anomaly', 8]]];
export const fusion: T.FusionItem[] = findings.slice().sort((a, b) => b.fusion_score - a.fusion_score).slice(0, 6).map((f, i) => ({
  finding_id: f.finding_id, entity_name: f.entity_name, area: f.area, fused_score: f.fusion_score, converging_signals: FW[i].length,
  contributions: FW[i].map(([signal, weight]) => ({ signal, weight })), narrative: f.narrative }));
export const sourceRecords: T.SourceRecord[] = [
  { record_id: 'ALR-88213', record_type: 'Alert', entity_id: 'CSE-07', timestamp: '2026-09-14T09:14:00Z', fields: { severity: 'High', asset_id: 'A-0412', acknowledged: '09:14', closed: '09:52', disposition: 'Closed – no action', escalation_status: null, case_id: null }, linked_finding_ids: ['F-1042'] },
  { record_id: 'ALR-88240', record_type: 'Alert', entity_id: 'CSE-07', timestamp: '2026-09-15T13:02:00Z', fields: { severity: 'High', asset_id: 'A-0415', acknowledged: '13:09', closed: '13:41', escalation_status: null }, linked_finding_ids: ['F-1042'] },
  { record_id: 'AST-A0412', record_type: 'Asset', entity_id: 'CSE-07', timestamp: '2026-09-01T00:00:00Z', fields: { asset_id: 'A-0412', criticality: 'Critical', system_type: 'SCADA gateway', monitoring_status: 'Active' }, linked_finding_ids: ['F-1042', 'F-1027'] },
  { record_id: 'MON-0912', record_type: 'Monitoring', entity_id: 'CSE-07', timestamp: '2026-09-12T23:59:00Z', fields: { assets_affected: 18, telemetry_last_seen: '2026-09-12', coverage_pct: 81 }, linked_finding_ids: ['F-1027'] },
  { record_id: 'ALR-70114', record_type: 'Alert', entity_id: 'CSE-12', timestamp: '2026-09-09T02:11:04Z', fields: { severity: 'High', closed: '02:11:41', investigation_id: null }, linked_finding_ids: ['F-1038', 'F-1011'] },
  { record_id: 'ALR-70115', record_type: 'Alert', entity_id: 'CSE-12', timestamp: '2026-09-09T02:14:10Z', fields: { severity: 'Medium', closed: '02:14:48', investigation_id: null }, linked_finding_ids: ['F-1038'] },
  { record_id: 'RPT-KPI-Q3', record_type: 'Report', entity_id: 'CSE-12', timestamp: '2026-09-30T00:00:00Z', fields: { section: '§4.2', claim: '100% of alerts triaged within 30 min' }, linked_finding_ids: ['F-1038', 'F-1011'] },
  { record_id: 'ALR-91002', record_type: 'Alert', entity_id: 'CSE-03', timestamp: '2026-09-20T07:30:00Z', fields: { severity: 'Medium', investigation_id: null }, linked_finding_ids: ['F-1031', 'F-0997'] },
  { record_id: 'CASE-5521', record_type: 'Case', entity_id: 'CSE-15', timestamp: '2026-09-03T11:00:00Z', fields: { outcome: 'Confirmed', remediation_status: null, closed: '2026-09-03' }, linked_finding_ids: ['F-1019'] },
  { record_id: 'CASE-5530', record_type: 'Case', entity_id: 'CSE-15', timestamp: '2026-09-05T08:40:00Z', fields: { outcome: 'Confirmed', remediation_status: null }, linked_finding_ids: ['F-1019', 'F-0976'] },
  { record_id: 'ESC-2201', record_type: 'Escalation', entity_id: 'CSE-15', timestamp: '2026-09-06T21:10:00Z', fields: { level: 'L2', delay_hours: 4.6, status: 'Completed' }, linked_finding_ids: ['F-0969'] },
  { record_id: 'ALR-60001', record_type: 'Alert', entity_id: 'CSE-21', timestamp: '2026-09-11T05:20:00Z', fields: { severity: 'Medium', investigation_id: null }, linked_finding_ids: ['F-0988'] }];
export const reports: T.ReportItem[] = [
  { report_id: 'RPT-A-001', kind: 'Supervisory Assessment', title: 'Supervisory Assessment Report — 2026-Q3', generated_at: '2026-09-28T02:10:00Z', rule_model_version: '1.3.0 / IF 0.9.1', item_count: 24, formats: ['PDF', 'JSON'] },
  { report_id: 'RPT-F-014', kind: 'Finding Report', title: 'Finding Report — F-1042', generated_at: '2026-09-28T11:05:00Z', rule_model_version: '1.3.0', item_count: 1, formats: ['PDF', 'JSON'] },
  { report_id: 'RPT-E-007', kind: 'Evidence Report', title: 'Evidence Report — CSE-07', generated_at: '2026-09-28T11:30:00Z', rule_model_version: '1.3.0', item_count: 5, formats: ['PDF', 'CSV'] },
  { report_id: 'RPT-P-003', kind: 'Prioritized Review List', title: 'Prioritized Review List — 2026-Q3', generated_at: '2026-09-28T02:15:00Z', rule_model_version: '1.3.0', item_count: 138, formats: ['CSV', 'JSON'] },
  { report_id: 'RPT-H-002', kind: 'Historical Finding Records', title: 'Historical Finding Records — last 4 periods', generated_at: '2026-09-28T02:20:00Z', rule_model_version: 'multiple', item_count: 468, formats: ['CSV'] },
  { report_id: 'RPT-V-001', kind: 'Validation Metrics', title: 'Validation Metrics — 2026-Q2', generated_at: '2026-07-10T09:00:00Z', rule_model_version: '1.2.0', item_count: 6, formats: ['PDF', 'JSON'] }];
export const auditTrail: T.AuditEvent[] = [
  { event_id: 'AUD-0931', timestamp: '2026-09-28T11:42:00Z', actor: 'Examiner S. Rao', action: 'Review decision', object: 'F-1042', rule_model_version: '1.3.0', detail: 'Taken to examination' },
  { event_id: 'AUD-0930', timestamp: '2026-09-28T11:05:00Z', actor: 'Examiner S. Rao', action: 'Report generated', object: 'RPT-F-014', rule_model_version: '1.3.0', detail: 'Finding report exported (PDF)' },
  { event_id: 'AUD-0922', timestamp: '2026-09-28T02:20:00Z', actor: 'System', action: 'Assessment completed', object: 'ASM-2026-Q3', rule_model_version: '1.3.0 / IF 0.9.1', detail: '24 entities, 138 findings, 94% data completeness' },
  { event_id: 'AUD-0921', timestamp: '2026-09-28T01:55:00Z', actor: 'System', action: 'Model inference', object: 'Isolation Forest', rule_model_version: '0.9.1', detail: 'Local inference on 24 entity feature vectors' },
  { event_id: 'AUD-0915', timestamp: '2026-09-27T20:00:00Z', actor: 'System', action: 'Data validation', object: 'Input batch 2026-Q3', rule_model_version: '—', detail: '3 malformed records quarantined' },
  { event_id: 'AUD-0899', timestamp: '2026-09-20T14:12:00Z', actor: 'Validation team', action: 'Threshold updated', object: 'MON-COV-003', rule_model_version: '1.3.0', detail: 'Silence window 10 → 7 days (expert feedback)' }];
export const validation: T.ValidationData = {
  metrics: [{ label: 'Precision', value: '0.78' }, { label: 'Recall', value: '0.71' }, { label: 'False-positive rate', value: '0.09' }, { label: 'False-negative rate', value: '0.29' },
    { label: 'Examiner agreement', value: '82%' }, { label: 'Sampling reduction', value: '64%', note: 'vs manual sampling baseline' }],
  trend: { periods: ['2025-Q4', '2026-Q1', '2026-Q2'], precision: [0.66, 0.72, 0.78], recall: [0.6, 0.67, 0.71] },
  comparisons: [
    { finding_id: 'F-1042', entity_name: en('CSE-07'), cyberlens_priority: 'High', expert_assessment: 'Confirmed', agreement: true, note: 'Escalation gap verified in sample.' },
    { finding_id: 'F-1038', entity_name: en('CSE-12'), cyberlens_priority: 'High', expert_assessment: 'Confirmed', agreement: true, note: 'Closure pattern confirmed.' },
    { finding_id: 'F-1031', entity_name: en('CSE-03'), cyberlens_priority: 'Medium', expert_assessment: 'Not confirmed', agreement: false, note: 'Volume spike explained by planned penetration test.' },
    { finding_id: 'F-1019', entity_name: en('CSE-15'), cyberlens_priority: 'Medium', expert_assessment: 'Partially confirmed', agreement: true, note: 'Remediation tracked in an external system.' }],
  missed_by_cyberlens: [{ description: 'Stale detection content not updated for 8 months', entity_name: en('CSE-21') }],
};
