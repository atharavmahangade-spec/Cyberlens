import { useState } from 'react';
import { Chip, LinearProgress, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import { Link as RLink } from 'react-router-dom';
import { api } from '../services/api';
import FindingTable from '../components/FindingTable';
import { Async, ChartPanel, Empty, EntitySelect, Grid, PageHeader, Panel, useApi } from '../components/ui';

export function Anomalies() {
  const s = useApi(() => api.getAnomalies()); const f = useApi(() => api.getFindings({ types: ['anomaly'] }));
  return <><PageHeader title="Anomaly & Behaviour Analytics" sub="Unsupervised, locally-run Isolation Forest surfaces unusual operational patterns not covered by deterministic rules. It does not determine whether a cyberattack occurred." />
    <Async s={s}>{(a) => <>
      <ChartPanel title={`Anomaly score by entity — ${a.model} v${a.model_version}`} option={{ tooltip: {}, xAxis: { type: 'category', data: a.points.map((p) => p.entity_id) }, yAxis: { type: 'value', min: 0, max: 1 },
        series: [{ type: 'bar', data: a.points.map((p) => ({ value: p.score, itemStyle: { color: p.score >= a.threshold ? '#ef6c00' : '#6d7f94', borderRadius: [4, 4, 0, 0] } })), markLine: { symbol: 'none', label: { formatter: `threshold ${a.threshold}` }, data: [{ yAxis: a.threshold }] } }] }} />
      <Panel title="Contributing feature deviations (z-scores)" sx={{ my: 2 }}><Table size="small"><TableHead><TableRow><TableCell>Entity</TableCell><TableCell>Score</TableCell><TableCell>Top deviating features</TableCell><TableCell>Finding</TableCell></TableRow></TableHead>
        <TableBody>{a.points.map((p) => <TableRow key={p.entity_id}><TableCell>{p.entity_name}</TableCell><TableCell>{p.score}</TableCell><TableCell>{p.features.map((x) => <Chip key={x.name} size="small" sx={{ mr: 0.5 }} variant="outlined" label={`${x.name}: ${x.z > 0 ? '+' : ''}${x.z}`} />)}</TableCell><TableCell>{p.finding_id && <RLink to={`/findings/${p.finding_id}`}>{p.finding_id}</RLink>}</TableCell></TableRow>)}</TableBody></Table></Panel></>}</Async>
    <Async s={f}>{(rows) => <Panel title="Anomaly findings"><FindingTable findings={rows} /></Panel>}</Async></>;
}
export function Statistics() {
  const [e, setE] = useState('CSE-07'); const s = useApi(() => api.getStatistics(e), [e]);
  return <><PageHeader title="Statistical Analysis" sub="Percentiles, median deviation, IQR and Z-score against historical and peer baselines, computed by the backend." action={<EntitySelect value={e} onChange={setE} />} />
    <Async s={s}>{(r) => !r.length ? <Empty text="No statistical results for this entity." /> : <Grid min={420}>
      <ChartPanel title="Z-score by metric" option={{ tooltip: {}, grid: { left: 150, right: 20, top: 20, bottom: 30 }, xAxis: { type: 'value' }, yAxis: { type: 'category', data: r.map((x) => x.metric) }, series: [{ type: 'bar', data: r.map((x) => ({ value: x.z_score, itemStyle: { color: x.flagged ? '#ef6c00' : '#6d7f94' } })) }] }} />
      <Panel title="Metrics"><Table size="small"><TableHead><TableRow><TableCell>Metric</TableCell><TableCell>Value</TableCell><TableCell>Median</TableCell><TableCell>IQR</TableCell><TableCell>Z</TableCell><TableCell>Pctl</TableCell><TableCell /></TableRow></TableHead>
        <TableBody>{r.map((x) => <TableRow key={x.metric}><TableCell>{x.metric}</TableCell><TableCell>{x.value}</TableCell><TableCell>{x.median}</TableCell><TableCell>{x.iqr_low}–{x.iqr_high}</TableCell><TableCell>{x.z_score}</TableCell><TableCell>{x.percentile}</TableCell><TableCell>{x.flagged && <Chip size="small" color="warning" label="Outlier" />}</TableCell></TableRow>)}</TableBody></Table></Panel></Grid>}</Async></>;
}
export function Peer() {
  const [e, setE] = useState('CSE-07'); const s = useApi(() => api.getPeerComparison(e), [e]); const f = useApi(() => api.getFindings({ types: ['peer_deviation'] }));
  return <><PageHeader title="Peer Comparison" sub="Comparison with comparable CSEs. Deviations are context for the examiner, not an automatic judgement of an entity." action={<EntitySelect value={e} onChange={setE} />} />
    <Async s={s}>{(r) => !r.length ? <Empty text="No peer comparison available for this entity." /> : <Grid min={420}>
      <ChartPanel title="Entity vs peer median" option={{ tooltip: {}, legend: { top: 0 }, xAxis: { type: 'category', data: r.map((x) => x.dimension), axisLabel: { interval: 0, fontSize: 10 } }, yAxis: { type: 'value' },
        series: [{ name: 'Entity', type: 'bar', data: r.map((x) => x.value) }, { name: 'Peer median', type: 'bar', data: r.map((x) => x.peer_median), itemStyle: { color: '#6d7f94' } }] }} />
      <Panel title="Peer position"><Table size="small"><TableHead><TableRow><TableCell>Dimension</TableCell><TableCell>Entity</TableCell><TableCell>Peer IQR</TableCell><TableCell>Percentile</TableCell></TableRow></TableHead>
        <TableBody>{r.map((x) => <TableRow key={x.dimension}><TableCell>{x.dimension}</TableCell><TableCell>{x.value}{x.unit}</TableCell><TableCell>{x.peer_p25}–{x.peer_p75}{x.unit}</TableCell><TableCell sx={{ width: 130 }}><LinearProgress variant="determinate" value={x.percentile} /><Typography variant="caption">{x.percentile}</Typography></TableCell></TableRow>)}</TableBody></Table></Panel></Grid>}</Async>
    <Async s={f}>{(rows) => <Panel title="Peer-deviation findings"><FindingTable findings={rows} /></Panel>}</Async></>;
}
export function Historical() {
  const [e, setE] = useState('CSE-07'); const s = useApi(() => api.getHistory(e), [e]);
  return <><PageHeader title="Historical Self-Benchmarking" sub="Current behaviour against the entity's own history: baselines, trends, deviation and period-over-period change. Complements peer comparison." action={<EntitySelect value={e} onChange={setE} />} />
    <Async s={s}>{(r) => !r.length ? <Empty text="No historical series for this entity." /> : <Grid min={420}>{r.map((x) => <ChartPanel key={x.metric} title={`${x.metric}${x.unit ? ` (${x.unit})` : ''}`} option={{ tooltip: { trigger: 'axis' }, xAxis: { type: 'category', data: x.periods }, yAxis: { type: 'value', scale: true },
      series: [{ type: 'line', data: x.values, smooth: true, markArea: { itemStyle: { color: 'rgba(46,125,50,.10)' }, data: [[{ yAxis: x.band_low }, { yAxis: x.band_high }]] }, markLine: { symbol: 'none', data: [{ yAxis: x.baseline, label: { formatter: 'baseline' } }] } }] }} />)}</Grid>}</Async></>;
}
export function Fusion() {
  const s = useApi(() => api.getFusion());
  return <><PageHeader title="Supervisory Signal Fusion & Review Prioritization" sub="Lifecycle, execution-gap, negative-space, peer, historical, anomaly and statistical signals combined with asset criticality and evidence strength into an explainable review priority." />
    <Async s={s}>{(items) => {
      const names = [...new Set(items.flatMap((i) => i.contributions.map((c) => c.signal)))];
      return <><ChartPanel title="Contribution of each signal to the fused review score" height={340} option={{ tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, legend: { top: 0, type: 'scroll' }, grid: { left: 190, right: 20, top: 50, bottom: 24 },
        xAxis: { type: 'value' }, yAxis: { type: 'category', inverse: true, data: items.map((i) => `${i.finding_id} · ${i.entity_name.split(' ')[0]}`) },
        series: names.map((n) => ({ name: n, type: 'bar', stack: 't', data: items.map((i) => i.contributions.find((c) => c.signal === n)?.weight ?? 0) })) }} />
        <Panel title="Prioritized review list" sx={{ mt: 2 }}><Table size="small"><TableHead><TableRow><TableCell>Finding</TableCell><TableCell>Entity / area</TableCell><TableCell>Fused score</TableCell><TableCell>Converging signals</TableCell><TableCell>Narrative</TableCell></TableRow></TableHead>
          <TableBody>{items.map((i) => <TableRow key={i.finding_id}><TableCell><RLink to={`/findings/${i.finding_id}`}>{i.finding_id}</RLink></TableCell><TableCell>{i.entity_name}<br /><Typography variant="caption" color="text.secondary">{i.area}</Typography></TableCell><TableCell>{i.fused_score}</TableCell><TableCell>{i.converging_signals}</TableCell><TableCell sx={{ maxWidth: 420 }}>{i.narrative}</TableCell></TableRow>)}</TableBody></Table></Panel></>; }}</Async></>;
}
