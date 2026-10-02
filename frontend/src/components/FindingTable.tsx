import { Chip, LinearProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import type { Finding } from '../types';
import { TYPE_META } from '../nav';
import { ConfChip, Empty, PriorityChip } from './ui';

export default function FindingTable({ findings }: { findings: Finding[] }) {
  const go = useNavigate();
  if (!findings.length) return <Empty text="No findings match the current view." />;
  return (
    <TableContainer><Table size="small" sx={{ minWidth: 760 }}>
      <TableHead><TableRow><TableCell>Priority</TableCell><TableCell>Finding</TableCell><TableCell>Entity</TableCell><TableCell>Area</TableCell><TableCell>Signal</TableCell><TableCell>Fusion</TableCell><TableCell>Evidence</TableCell><TableCell>Status</TableCell></TableRow></TableHead>
      <TableBody>{findings.map((f) => (
        <TableRow key={f.finding_id} hover sx={{ cursor: 'pointer' }} onClick={() => go(`/findings/${f.finding_id}`)}>
          <TableCell><PriorityChip p={f.priority} /></TableCell>
          <TableCell><Typography variant="body2" fontWeight={600}>{f.title}</Typography><Typography variant="caption" color="text.secondary">{f.finding_id} · {f.rule_id}</Typography></TableCell>
          <TableCell>{f.entity_name}</TableCell><TableCell>{f.area}</TableCell>
          <TableCell><Chip size="small" variant="outlined" label={TYPE_META[f.signal_type].label} /></TableCell>
          <TableCell sx={{ width: 110 }}><LinearProgress variant="determinate" value={f.fusion_score} /><Typography variant="caption">{f.fusion_score}</Typography></TableCell>
          <TableCell><ConfChip c={f.evidence_confidence} /><Typography variant="caption" display="block" color="text.secondary">{f.evidence_availability} evidence</Typography></TableCell>
          <TableCell><Typography variant="caption">{f.status}</Typography></TableCell>
        </TableRow>))}</TableBody></Table></TableContainer>);
}
