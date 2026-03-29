import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Badge,
  InputBase,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  AccountCircle,
  Logout,
  Settings,
  FolderOpen,
  SwapHoriz,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { alpha } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import colors from '../../theme/colors';

const Header = ({ onMenuClick, drawerWidth = 280, sidebarOpen = false, isMobile = false }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [notifAnchor, setNotifAnchor] = useState(null);
  const [currentCase, setCurrentCase] = useState(null);
  const [username, setUsername] = useState('');

  useEffect(() => {
    const caseData = localStorage.getItem('selectedCase');
    const user = localStorage.getItem('username');
    if (caseData) setCurrentCase(JSON.parse(caseData));
    if (user) setUsername(user);
  }, []);

  const handleProfileMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleNotifMenuOpen = (event) => setNotifAnchor(event.currentTarget);
  const handleMenuClose = () => {
    setAnchorEl(null);
    setNotifAnchor(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('selectedCase');
    navigate('/login');
  };

  const handleSwitchCase = () => {
    navigate('/case-selection');
    handleMenuClose();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return colors.status.info;
      case 'completed': return colors.status.success;
      case 'pending': return colors.status.warning;
      case 'processing': return colors.accent.cyan;
      default: return colors.text.secondary;
    }
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        left: !isMobile && sidebarOpen ? `${drawerWidth}px` : 0,
        width: !isMobile && sidebarOpen ? `calc(100% - ${drawerWidth}px)` : '100%',
        background: `linear-gradient(180deg, ${alpha(colors.background.dark, 0.95)} 0%, ${alpha(colors.background.paper, 0.88)} 100%)`,
        backdropFilter: 'blur(10px)',
        borderBottom: `1px solid ${alpha(colors.primary.main, 0.2)}`,
        zIndex: (theme) => theme.zIndex.drawer + 1,
        transition: 'left 0.3s ease, width 0.3s ease',
      }}
    >
      <Toolbar>
        <IconButton edge="start" onClick={onMenuClick} sx={{ mr: 2, color: colors.primary.main }}>
          <MenuIcon />
        </IconButton>

        <Box
          sx={{
            position: 'relative',
            borderRadius: 2,
            backgroundColor: alpha(colors.primary.main, 0.1),
            border: `1px solid ${alpha(colors.primary.main, 0.25)}`,
            '&:hover': { backgroundColor: alpha(colors.primary.main, 0.14) },
            width: { xs: '100%', sm: 'auto' },
            maxWidth: 420,
            flexGrow: { xs: 1, sm: 0 },
          }}
        >
          <Box
            sx={{
              px: 2,
              height: '100%',
              position: 'absolute',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SearchIcon sx={{ color: colors.primary.main }} />
          </Box>
          <InputBase
            placeholder="Search signals, cases, artifacts..."
            sx={{
              color: colors.text.primary,
              width: '100%',
              '& .MuiInputBase-input': {
                padding: '10px 12px 10px 48px',
                width: { xs: '100%', sm: '220px' },
                '&:focus': { width: { xs: '100%', sm: '320px' } },
              },
            }}
          />
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        {currentCase && (
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 1.5, mr: 2 }}>
            <Tooltip title="Current case context">
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  px: 1.5,
                  py: 0.75,
                  borderRadius: 2,
                  background: `linear-gradient(90deg, ${alpha(colors.primary.main, 0.18)} 0%, ${alpha(colors.accent.violet, 0.16)} 100%)`,
                  border: `1px solid ${alpha(colors.primary.main, 0.35)}`,
                }}
              >
                <FolderOpen sx={{ fontSize: 19, color: colors.primary.main }} />
                <Box>
                  <Typography variant="caption" color={colors.text.secondary} display="block" lineHeight={1}>
                    {currentCase.case_id}
                  </Typography>
                  <Typography variant="body2" fontWeight={700} color={colors.text.primary} lineHeight={1.2}>
                    {currentCase.title?.length > 24 ? `${currentCase.title.substring(0, 24)}...` : currentCase.title}
                  </Typography>
                </Box>
                <Chip
                  label={currentCase.status}
                  size="small"
                  sx={{
                    backgroundColor: alpha(getStatusColor(currentCase.status), 0.25),
                    color: getStatusColor(currentCase.status),
                    border: `1px solid ${alpha(getStatusColor(currentCase.status), 0.5)}`,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    height: 22,
                  }}
                />
              </Box>
            </Tooltip>
            <Tooltip title="Switch case">
              <IconButton onClick={handleSwitchCase} sx={{ color: colors.secondary.main }}>
                <SwapHoriz />
              </IconButton>
            </Tooltip>
          </Box>
        )}

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <motion.div whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.96 }}>
            <IconButton onClick={handleNotifMenuOpen} sx={{ color: colors.primary.main }}>
              <Badge badgeContent={3} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </motion.div>

          <motion.div whileHover={{ scale: 1.06 }} whileTap={{ scale: 0.96 }}>
            <IconButton edge="end" onClick={handleProfileMenuOpen} sx={{ ml: 0.5 }}>
              <Avatar
                sx={{
                  background: colors.gradients.primary,
                  color: colors.background.dark,
                  width: 36,
                  height: 36,
                  fontWeight: 800,
                }}
              >
                {username ? username.charAt(0).toUpperCase() : 'U'}
              </Avatar>
            </IconButton>
          </motion.div>
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          PaperProps={{ sx: { bgcolor: colors.background.paper, border: `1px solid ${alpha(colors.primary.main, 0.25)}` } }}
        >
          <Box sx={{ px: 2, py: 1, borderBottom: `1px solid ${alpha(colors.primary.main, 0.15)}` }}>
            <Typography variant="body2" fontWeight={700}>{username || 'User'}</Typography>
            <Typography variant="caption" color={colors.text.secondary}>Threat Analyst</Typography>
          </Box>
          <MenuItem onClick={handleMenuClose}><AccountCircle sx={{ mr: 2 }} />Profile</MenuItem>
          <MenuItem onClick={() => { handleMenuClose(); navigate('/settings'); }}><Settings sx={{ mr: 2 }} />Settings</MenuItem>
          <MenuItem onClick={handleSwitchCase}><SwapHoriz sx={{ mr: 2 }} />Switch Case</MenuItem>
          <MenuItem onClick={handleLogout} sx={{ color: colors.status.critical }}><Logout sx={{ mr: 2 }} />Logout</MenuItem>
        </Menu>

        <Menu
          anchorEl={notifAnchor}
          open={Boolean(notifAnchor)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          PaperProps={{ sx: { bgcolor: colors.background.paper, border: `1px solid ${alpha(colors.primary.main, 0.25)}` } }}
        >
          <MenuItem onClick={handleMenuClose}><Typography variant="body2">New evidence ingest completed</Typography></MenuItem>
          <MenuItem onClick={handleMenuClose}><Typography variant="body2">Anomaly score increased in case timeline</Typography></MenuItem>
          <MenuItem onClick={handleMenuClose}><Typography variant="body2">Executive report generated</Typography></MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
