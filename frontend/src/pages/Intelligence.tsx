import { useState, type ReactNode } from 'react';
import { Chip, LinearProgress, Table, TableBody, TableCell, TableHead, TableRow, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { Link as RLink } from 'react-router-dom';
import { api } from '../services/api';
import type { SignalType } from '../types';
import FindingTable from '../components/FindingTable';
import { Async, ChartPanel, ConfChip, Empty, EntitySelect, Grid, Kpi, PageHeader, Panel, useApi } from '../components/ui';

function Findings({ types, title, sub, children }: { types: SignalType[]; title: string; sub: string; children?: ReactNode }) {
  const s = useApi(() => api.getFindings({ types }), [types.join()]);
  return <><PageHeader title={title} sub={sub} />{children}<Async s={s}>{(f) => <Panel title={`${f.length} findings`}><FindingTable findings={f} /></Panel>}</Async></>;
}
export function NegativeSpace() {
  return <Findings types={['negative_space']} title="Negative-Space Detection" sub="Significant absences: missing investigations, escalations, monitoring or remediation evidence, missing lifecycle stages and unexpectedly low activity. Absence is a prompt for review, not proof of weakness." />;
}
export function ExecutionGaps() {
  const [v, setV] = useState<'all' | 'execution_gap' | 'monitoring'>('all');
  const types: SignalType[] = v === 'all' ? ['execution_gap', 'monitoring'] : [v];
  return <><Findings key={v} types={types} title="Execution Gap Detection" sub="Differences between expected SOC processes and observed execution across escalation, investigation, closure, remediation, KPI/SLA, evidence and monitoring/coverage.">
    <ToggleButtonGroup exclusive size="small" value={v} onChange={(_, x) => x && setV(x)} sx={{ mb: 2 }}><ToggleButton value="all">All</ToggleButton><ToggleButton value="execution_gap">Process execution</ToggleButton><ToggleButton value="monitoring">Monitoring &amp; coverage</ToggleButton></ToggleButtonGroup></Findings></>;
}
export function Lifecycle() {
  const [e, setE] = useState('CSE-07');
  const s = useApi(() => api.getLifecycle(e), [e]);
  return <><PageHeader title="SOC Operational Lifecycle Intelligence" sub="Alert → Acknowledgement → Investigation → Escalation → Case Management → Remediation → Closure. Reconstructed sequences, missing stages and unexpected transitions feed downstream signal fusion." action={<EntitySelect value={e} onChange={setE} />} />
    <Async s={s}>{(l) => !l ? <Empty text="No lifecycle data for this entity in the current assessment." /> : <>
      <Grid min={180}>{l.indicators.map((i) => <Kpi key={i.label} label={i.label} value={i.value} />)}</Grid>
      <ChartPanel title="Records reaching each lifecycle stage" height={320} option={{ tooltip: {}, xAxis: { type: 'category', data: l.stages.map((x) => x.stage), axisLabel: { interval: 0, fontSize: 10 } }, yAxis: { type: 'value' }, series: [{ type: 'bar', data: l.stages.map((x) => x.count), label: { show: true, position: 'top', fontSize: 10 }, itemStyle: { borderRadius: [4, 4, 0, 0] } }] }} />
      <Panel title="Lifecycle breakdowns" sx={{ my: 2 }}>{l.breakdowns.map((b) => <Typography key={b.description} sx={{ mb: 1 }}>{b.description} {b.finding_id && <Chip size="small" clickable component={RLink} to={`/findings/${b.finding_id}`} label={b.finding_id} />}</Typography>)}</Panel></>}</Async>
    <LifecycleFindings /></>;
}
function LifecycleFindings() {
  const s = useApi(() => api.getFindings({ types: ['lifecycle'] }));
  return <Async s={s}>{(f) => <Panel title="Lifecycle findings"><FindingTable findings={f} /></Panel>}</Async>;
}
export function ExpectedEvidence() {
  const s = useApi(() => api.getExpectedEvidence()); const [e, setE] = useState('CSE-07');
  return <><PageHeader title="Expected Evidence Model" sub="Expected operational evidence versus observed operational evidence, per process type. Drives negative-space detection, execution-gap detection, evidence completeness and confidence." action={<EntitySelect value={e} onChange={setE} />} />
    <Async s={s}>{(m) => <>
      <Panel title={`Model definitions · v${m.version}`} sx={{ mb: 2 }}><Table size="small"><TableHead><TableRow><TableCell>Process type</TableCell><TableCell>Expected stages</TableCell><TableCell>Expected evidence</TableCell></TableRow></TableHead>
        <TableBody>{m.definitions.map((d) => <TableRow key={d.process_type}><TableCell>{d.process_type}</TableCell><TableCell>{d.expected_stages.join(' → ')}</TableCell><TableCell>{d.expected_evidence.join(', ')}</TableCell></TableRow>)}</TableBody></Table></Panel>
      <Panel title="Expected vs observed evidence">{(() => { const rows = m.comparison.filter((c) => c.entity_id === e); return rows.length ? <Table size="small"><TableHead><TableRow><TableCell>Process</TableCell><TableCell>Evidence category</TableCell><TableCell>Expected</TableCell><TableCell>Observed</TableCell><TableCell sx={{ width: 160 }}>Presence</TableCell><TableCell>Status</TableCell><TableCell>Finding</TableCell></TableRow></TableHead>
        <TableBody>{rows.map((r) => <TableRow key={r.process_type + r.evidence_category}><TableCell>{r.process_type}</TableCell><TableCell>{r.evidence_category}</TableCell><TableCell>{r.expected}</TableCell><TableCell>{r.observed}</TableCell>
          <TableCell><LinearProgress variant="determinate" color={r.status === 'Complete' ? 'success' : r.status === 'Partial' ? 'warning' : 'error'} value={Math.min(100, (r.observed / r.expected) * 100)} /></TableCell>
          <TableCell><Chip size="small" label={r.status} color={r.status === 'Complete' ? 'success' : r.status === 'Partial' ? 'warning' : 'error'} variant="outlined" /></TableCell>
          <TableCell>{r.finding_id && <RLink to={`/findings/${r.finding_id}`}>{r.finding_id}</RLink>}</TableCell></TableRow>)}</TableBody></Table> : <Empty text="No expected-vs-observed comparison for this entity." />; })()}</Panel></>}</Async></>;
}
export function Contradictions() {
  const s = useApi(() => api.getContradictions());
  return <><PageHeader title="Capability–Evidence Contradiction Analysis" sub="Documented or reported capability compared with operational evidence. Potential inconsistencies are evidence-based and presented for human review only." />
    <Async s={s}>{(rows) => <Panel><Table size="small"><TableHead><TableRow><TableCell>Entity</TableCell><TableCell>Reported capability</TableCell><TableCell>Source</TableCell><TableCell>Observed evidence</TableCell><TableCell>Confidence</TableCell><TableCell>Finding</TableCell></TableRow></TableHead>
      <TableBody>{rows.map((r) => <TableRow key={r.id}><TableCell>{r.entity_id}</TableCell><TableCell>{r.claim}</TableCell><TableCell>{r.claim_source}</TableCell><TableCell>{r.observed}</TableCell><TableCell><ConfChip c={r.confidence} /></TableCell><TableCell><RLink to={`/findings/${r.finding_id}`}>{r.finding_id}</RLink></TableCell></TableRow>)}</TableBody></Table></Panel>}</Async></>;
}
