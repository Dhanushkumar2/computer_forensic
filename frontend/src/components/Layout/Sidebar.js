import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Dashboard as DashboardIcon,
  FolderOpen as CasesIcon,
  Storage as ArtifactsIcon,
  Timeline as TimelineIcon,
  Analytics as AnalyticsIcon,
  Description as ReportsIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  BugReport as AnomalyIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { alpha } from '@mui/material/styles';
import colors from '../../theme/colors';

const menuItems = [
  { text: 'Basic Info', icon: <SecurityIcon />, path: '/basic-info' },
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { text: 'Cases', icon: <CasesIcon />, path: '/cases' },
  { text: 'Artifacts', icon: <ArtifactsIcon />, path: '/artifacts' },
  { text: 'Timeline', icon: <TimelineIcon />, path: '/timeline' },
  { text: 'Analytics', icon: <AnalyticsIcon />, path: '/analytics' },
  { text: 'AI Anomaly Detection', icon: <AnomalyIcon />, path: '/anomaly-detection' },
  { text: 'Reports', icon: <ReportsIcon />, path: '/reports' },
  { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

const Sidebar = ({ open, onClose, isMobile, drawerWidth = 280 }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path) => {
    if (path === '/anomaly-detection') {
      const selectedCase = localStorage.getItem('selectedCase');
      if (selectedCase) {
        const caseData = JSON.parse(selectedCase);
        navigate(`/cases/${caseData.id}/anomaly-detection`);
      } else {
        navigate('/case-selection');
      }
    } else {
      navigate(path);
    }

    if (isMobile) {
      onClose();
    }
  };

  const drawerContent = (
    <Box
      sx={{
        height: '100%',
        background: colors.gradients.dark,
        color: colors.text.primary,
        display: 'flex',
        flexDirection: 'column',
        borderRight: `1px solid ${alpha(colors.primary.main, 0.2)}`,
      }}
    >
      <Box sx={{ p: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: 1.5,
            display: 'grid',
            placeItems: 'center',
            background: colors.gradients.primary,
            color: colors.background.dark,
            boxShadow: `0 0 18px ${alpha(colors.primary.main, 0.4)}`,
          }}
        >
          <SecurityIcon sx={{ fontSize: 28 }} />
        </Box>
        <Box>
          <Typography variant="h6" fontWeight={700} sx={{ lineHeight: 1.1 }}>
            CYBER FORENSICS
          </Typography>
          <Typography variant="caption" sx={{ color: colors.accent.emerald, letterSpacing: '0.08em' }}>
            INVESTIGATION GRID
          </Typography>
        </Box>
      </Box>

      <Divider sx={{ borderColor: alpha(colors.primary.main, 0.15) }} />

      <List sx={{ flexGrow: 1, px: 2, py: 3 }}>
        {menuItems.map((item, index) => {
          const isActive = item.path === '/anomaly-detection'
            ? location.pathname.includes('/anomaly-detection')
            : location.pathname === item.path;

          return (
            <motion.div
              key={item.text}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.04 }}
            >
              <ListItem disablePadding sx={{ mb: 1 }}>
                <ListItemButton
                  onClick={() => handleNavigation(item.path)}
                  sx={{
                    borderRadius: 2,
                    py: 1.2,
                    border: `1px solid ${isActive ? alpha(colors.primary.main, 0.4) : 'transparent'}`,
                    background: isActive
                      ? `linear-gradient(90deg, ${alpha(colors.primary.main, 0.24)} 0%, ${alpha(colors.accent.violet, 0.2)} 100%)`
                      : 'transparent',
                    '&:hover': {
                      background: isActive
                        ? `linear-gradient(90deg, ${alpha(colors.primary.main, 0.32)} 0%, ${alpha(colors.accent.violet, 0.26)} 100%)`
                        : alpha(colors.primary.main, 0.12),
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: isActive ? colors.primary.main : colors.text.secondary,
                      minWidth: 38,
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontWeight: isActive ? 700 : 500,
                      color: isActive ? colors.text.primary : colors.text.secondary,
                    }}
                  />
                </ListItemButton>
              </ListItem>
            </motion.div>
          );
        })}
      </List>

      <Box sx={{ p: 2.5, borderTop: `1px solid ${alpha(colors.primary.main, 0.15)}` }}>
        <Typography variant="caption" sx={{ color: colors.text.secondary }}>
          SOC Console v2.4.1
        </Typography>
      </Box>
    </Box>
  );

  return isMobile ? (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      sx={{ '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' } }}
    >
      {drawerContent}
    </Drawer>
  ) : (
    <Drawer
      variant="persistent"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          border: 'none',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
};

export default Sidebar;
