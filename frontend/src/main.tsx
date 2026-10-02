import { StrictMode, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, Route, Routes } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { makeTheme } from './theme';
import Shell from './components/Shell';
import * as P from './pages';

function App() {
  const [mode, setMode] = useState<'light' | 'dark'>(() => (localStorage.getItem('cl-mode') as 'light' | 'dark') || 'light');
  const theme = useMemo(() => makeTheme(mode), [mode]);
  return (
    <ThemeProvider theme={theme}><CssBaseline />
      <HashRouter><Routes>
        <Route element={<Shell toggle={() => setMode((m) => { const n = m === 'light' ? 'dark' : 'light'; localStorage.setItem('cl-mode', n); return n; })} />}>
          <Route index element={<P.Overview />} />
          <Route path="assessments" element={<P.Assessments />} />
          <Route path="queue" element={<P.ReviewQueue />} />
          <Route path="findings/:id" element={<P.FindingDetail />} />
          <Route path="lifecycle" element={<P.Lifecycle />} />
          <Route path="execution-gaps" element={<P.ExecutionGaps />} />
          <Route path="expected-evidence" element={<P.ExpectedEvidence />} />
          <Route path="negative-space" element={<P.NegativeSpace />} />
          <Route path="contradictions" element={<P.Contradictions />} />
          <Route path="anomalies" element={<P.Anomalies />} />
          <Route path="statistics" element={<P.Statistics />} />
          <Route path="peer" element={<P.Peer />} />
          <Route path="history" element={<P.Historical />} />
          <Route path="fusion" element={<P.Fusion />} />
          <Route path="evidence" element={<P.EvidenceExplorer />} />
          <Route path="sources" element={<P.SourceRecords />} />
          <Route path="reports" element={<P.Reports />} />
          <Route path="audit" element={<P.AuditTrail />} />
          <Route path="validation" element={<P.Validation />} />
        </Route>
      </Routes></HashRouter>
    </ThemeProvider>);
}
createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
