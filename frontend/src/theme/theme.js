import { createTheme, alpha } from '@mui/material/styles';
import colors from './colors';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: colors.primary,
    secondary: colors.secondary,
    background: colors.background,
    text: colors.text,
    error: { main: colors.status.critical },
    warning: { main: colors.status.warning },
    info: { main: colors.status.info },
    success: { main: colors.status.success },
  },
  typography: {
    fontFamily: '"Rajdhani", "Segoe UI", sans-serif',
    h1: { fontFamily: '"Orbitron", "Rajdhani", sans-serif', fontSize: '2.5rem', fontWeight: 700, color: colors.text.primary },
    h2: { fontFamily: '"Orbitron", "Rajdhani", sans-serif', fontSize: '2rem', fontWeight: 700, color: colors.text.primary },
    h3: { fontFamily: '"Orbitron", "Rajdhani", sans-serif', fontSize: '1.7rem', fontWeight: 700, color: colors.text.primary },
    h4: { fontFamily: '"Orbitron", "Rajdhani", sans-serif', fontSize: '1.4rem', fontWeight: 700, color: colors.text.primary },
    h5: { fontFamily: '"Orbitron", "Rajdhani", sans-serif', fontSize: '1.15rem', fontWeight: 700, color: colors.text.primary },
    h6: { fontFamily: '"Orbitron", "Rajdhani", sans-serif', fontSize: '1rem', fontWeight: 600, color: colors.text.primary },
    body1: { fontSize: '1rem', color: colors.text.primary, letterSpacing: '0.02em' },
    body2: { fontSize: '0.9rem', color: colors.text.secondary, letterSpacing: '0.02em' },
  },
  shape: {
    borderRadius: 14,
  },
  shadows: [
    'none',
    '0 2px 8px rgba(0, 229, 255, 0.12)',
    '0 4px 14px rgba(0, 229, 255, 0.14)',
    '0 8px 20px rgba(0, 229, 255, 0.18)',
    '0 12px 30px rgba(0, 229, 255, 0.2)',
    '0 16px 36px rgba(91, 140, 255, 0.25)',
    ...Array(19).fill('0 18px 42px rgba(91, 140, 255, 0.28)'),
  ],
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: colors.gradients.dark,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 700,
          borderRadius: 12,
          padding: '10px 22px',
        },
        contained: {
          background: colors.gradients.primary,
          color: colors.background.dark,
          boxShadow: `0 8px 18px ${alpha(colors.primary.main, 0.35)}`,
          '&:hover': {
            boxShadow: `0 10px 24px ${alpha(colors.primary.main, 0.45)}`,
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          background: `linear-gradient(145deg, ${alpha(colors.background.card, 0.92)} 0%, ${alpha(colors.background.paper, 0.9)} 100%)`,
          border: `1px solid ${alpha(colors.primary.main, 0.2)}`,
          boxShadow: `0 10px 22px ${alpha(colors.background.dark, 0.5)}`,
          backdropFilter: 'blur(10px)',
          '&:hover': {
            borderColor: alpha(colors.primary.main, 0.45),
            boxShadow: `0 14px 28px ${alpha(colors.primary.main, 0.2)}`,
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: alpha(colors.background.paper, 0.9),
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          fontWeight: 700,
          letterSpacing: '0.03em',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          height: 8,
          backgroundColor: alpha(colors.primary.main, 0.14),
        },
        bar: {
          background: colors.gradients.primary,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${alpha(colors.primary.main, 0.12)}`,
        },
        head: {
          backgroundColor: alpha(colors.primary.main, 0.12),
          color: colors.text.primary,
          fontWeight: 700,
        },
      },
    },
  },
});

export default theme;
