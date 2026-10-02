import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { AppBar, Box, Chip, Drawer, IconButton, List, ListItemButton, ListItemIcon, ListItemText, ListSubheader, Toolbar, Typography, useMediaQuery, Alert } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import MenuIcon from '@mui/icons-material/Menu';
import DarkModeOutlined from '@mui/icons-material/DarkModeOutlined';
import LightModeOutlined from '@mui/icons-material/LightModeOutlined';
import WifiOffOutlined from '@mui/icons-material/WifiOffOutlined';
import { NAV } from '../nav';
import { api } from '../services/api';

const W = 272;
export default function Shell({ toggle }: { toggle: () => void }) {
  const theme = useTheme(); const desktop = useMediaQuery(theme.breakpoints.up('md'));
  const [open, setOpen] = useState(false); const loc = useLocation(); const go = useNavigate();
  const drawer = (
    <Box sx={{ pb: 4 }}>
      <Toolbar><Typography variant="h6" fontWeight={800}>Cyber<span style={{ color: theme.palette.primary.main }}>Lens</span></Typography></Toolbar>
      {NAV.map((g) => (
        <List key={g.group} dense subheader={<ListSubheader sx={{ bgcolor: 'transparent', lineHeight: '30px', fontSize: 11, letterSpacing: '.06em', textTransform: 'uppercase' }}>{g.group}</ListSubheader>}>
          {g.items.map((i) => (
            <ListItemButton key={i.path} selected={i.path === '/' ? loc.pathname === '/' : loc.pathname.startsWith(i.path)} sx={{ mx: 1, borderRadius: 1.5 }}
              onClick={() => { go(i.path); setOpen(false); }}>
              <ListItemIcon sx={{ minWidth: 36 }}>{i.icon}</ListItemIcon><ListItemText primary={i.label} primaryTypographyProps={{ fontSize: 14 }} /></ListItemButton>))}
        </List>))}
    </Box>);
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" color="inherit" elevation={0} sx={{ ml: { md: `${W}px` }, width: { md: `calc(100% - ${W}px)` }, borderBottom: 1, borderColor: 'divider' }}>
        <Toolbar sx={{ gap: 1 }}>
          {!desktop && <IconButton onClick={() => setOpen(true)}><MenuIcon /></IconButton>}
          <Typography variant="subtitle2" color="text.secondary" sx={{ flex: 1 }}>Assessment 2026-Q3 · NCIIPC Supervisor</Typography>
          <Chip size="small" icon={<WifiOffOutlined />} color="success" variant="outlined" label={api.isMock ? 'Offline · mock data' : 'Offline · local backend'} />
          <IconButton onClick={toggle}>{theme.palette.mode === 'dark' ? <LightModeOutlined /> : <DarkModeOutlined />}</IconButton>
        </Toolbar>
      </AppBar>
      <Drawer variant={desktop ? 'permanent' : 'temporary'} open={desktop || open} onClose={() => setOpen(false)} sx={{ '& .MuiDrawer-paper': { width: W, boxSizing: 'border-box' } }}>{drawer}</Drawer>
      <Box component="main" sx={{ flex: 1, minWidth: 0, ml: { md: `${W}px` }, p: { xs: 2, md: 3 }, pt: { xs: 10, md: 11 }, maxWidth: 1500 }}>
        <Alert severity="info" variant="outlined" sx={{ mb: 2, py: 0 }}>CyberLens is decision support. Findings prioritize human review; they are not determinations. The supervisory decision rests with the examiner.</Alert>
        <Outlet />
      </Box>
    </Box>);
}
