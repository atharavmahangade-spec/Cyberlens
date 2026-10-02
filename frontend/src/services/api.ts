// Single data-access layer. Mock by default; set VITE_API_BASE_URL to call the local FastAPI backend.
import * as M from '../data/mock';
import type * as T from '../types';

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '';
const wait = <V,>(v: V): Promise<V> => new Promise((r) => setTimeout(() => r(structuredClone(v)), 120));

async function get<V>(path: string, mock: () => V): Promise<V> {
  if (!BASE) return wait(mock());
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`);
  return res.json() as Promise<V>;
}
async function post<V>(path: string, body: unknown, mock: () => V): Promise<V> {
  if (!BASE) return wait(mock());
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} — ${path}`);
  return res.json() as Promise<V>;
}
const decisions: Record<string, T.ReviewStatus> = {};
const withDecision = (f: T.Finding): T.Finding => ({ ...f, status: decisions[f.finding_id] ?? f.status });

export const api = {
  isMock: !BASE,
  getEntities: () => get<T.Entity[]>('/entities', () => M.entities),
  getOverview: () => get<T.OverviewData>('/overview', () => M.overview),
  getAssessments: () => get<T.AssessmentRun[]>('/assessments', () => M.assessments),
  getFindings: (f: T.FindingFilter = {}) =>
    get<T.Finding[]>(`/findings${f.entity_id ? `?entity_id=${f.entity_id}` : ''}`, () => M.findings.map(withDecision))
      .then((l) => l.filter((x) => (!f.types || f.types.includes(x.signal_type)) && (!f.entity_id || x.entity_id === f.entity_id))),
  getFinding: (id: string) => get<T.Finding | undefined>(`/findings/${id}`, () => { const f = M.findings.find((x) => x.finding_id === id); return f && withDecision(f); }),
  getLifecycle: (entityId: string) => get<T.LifecycleSummary | undefined>(`/lifecycle/${entityId}`, () => M.lifecycles.find((l) => l.entity_id === entityId)),
  getExpectedEvidence: () => get<T.ExpectedEvidenceModel>('/expected-evidence', () => M.expectedEvidence),
  getContradictions: () => get<T.Contradiction[]>('/contradictions', () => M.contradictions),
  getAnomalies: () => get<T.AnomalyResult>('/anomalies', () => M.anomalies),
  getStatistics: (entityId: string) => get<T.StatRow[]>(`/statistics/${entityId}`, () => M.statistics.filter((s) => s.entity_id === entityId)),
  getPeerComparison: (entityId: string) => get<T.PeerRow[]>(`/peer-comparison/${entityId}`, () => M.peers.filter((s) => s.entity_id === entityId)),
  getHistory: (entityId: string) => get<T.HistSeries[]>(`/history/${entityId}`, () => M.history.filter((s) => s.entity_id === entityId)),
  getFusion: () => get<T.FusionItem[]>('/fusion', () => M.fusion),
  getEvidence: () => get<T.EvidenceRow[]>('/evidence', () => M.findings.flatMap((f) => f.evidence.map((e) => ({ ...e, finding_id: f.finding_id, entity_id: f.entity_id, entity_name: f.entity_name, signal_type: f.signal_type, confidence: f.evidence_confidence })))),
  getSourceRecords: (ids?: string[]) => get<T.SourceRecord[]>(`/source-records${ids ? `?ids=${ids.join(',')}` : ''}`, () => M.sourceRecords).then((r) => (ids ? r.filter((x) => ids.includes(x.record_id)) : r)),
  getReports: () => get<T.ReportItem[]>('/reports', () => M.reports),
  getAuditTrail: () => get<T.AuditEvent[]>('/audit', () => M.auditTrail),
  getValidation: () => get<T.ValidationData>('/validation', () => M.validation),
  submitReviewDecision: (d: T.ReviewDecision) => post<T.ReviewDecision>('/review-decisions', d, () => { decisions[d.finding_id] = d.decision; return d; }),
  submitExpertFeedback: (f: T.ExpertFeedback) => post<T.ExpertFeedback>('/expert-feedback', f, () => f),
};
