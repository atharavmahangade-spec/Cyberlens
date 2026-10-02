import type { ReactNode } from 'react';
import type { SignalType } from './types';
import DashboardOutlined from '@mui/icons-material/DashboardOutlined';
import AssignmentOutlined from '@mui/icons-material/AssignmentOutlined';
import RateReviewOutlined from '@mui/icons-material/RateReviewOutlined';
import AccountTreeOutlined from '@mui/icons-material/AccountTreeOutlined';
import RuleOutlined from '@mui/icons-material/RuleOutlined';
import FactCheckOutlined from '@mui/icons-material/FactCheckOutlined';
import VisibilityOffOutlined from '@mui/icons-material/VisibilityOffOutlined';
import CompareArrowsOutlined from '@mui/icons-material/CompareArrowsOutlined';
import BubbleChartOutlined from '@mui/icons-material/BubbleChartOutlined';
import QueryStatsOutlined from '@mui/icons-material/QueryStatsOutlined';
import GroupsOutlined from '@mui/icons-material/GroupsOutlined';
import TimelineOutlined from '@mui/icons-material/TimelineOutlined';
import HubOutlined from '@mui/icons-material/HubOutlined';
import SearchOutlined from '@mui/icons-material/SearchOutlined';
import StorageOutlined from '@mui/icons-material/StorageOutlined';
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined';
import HistoryOutlined from '@mui/icons-material/HistoryOutlined';
import VerifiedOutlined from '@mui/icons-material/VerifiedOutlined';

export interface NavItem { label: string; path: string; icon: ReactNode }
export const NAV: { group: string; items: NavItem[] }[] = [
  { group: 'Overview', items: [
    { label: 'Overview', path: '/', icon: <DashboardOutlined /> },
    { label: 'Assessments', path: '/assessments', icon: <AssignmentOutlined /> },
    { label: 'Review Queue', path: '/queue', icon: <RateReviewOutlined /> }] },
  { group: 'Supervisory Intelligence', items: [
    { label: 'Lifecycle Intelligence', path: '/lifecycle', icon: <AccountTreeOutlined /> },
    { label: 'Execution Gaps', path: '/execution-gaps', icon: <RuleOutlined /> },
    { label: 'Expected Evidence', path: '/expected-evidence', icon: <FactCheckOutlined /> },
    { label: 'Negative Space', path: '/negative-space', icon: <VisibilityOffOutlined /> },
    { label: 'Capability–Evidence Analysis', path: '/contradictions', icon: <CompareArrowsOutlined /> }] },
  { group: 'Behaviour Analytics', items: [
    { label: 'Anomalies', path: '/anomalies', icon: <BubbleChartOutlined /> },
    { label: 'Statistical Analysis', path: '/statistics', icon: <QueryStatsOutlined /> }] },
  { group: 'Context & Comparison', items: [
    { label: 'Peer Comparison', path: '/peer', icon: <GroupsOutlined /> },
    { label: 'Historical Benchmarking', path: '/history', icon: <TimelineOutlined /> },
    { label: 'Signal Fusion', path: '/fusion', icon: <HubOutlined /> }] },
  { group: 'Evidence', items: [
    { label: 'Evidence Explorer', path: '/evidence', icon: <SearchOutlined /> },
    { label: 'Source Records', path: '/sources', icon: <StorageOutlined /> }] },
  { group: 'Reporting & Audit', items: [
    { label: 'Reports', path: '/reports', icon: <DescriptionOutlined /> },
    { label: 'Audit Trail', path: '/audit', icon: <HistoryOutlined /> }] },
  { group: 'Validation', items: [{ label: 'Expert Validation', path: '/validation', icon: <VerifiedOutlined /> }] },
];
export const TYPE_META: Record<SignalType, { label: string; path: string }> = {
  execution_gap: { label: 'Execution gap', path: '/execution-gaps' },
  negative_space: { label: 'Negative space', path: '/negative-space' },
  anomaly: { label: 'Anomaly', path: '/anomalies' },
  peer_deviation: { label: 'Peer deviation', path: '/peer' },
  lifecycle: { label: 'Lifecycle', path: '/lifecycle' },
  monitoring: { label: 'Monitoring / coverage', path: '/execution-gaps' },
  contradiction: { label: 'Capability–evidence', path: '/contradictions' },
  statistical: { label: 'Statistical', path: '/statistics' },
};
