import type { ReactNode } from 'react';
import { useState } from 'react';
import { Alert, Box, Button, Chip, LinearProgress, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { Link as RLink, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { TYPE_META } from '../nav';
import type { ReviewStatus, SignalType } from '../types';
import FindingTable from '../components/FindingTable';
import { Async, ChartPanel, ConfChip, Empty, Grid, Kpi, PageHeader, Panel, PriorityChip, fmt, useApi } from '../components/ui';

export function Overview() {
  const s = useApi(() => api.getOverview()); const go = useNavigate();
  return <Async s={s}>{(o) => (<>
    <PageHeader title="Assessment Overview" sub={`Assessment period ${o.period}. CyberLens highlights where supervisory attention may be directed and why.`} />
    <Grid min={170}>
      <Kpi label="Entities assessed" value={o.entities_assessed} /><Kpi label="Entities requiring review" value={o.entities_requiring_review} color="#ef6c00" />
      <Kpi label="Total findings" value={o.total_findings} /><Kpi label="High-priority findings" value={o.priority_distribution.High} color="#d32f2f" />
      <Kpi label="Estimated sampling reduction" value={`${o.review_workload.estimated_sampling_reduction_pct}%`} sub={`${o.review_workload.records_prioritized.toLocaleString()} of ${o.review_workload.records_in_scope.toLocaleString()} records prioritized`} /></Grid>
    <Grid>
      <ChartPanel title="Priority distribution" option={{ tooltip: {}, series: [{ type: 'pie', radius: ['48%', '74%'], data: [
        { name: 'High', value: o.priority_distribution.High, itemStyle: { color: '#d32f2f' } }, { name: 'Medium', value: o.priority_distribution.Medium, itemStyle: { color: '#ed6c02' } }, { name: 'Low', value: o.priority_distribution.Low, itemStyle: { color: '#2e7d32' } }] }] }} />
      <ChartPanel title="Findings by signal type" option={{ tooltip: {}, xAxis: { type: 'category', data: o.findings_by_type.map((x) => TYPE_META[x.signal_type].label), axisLabel: { interval: 0, rotate: 25, fontSize: 10 } }, yAxis: { type: 'value' }, grid: { bottom: 70, left: 40, right: 12, top: 20 }, series: [{ type: 'bar', data: o.findings_by_type.map((x) => x.count), itemStyle: { borderRadius: [4, 4, 0, 0] } }] }} /></Grid>
    <Panel title="Finding views" sx={{ mb: 2 }}><Box sx={{ display: 'grid', gap: 1.5, gridTemplateColumns: 'repeat(auto-fit,minmax(170px,1fr))' }}>
      {o.findings_by_type.map((x) => <Paper key={x.signal_type} variant="outlined" sx={{ p: 1.5, cursor: 'pointer', '&:hover': { borderColor: 'primary.main' } }} onClick={() => go(TYPE_META[x.signal_type].path)}>
        <Typography variant="h6">{x.count}</Typography><Typography variant="body2" color="text.secondary">{TYPE_META[x.signal_type].label}</Typography></Paper>)}</Box></Panel>
    <Panel title="Entities requiring review — by fused review score"><Table size="small"><TableHead><TableRow><TableCell>Entity</TableCell><TableCell>Fused score</TableCell><TableCell>Open findings</TableCell><TableCell>Leading area</TableCell><TableCell>Review</TableCell></TableRow></TableHead>
      <TableBody>{o.entity_summaries.map((e) => <TableRow key={e.entity_id} hover sx={{ cursor: 'pointer' }} onClick={() => go(`/queue?entity=${e.entity_id}`)}>
        <TableCell>{e.name}</TableCell><TableCell sx={{ width: 180 }}><LinearProgress variant="determinate" value={e.fused_score} /><Typography variant="caption">{e.fused_score}</Typography></TableCell>
        <TableCell>{e.findings}</TableCell><TableCell>{e.top_area}</TableCell><TableCell>{e.requires_review ? <Chip size="small" color="warning" label="Requires review" /> : <Chip size="small" label="No priority review" />}</TableCell></TableRow>)}</TableBody></Table></Panel></>)}</Async>;
}

export function Assessments() {
  const s = useApi(() => api.getAssessments());
  return <><PageHeader title="Assessments" sub="Retained assessment runs with timestamps and rule/model versions (reproducible and auditable)." />
    <Async s={s}>{(rows) => <Panel><Table size="small"><TableHead><TableRow><TableCell>Assessment</TableCell><TableCell>Period</TableCell><TableCell>Completed</TableCell><TableCell>Entities</TableCell><TableCell>Findings</TableCell><TableCell>Rule/model version</TableCell><TableCell>Data completeness</TableCell><TableCell>Status</TableCell></TableRow></TableHead>
      <TableBody>{rows.map((r) => <TableRow key={r.assessment_id}><TableCell>{r.assessment_id}</TableCell><TableCell>{r.period}</TableCell><TableCell>{fmt(r.completed_at)}</TableCell><TableCell>{r.entities}</TableCell><TableCell>{r.findings}</TableCell><TableCell>{r.rule_model_version}</TableCell><TableCell>{r.data_completeness_pct}%</TableCell><TableCell><Chip size="small" label={r.status} color={r.status === 'Complete' ? 'success' : 'warning'} variant="outlined" /></TableCell></TableRow>)}</TableBody></Table></Panel>}</Async></>;
}

export function ReviewQueue() {
  const [sp] = useSearchParams(); const entity = sp.get('entity') ?? '';
  const [pri, setPri] = useState(''); const [type, setType] = useState(''); const [q, setQ] = useState('');
  const s = useApi(() => api.getFindings({ entity_id: entity || undefined }), [entity]);
  return <><PageHeader title="Review Queue" sub="Prioritized by Supervisory Signal Fusion: signal strength, evidence strength, asset criticality, lifecycle impact, historical and peer deviation, and signal convergence. Decision support only." />
    <Stack direction="row" spacing={1.5} sx={{ mb: 2, flexWrap: 'wrap', gap: 1 }}>
      <TextField size="small" label="Search" value={q} onChange={(e) => setQ(e.target.value)} />
      <TextField select size="small" label="Priority" value={pri} onChange={(e) => setPri(e.target.value)} sx={{ minWidth: 130 }}><MenuItem value="">All</MenuItem>{['High', 'Medium', 'Low'].map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}</TextField>
      <TextField select size="small" label="Signal type" value={type} onChange={(e) => setType(e.target.value)} sx={{ minWidth: 190 }}><MenuItem value="">All</MenuItem>{(Object.keys(TYPE_META) as SignalType[]).map((t) => <MenuItem key={t} value={t}>{TYPE_META[t].label}</MenuItem>)}</TextField>
      {entity && <Chip label={`Entity: ${entity}`} component={RLink} to="/queue" clickable onDelete={() => undefined} />}</Stack>
    <Async s={s}>{(rows) => <Panel><FindingTable findings={rows.filter((f) => (!pri || f.priority === pri) && (!type || f.signal_type === type) && (!q || `${f.title} ${f.entity_name} ${f.finding_id} ${f.area}`.toLowerCase().includes(q.toLowerCase())))
      .sort((a, b) => b.fusion_score - a.fusion_score)} /></Panel>}</Async></>;
}

const Step = ({ n, label, children }: { n: number; label: string; children: ReactNode }) => (
  <Paper variant="outlined" sx={{ p: 2, mb: 1.5 }}><Typography variant="overline" color="primary" fontWeight={700}>{n}. {label}</Typography>{children}</Paper>);

export function FindingDetail() {
  const { id = '' } = useParams(); const [ver, setVer] = useState(0); const [note, setNote] = useState(''); const [msg, setMsg] = useState('');
  const s = useApi(() => api.getFinding(id), [id, ver]);
  const rec = useApi(async () => { const f = await api.getFinding(id); return f ? api.getSourceRecords(f.source_record_ids) : []; }, [id]);
  const decide = async (d: ReviewStatus) => { await api.submitReviewDecision({ finding_id: id, decision: d, note }); setMsg(`Decision recorded: ${d}. Logged to the local audit trail.`); setNote(''); setVer((v) => v + 1); };
  return <Async s={s}>{(f) => !f ? <Empty text={`Finding ${id} not found.`} /> : (<>
    <PageHeader title={f.title} sub={`${f.finding_id} · ${f.entity_name} · ${f.area}`} action={<Stack direction="row" spacing={1}><PriorityChip p={f.priority} /><ConfChip c={f.evidence_confidence} /><Chip size="small" label={f.status} /></Stack>} />
    <Stack direction="row" spacing={0.5} sx={{ mb: 2, flexWrap: 'wrap', gap: 0.5, alignItems: 'center' }}>
      {['Finding', 'Rule/Model', 'Reason', 'Evidence', 'Source Records', 'Context', 'Version'].map((x, i, a) => <Box key={x} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}><Chip size="small" color="primary" variant="outlined" label={x} />{i < a.length - 1 && '→'}</Box>)}</Stack>
    <Panel sx={{ mb: 2, borderColor: 'primary.main' }} title="Why was this flagged?"><Typography>{f.reason}</Typography><Typography color="text.secondary" sx={{ mt: 1 }}>{f.narrative}</Typography></Panel>
    <Grid min={420}><Box>
      <Step n={1} label="Rule / model"><Typography>{f.rule_model_name}</Typography><Typography variant="caption" color="text.secondary">Rule ID {f.rule_id} · {TYPE_META[f.signal_type].label} · {f.category}</Typography></Step>
      <Step n={2} label="Supporting evidence">{f.evidence.map((e) => <Box key={e.evidence_id} sx={{ mt: 1 }}><Typography variant="body2" fontWeight={600}>{e.label}</Typography><Typography variant="body2" color="text.secondary">{e.detail}</Typography>
        <Stack direction="row" spacing={0.5} sx={{ mt: 0.5, flexWrap: 'wrap' }}>{e.source_record_ids.map((r) => <Chip key={r} size="small" clickable component={RLink} to={`/sources?id=${r}`} label={r} />)}</Stack></Box>)}</Step>
      <Step n={3} label="Source records"><Async s={rec}>{(rs) => rs.length ? <Table size="small"><TableBody>{rs.map((r) => <TableRow key={r.record_id}><TableCell><RLink to={`/sources?id=${r.record_id}`}>{r.record_id}</RLink></TableCell><TableCell>{r.record_type}</TableCell><TableCell sx={{ fontSize: 12 }}>{Object.entries(r.fields).map(([k, v]) => `${k}: ${v ?? 'NULL'}`).join(' · ')}</TableCell></TableRow>)}</TableBody></Table> : <Empty text="No source records returned." />}</Async></Step></Box>
    <Box>
      <Step n={4} label="Context">{([['Historical', f.historical_context], ['Peer', f.peer_context], ['Lifecycle', f.lifecycle_context]] as const).map(([l, c]) => c && <Box key={l} sx={{ mt: 1 }}><Typography variant="body2" fontWeight={600}>{l} context</Typography><Typography variant="body2" color="text.secondary">{c.summary}</Typography>
        <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }}>{c.metrics?.map((m) => <Chip key={m.label} size="small" variant="outlined" label={`${m.label}: ${m.value}`} />)}</Stack></Box>)}
        <Typography variant="body2" sx={{ mt: 1 }}>Asset criticality: <b>{f.asset_criticality}</b> · Evidence availability: <b>{f.evidence_availability}</b></Typography></Step>
      <Step n={5} label="Version & provenance"><Typography variant="body2">Rule/model version <b>{f.rule_model_version}</b> · Generated {fmt(f.created_at)} · Fusion score {f.fusion_score}</Typography>
        <Typography variant="caption" color="text.secondary">Missing or incomplete data is not treated as proof of weakness.</Typography></Step>
      <Panel title="Human review — examiner decision"><Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>CyberLens does not enforce controls, penalize entities, or make supervisory determinations.</Typography>
        {msg && <Alert severity="success" sx={{ mb: 1 }}>{msg}</Alert>}
        <TextField fullWidth multiline minRows={2} size="small" label="Examiner note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
        <Stack direction="row" spacing={1} sx={{ mt: 1.5, flexWrap: 'wrap', gap: 1 }}><Button variant="contained" onClick={() => decide('Under examination')}>Take to examination</Button><Button variant="outlined" onClick={() => decide('Deferred')}>Defer</Button><Button variant="outlined" onClick={() => decide('Closed by examiner')}>Close — no further action</Button></Stack></Panel></Box></Grid></>)}</Async>;
}
