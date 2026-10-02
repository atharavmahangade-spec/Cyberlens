import { useState } from 'react';
import { Alert, Box, Button, Chip, MenuItem, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { Link as RLink, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { TYPE_META } from '../nav';
import type { ExpertFeedback, ReportItem } from '../types';
import { Async, ChartPanel, ConfChip, Empty, Grid, Kpi, PageHeader, Panel, PriorityChip, fmt, useApi } from '../components/ui';

export function EvidenceExplorer() {
  const s = useApi(() => api.getEvidence()); const [q, setQ] = useState('');
  return <><PageHeader title="Evidence Explorer" sub="All supporting evidence across findings. Navigate Finding → Evidence → Source Record." />
    <TextField size="small" label="Search evidence" value={q} onChange={(e) => setQ(e.target.value)} sx={{ mb: 2 }} />
    <Async s={s}>{(rows) => <Panel><Table size="small"><TableHead><TableRow><TableCell>Evidence</TableCell><TableCell>Finding</TableCell><TableCell>Entity</TableCell><TableCell>Signal</TableCell><TableCell>Confidence</TableCell><TableCell>Source records</TableCell></TableRow></TableHead>
      <TableBody>{rows.filter((r) => !q || `${r.label} ${r.detail} ${r.entity_name}`.toLowerCase().includes(q.toLowerCase())).map((r) => <TableRow key={r.evidence_id}>
        <TableCell><Typography variant="body2" fontWeight={600}>{r.label}</Typography><Typography variant="caption" color="text.secondary">{r.detail}</Typography></TableCell>
        <TableCell><RLink to={`/findings/${r.finding_id}`}>{r.finding_id}</RLink></TableCell><TableCell>{r.entity_name}</TableCell><TableCell>{TYPE_META[r.signal_type].label}</TableCell><TableCell><ConfChip c={r.confidence} /></TableCell>
        <TableCell>{r.source_record_ids.map((x) => <Chip key={x} size="small" clickable component={RLink} to={`/sources?id=${x}`} label={x} sx={{ mr: 0.5 }} />)}</TableCell></TableRow>)}</TableBody></Table></Panel>}</Async></>;
}
export function SourceRecords() {
  const [sp, setSp] = useSearchParams(); const sel = sp.get('id'); const [q, setQ] = useState('');
  const s = useApi(() => api.getSourceRecords());
  return <><PageHeader title="Source Record Traceability" sub="Underlying alert, investigation, escalation, case, asset, monitoring and report records referenced by findings." />
    <TextField size="small" label="Search records" value={q} onChange={(e) => setQ(e.target.value)} sx={{ mb: 2 }} />
    <Async s={s}>{(rows) => { const cur = rows.find((r) => r.record_id === sel); return <Grid min={420}>
      <Panel><Table size="small"><TableHead><TableRow><TableCell>Record</TableCell><TableCell>Type</TableCell><TableCell>Entity</TableCell><TableCell>Timestamp</TableCell></TableRow></TableHead>
        <TableBody>{rows.filter((r) => !q || `${r.record_id} ${r.record_type} ${r.entity_id}`.toLowerCase().includes(q.toLowerCase())).map((r) => <TableRow key={r.record_id} hover selected={r.record_id === sel} sx={{ cursor: 'pointer' }} onClick={() => setSp({ id: r.record_id })}><TableCell>{r.record_id}</TableCell><TableCell>{r.record_type}</TableCell><TableCell>{r.entity_id}</TableCell><TableCell>{fmt(r.timestamp)}</TableCell></TableRow>)}</TableBody></Table></Panel>
      <Panel title="Record detail">{!cur ? <Empty text="Select a record to inspect its fields and linked findings." /> : <>
        <Typography variant="h6">{cur.record_id}</Typography><Typography color="text.secondary" sx={{ mb: 1 }}>{cur.record_type} · {cur.entity_id} · {fmt(cur.timestamp)}</Typography>
        <Table size="small"><TableBody>{Object.entries(cur.fields).map(([k, v]) => <TableRow key={k}><TableCell sx={{ fontWeight: 600 }}>{k}</TableCell><TableCell sx={{ fontFamily: 'monospace' }}>{v ?? 'NULL'}</TableCell></TableRow>)}</TableBody></Table>
        <Typography variant="overline" sx={{ display: 'block', mt: 2 }}>Linked findings</Typography>{cur.linked_finding_ids.map((f) => <Chip key={f} clickable component={RLink} to={`/findings/${f}`} label={f} sx={{ mr: 0.5 }} />)}</>}</Panel></Grid>; }}</Async></>;
}
const download = (r: ReportItem) => { const u = URL.createObjectURL(new Blob([JSON.stringify(r, null, 2)], { type: 'application/json' })); const a = document.createElement('a'); a.href = u; a.download = `${r.report_id}.json`; a.click(); URL.revokeObjectURL(u); };
export function Reports() {
  const s = useApi(() => api.getReports());
  return <><PageHeader title="Reporting" sub="Supervisory assessment, finding, evidence and prioritized-review reports, historical finding records and validation metrics. Each retains timestamp and rule/model version." />
    {api.isMock && <Alert severity="info" sx={{ mb: 2 }}>Mock mode: export downloads report metadata only. Full export is produced by the local backend.</Alert>}
    <Async s={s}>{(rows) => <Panel><Table size="small"><TableHead><TableRow><TableCell>Report</TableCell><TableCell>Type</TableCell><TableCell>Generated</TableCell><TableCell>Rule/model version</TableCell><TableCell>Items</TableCell><TableCell>Formats</TableCell><TableCell /></TableRow></TableHead>
      <TableBody>{rows.map((r) => <TableRow key={r.report_id}><TableCell>{r.title}</TableCell><TableCell>{r.kind}</TableCell><TableCell>{fmt(r.generated_at)}</TableCell><TableCell>{r.rule_model_version}</TableCell><TableCell>{r.item_count}</TableCell><TableCell>{r.formats.join(', ')}</TableCell><TableCell><Button size="small" onClick={() => download(r)}>Export</Button></TableCell></TableRow>)}</TableBody></Table></Panel>}</Async></>;
}
export function AuditTrail() {
  const s = useApi(() => api.getAuditTrail()); const [q, setQ] = useState('');
  return <><PageHeader title="Audit Trail" sub="Local, reproducible record of analytical runs, model inference, examiner decisions and configuration changes, with rule/model versions." />
    <TextField size="small" label="Search audit log" value={q} onChange={(e) => setQ(e.target.value)} sx={{ mb: 2 }} />
    <Async s={s}>{(rows) => <Panel><Table size="small"><TableHead><TableRow><TableCell>Time</TableCell><TableCell>Actor</TableCell><TableCell>Action</TableCell><TableCell>Object</TableCell><TableCell>Version</TableCell><TableCell>Detail</TableCell></TableRow></TableHead>
      <TableBody>{rows.filter((r) => !q || JSON.stringify(r).toLowerCase().includes(q.toLowerCase())).map((r) => <TableRow key={r.event_id}><TableCell>{fmt(r.timestamp)}</TableCell><TableCell>{r.actor}</TableCell><TableCell>{r.action}</TableCell><TableCell>{r.object}</TableCell><TableCell>{r.rule_model_version}</TableCell><TableCell>{r.detail}</TableCell></TableRow>)}</TableBody></Table></Panel>}</Async></>;
}
export function Validation() {
  const s = useApi(() => api.getValidation()); const [fb, setFb] = useState<ExpertFeedback>({ finding_id: '', target: 'rule', comment: '' }); const [ok, setOk] = useState(false);
  return <><PageHeader title="Expert Validation" sub="CyberLens findings compared with expert manual assessment: precision, recall, false positives/negatives, examiner agreement, and feedback for rule, threshold, feature and model calibration." />
    <Async s={s}>{(v) => <>
      <Grid min={170}>{v.metrics.map((m) => <Kpi key={m.label} label={m.label} value={m.value} sub={m.note} />)}</Grid>
      <ChartPanel title="Precision and recall by period" option={{ tooltip: { trigger: 'axis' }, legend: { top: 0 }, xAxis: { type: 'category', data: v.trend.periods }, yAxis: { type: 'value', min: 0, max: 1 }, series: [{ name: 'Precision', type: 'line', data: v.trend.precision }, { name: 'Recall', type: 'line', data: v.trend.recall }] }} />
      <Panel title="CyberLens vs expert assessment" sx={{ my: 2 }}><Table size="small"><TableHead><TableRow><TableCell>Finding</TableCell><TableCell>Entity</TableCell><TableCell>CyberLens priority</TableCell><TableCell>Expert assessment</TableCell><TableCell>Agreement</TableCell><TableCell>Note</TableCell></TableRow></TableHead>
        <TableBody>{v.comparisons.map((c) => <TableRow key={c.finding_id}><TableCell><RLink to={`/findings/${c.finding_id}`}>{c.finding_id}</RLink></TableCell><TableCell>{c.entity_name}</TableCell><TableCell><PriorityChip p={c.cyberlens_priority} /></TableCell><TableCell>{c.expert_assessment}</TableCell><TableCell><Chip size="small" color={c.agreement ? 'success' : 'error'} variant="outlined" label={c.agreement ? 'Agree' : 'Disagree'} /></TableCell><TableCell>{c.note}</TableCell></TableRow>)}</TableBody></Table></Panel>
      <Grid><Panel title="Missed by CyberLens (false negatives)">{v.missed_by_cyberlens.map((m) => <Typography key={m.description}>{m.entity_name}: {m.description}</Typography>)}</Panel>
        <Panel title="Expert feedback for calibration">{ok && <Alert severity="success" sx={{ mb: 1 }}>Feedback recorded.</Alert>}<Stack spacing={1.5}>
          <TextField size="small" label="Finding ID" value={fb.finding_id} onChange={(e) => setFb({ ...fb, finding_id: e.target.value })} />
          <TextField select size="small" label="Calibration target" value={fb.target} onChange={(e) => setFb({ ...fb, target: e.target.value as ExpertFeedback['target'] })}>{['rule', 'threshold', 'feature', 'model'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}</TextField>
          <TextField size="small" multiline minRows={2} label="Comment" value={fb.comment} onChange={(e) => setFb({ ...fb, comment: e.target.value })} />
          <Box><Button variant="contained" disabled={!fb.finding_id || !fb.comment} onClick={async () => { await api.submitExpertFeedback(fb); setOk(true); setFb({ finding_id: '', target: 'rule', comment: '' }); }}>Submit feedback</Button></Box></Stack></Panel></Grid></>}</Async></>;
}
