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
  alpha,
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
import { useNavigate } from 'react-router-dom';
import colors from '../../theme/colors';

const Header = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [notifAnchor, setNotifAnchor] = useState(null);
  const [currentCase, setCurrentCase] = useState(null);
  const [username, setUsername] = useState('');

  useEffect(() => {
    // Load current case and username
    const caseData = localStorage.getItem('selectedCase');
    const user = localStorage.getItem('username');
    if (caseData) {
      setCurrentCase(JSON.parse(caseData));
    }
    if (user) {
      setUsername(user);
    }
  }, []);

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleNotifMenuOpen = (event) => {
    setNotifAnchor(event.currentTarget);
  };

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
      case 'active':
        return colors.status.info;
      case 'completed':
        return colors.status.success;
      case 'pending':
        return colors.status.warning;
      case 'processing':
        return colors.accent.cyan;
      default:
        return colors.text.secondary;
    }
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        background: 'white',
        borderBottom: `1px solid ${alpha(colors.primary.main, 0.1)}`,
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          onClick={onMenuClick}
          sx={{ mr: 2, color: colors.primary.main }}
        >
          <MenuIcon />
        </IconButton>

        {/* Search Bar */}
        <Box
          sx={{
            position: 'relative',
            borderRadius: 2,
            backgroundColor: alpha(colors.primary.main, 0.05),
            '&:hover': {
              backgroundColor: alpha(colors.primary.main, 0.08),
            },
            marginLeft: 0,
            width: { xs: '100%', sm: 'auto' },
            maxWidth: 400,
            flexGrow: { xs: 1, sm: 0 },
          }}
        >
          <Box
            sx={{
              padding: '0 16px',
              height: '100%',
              position: 'absolute',
              pointerEvents: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SearchIcon sx={{ color: colors.text.secondary }} />
          </Box>
          <InputBase
            placeholder="Search cases, artifacts..."
            sx={{
              color: 'inherit',
              width: '100%',
              '& .MuiInputBase-input': {
                padding: '10px 10px 10px 48px',
                transition: 'width 0.3s',
                width: { xs: '100%', sm: '200px' },
                '&:focus': {
                  width: { xs: '100%', sm: '300px' },
                },
              },
            }}
          />
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        {/* Current Case Info */}
        {currentCase && (
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 2, mr: 2 }}>
            <Tooltip title="Current Case">
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  px: 2,
                  py: 1,
                  borderRadius: 2,
                  background: `${colors.primary.main}10`,
                  border: `1px solid ${colors.primary.main}30`,
                }}
              >
                <FolderOpen sx={{ fontSize: 20, color: colors.primary.main }} />
                <Box>
                  <Typography variant="caption" color={colors.text.secondary} display="block" lineHeight={1}>
                    {currentCase.case_id}
                  </Typography>
                  <Typography variant="body2" fontWeight={600} color={colors.text.primary} lineHeight={1.2}>
                    {currentCase.title.length > 25 ? currentCase.title.substring(0, 25) + '...' : currentCase.title}
                  </Typography>
                </Box>
                <Chip
                  label={currentCase.status}
                  size="small"
                  sx={{
                    backgroundColor: getStatusColor(currentCase.status),
                    color: 'white',
                    fontWeight: 600,
                    fontSize: '0.7rem',
                    height: 20,
                    textTransform: 'uppercase',
                  }}
                />
              </Box>
            </Tooltip>
            <Tooltip title="Switch Case">
              <IconButton
                onClick={handleSwitchCase}
                sx={{
                  color: colors.primary.main,
                  '&:hover': {
                    background: `${colors.primary.main}10`,
                  },
                }}
              >
                <SwapHoriz />
              </IconButton>
            </Tooltip>
          </Box>
        )}

        {/* Right side icons */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.95 }}>
            <IconButton
              color="inherit"
              onClick={handleNotifMenuOpen}
              sx={{ color: colors.primary.main }}
            >
              <Badge badgeContent={3} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </motion.div>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <IconButton
              edge="end"
              onClick={handleProfileMenuOpen}
              sx={{ ml: 1 }}
            >
              <Avatar
                sx={{
                  bgcolor: colors.primary.main,
                  width: 36,
                  height: 36,
                }}
              >
                {username ? username.charAt(0).toUpperCase() : 'U'}
              </Avatar>
            </IconButton>
          </motion.div>
        </Box>

        {/* Profile Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <Box sx={{ px: 2, py: 1, borderBottom: `1px solid ${colors.background.lighter}` }}>
            <Typography variant="body2" fontWeight={600}>
              {username || 'User'}
            </Typography>
            <Typography variant="caption" color={colors.text.secondary}>
              Forensic Investigator
            </Typography>
          </Box>
          <MenuItem onClick={handleMenuClose}>
            <AccountCircle sx={{ mr: 2 }} />
            Profile
          </MenuItem>
          <MenuItem onClick={() => { handleMenuClose(); navigate('/settings'); }}>
            <Settings sx={{ mr: 2 }} />
            Settings
          </MenuItem>
          <MenuItem onClick={handleSwitchCase}>
            <SwapHoriz sx={{ mr: 2 }} />
            Switch Case
          </MenuItem>
          <MenuItem onClick={handleLogout} sx={{ color: colors.status.critical }}>
            <Logout sx={{ mr: 2 }} />
            Logout
          </MenuItem>
        </Menu>

        {/* Notifications Menu */}
        <Menu
          anchorEl={notifAnchor}
          open={Boolean(notifAnchor)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItem onClick={handleMenuClose}>
            <Typography variant="body2">New case assigned</Typography>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <Typography variant="body2">Analysis complete</Typography>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <Typography variant="body2">Report generated</Typography>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
