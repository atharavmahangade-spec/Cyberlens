import { useEffect, useState, type ReactNode } from 'react';
import { Alert, Box, Chip, CircularProgress, MenuItem, Paper, TextField, Typography } from '@mui/material';
import type { Confidence, Priority } from '../types';
import { api } from '../services/api';
import Chart from './Chart';

export function useApi<V>(fn: () => Promise<V>, deps: unknown[] = []) {
  const [s, set] = useState<{ data?: V; loading: boolean; error?: string }>({ loading: true });
  useEffect(() => {
    let ok = true;
    set((p) => ({ ...p, loading: true }));
    fn().then((d) => ok && set({ data: d, loading: false })).catch((e) => ok && set({ loading: false, error: String(e) }));
    return () => { ok = false; };
  }, deps);
  return s;
}
export function Async<V>({ s, children }: { s: { data?: V; loading: boolean; error?: string }; children: (d: V) => ReactNode }) {
  if (s.error) return <Alert severity="error">Could not load data: {s.error}</Alert>;
  if (s.data === undefined) return <Box sx={{ p: 6, textAlign: 'center' }}><CircularProgress size={28} /></Box>;
  return <>{children(s.data)}</>;
}
export const PageHeader = ({ title, sub, action }: { title: string; sub?: string; action?: ReactNode }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2, mb: 2.5, flexWrap: 'wrap' }}>
    <Box><Typography variant="h5" fontWeight={700}>{title}</Typography>{sub && <Typography color="text.secondary" sx={{ maxWidth: 820 }}>{sub}</Typography>}</Box>{action}
  </Box>);
export const Panel = ({ title, children, sx }: { title?: string; children: ReactNode; sx?: object }) => (
  <Paper variant="outlined" sx={{ p: 2, minWidth: 0, ...sx }}>
    {title && <Typography variant="overline" color="text.secondary" fontWeight={700} sx={{ display: 'block', mb: 1 }}>{title}</Typography>}{children}</Paper>);
export const ChartPanel = ({ title, option, height }: { title: string; option: Parameters<typeof Chart>[0]['option']; height?: number }) =>
  <Panel title={title}><Chart option={option} height={height} /></Panel>;
export const Grid = ({ min = 320, children, sx }: { min?: number; children: ReactNode; sx?: object }) => (
  <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: `repeat(auto-fit,minmax(min(${min}px,100%),1fr))`, mb: 2, ...sx }}>{children}</Box>);
export const Kpi = ({ label, value, sub, color }: { label: string; value: ReactNode; sub?: string; color?: string }) => (
  <Paper variant="outlined" sx={{ p: 2 }}><Typography variant="h4" fontWeight={700} sx={{ color }}>{value}</Typography>
    <Typography color="text.secondary" variant="body2">{label}</Typography>{sub && <Typography variant="caption" color="text.secondary">{sub}</Typography>}</Paper>);
export const PriorityChip = ({ p }: { p: Priority }) => <Chip size="small" label={p} color={p === 'High' ? 'error' : p === 'Medium' ? 'warning' : 'success'} />;
export const ConfChip = ({ c }: { c: Confidence }) => <Chip size="small" variant="outlined" label={`${c} confidence`} color={c === 'High' ? 'success' : c === 'Medium' ? 'warning' : 'default'} />;
export function EntitySelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const s = useApi(() => api.getEntities(), []);
  return <TextField select size="small" label="Entity" value={value} onChange={(e) => onChange(e.target.value)} sx={{ minWidth: 240 }}>
    {(s.data ?? []).map((e) => <MenuItem key={e.entity_id} value={e.entity_id}>{e.name}</MenuItem>)}</TextField>;
}
export const Empty = ({ text }: { text: string }) => <Alert severity="info" variant="outlined">{text}</Alert>;
export const fmt = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
