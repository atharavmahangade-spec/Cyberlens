import { createTheme } from '@mui/material/styles';
export const makeTheme = (mode: 'light' | 'dark') => createTheme({
  palette: { mode, primary: { main: mode === 'dark' ? '#3cc0e0' : '#0b6e8a' },
    background: mode === 'dark' ? { default: '#0c121a', paper: '#141c27' } : { default: '#f4f6f9', paper: '#ffffff' } },
  shape: { borderRadius: 10 },
  typography: { fontFamily: 'Inter, "Segoe UI", system-ui, -apple-system, Roboto, sans-serif' },
  components: { MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } }, MuiTableCell: { styleOverrides: { head: { fontWeight: 700 } } } },
});
