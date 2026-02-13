import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  Search,
  Language,
  Storage,
  Usb,
  Event,
  Delete,
  Timeline,
  Apps,
  TrendingUp,
  Refresh,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import colors from '../../theme/colors';
import { forensicAPI } from '../../services/api';
import ReExtractButton from '../../components/Extraction/ReExtractButton';

const Artifacts = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [artifacts, setArtifacts] = useState({
    browser: [],
    registry: [],
    filesystem: [],
    usb: [],
    events: [],
    deleted: [],
    programs: [],
    activity: [],
  });
  const [stats, setStats] = useState({
    browser: 0,
    registry: 0,
    filesystem: 0,
    usb: 0,
    events: 0,
    deleted: 0,
    programs: 0,
    activity: 0,
  });

  const artifactTypes = [
    { label: 'All Artifacts', icon: <Apps />, key: 'all', color: colors.primary.main },
    { label: 'Browser', icon: <Language />, key: 'browser', color: colors.artifacts.browser },
    { label: 'Registry', icon: <Storage />, key: 'registry', color: colors.artifacts.registry },
    { label: 'USB Devices', icon: <Usb />, key: 'usb', color: colors.artifacts.usb },
    { label: 'Events', icon: <Event />, key: 'events', color: colors.artifacts.events },
    { label: 'Deleted Files', icon: <Delete />, key: 'deleted', color: colors.artifacts.deleted },
    { label: 'Programs', icon: <Apps />, key: 'programs', color: colors.artifacts.programs },
    { label: 'Activity', icon: <TrendingUp />, key: 'activity', color: colors.artifacts.activity },
  ];

  useEffect(() => {
    fetchArtifacts();
  }, []);

  const fetchArtifacts = async () => {
    setLoading(true);
    try {
      // Get current case from localStorage
      const currentCase = JSON.parse(localStorage.getItem('selectedCase') || '{}');
      
      if (!currentCase.id) {
        console.error('No case selected');
        setLoading(false);
        return;
      }
      
      // Fetch statistics from MongoDB
      const statsRes = await forensicAPI.getStatistics(currentCase.id);
      const mongoStats = statsRes.data;
      
      // Update stats with real data from MongoDB
      const realStats = {
        browser: mongoStats.browser_artifacts || 0,
        registry: mongoStats.registry_artifacts || 0,
        filesystem: mongoStats.filesystem_artifacts || 0,
        usb: mongoStats.usb_devices || 0,
        events: mongoStats.event_logs || 0,
        deleted: mongoStats.deleted_files || 0,
        programs: mongoStats.installed_programs || 0,
        activity: mongoStats.user_activity || 0,
      };
      
      setStats(realStats);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching artifacts:', error);
      // Fallback to mock data if API fails
      const mockStats = {
        browser: 1247,
        registry: 856,
        filesystem: 3421,
        usb: 12,
        events: 5678,
        deleted: 234,
        programs: 145,
        activity: 2890,
      };
      setStats(mockStats);
      setLoading(false);
    }
  };

  const handleExtractionComplete = (artifactsCount) => {
    // Refresh artifacts after extraction completes
    fetchArtifacts();
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getArtifactIcon = (type) => {
    const artifact = artifactTypes.find(a => a.key === type);
    return artifact ? artifact.icon : <Apps />;
  };

  const getArtifactColor = (type) => {
    const artifact = artifactTypes.find(a => a.key === type);
    return artifact ? artifact.color : colors.primary.main;
  };

  // Get current case ID
  const currentCase = JSON.parse(localStorage.getItem('selectedCase') || '{}');

  const renderArtifactCard = (type, count) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      whileHover={{ scale: 1.02 }}
    >
      <Card
        sx={{
          cursor: 'pointer',
          background: `linear-gradient(135deg, ${getArtifactColor(type)}15 0%, ${getArtifactColor(type)}05 100%)`,
          border: `2px solid ${getArtifactColor(type)}30`,
          '&:hover': {
            border: `2px solid ${getArtifactColor(type)}`,
          },
        }}
        onClick={() => {
          const index = artifactTypes.findIndex(a => a.key === type);
          if (index !== -1) setActiveTab(index);
        }}
      >
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={2}>
              <Box
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: 2,
                  background: `linear-gradient(135deg, ${getArtifactColor(type)} 0%, ${getArtifactColor(type)}CC 100%)`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                }}
              >
                {getArtifactIcon(type)}
              </Box>
              <Box>
                <Typography variant="h6" fontWeight={600} color={colors.text.primary}>
                  {artifactTypes.find(a => a.key === type)?.label}
                </Typography>
                <Typography variant="body2" color={colors.text.secondary}>
                  {count.toLocaleString()} items
                </Typography>
              </Box>
            </Box>
            <Chip
              label={count.toLocaleString()}
              sx={{
                backgroundColor: getArtifactColor(type),
                color: 'white',
                fontWeight: 600,
                fontSize: '1rem',
              }}
            />
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );

  const renderArtifactTable = (type) => {
    // Mock data for demonstration
    const mockData = {
      browser: [
        { id: 1, url: 'https://example.com', title: 'Example Site', visits: 45, lastVisit: '2024-11-24 10:30' },
        { id: 2, url: 'https://github.com', title: 'GitHub', visits: 123, lastVisit: '2024-11-24 09:15' },
        { id: 3, url: 'https://stackoverflow.com', title: 'Stack Overflow', visits: 67, lastVisit: '2024-11-23 16:45' },
      ],
      usb: [
        { id: 1, device: 'SanDisk USB 3.0', serial: 'ABC123456', firstConnect: '2024-11-20 14:30', lastConnect: '2024-11-24 08:00' },
        { id: 2, device: 'Kingston DataTraveler', serial: 'XYZ789012', firstConnect: '2024-11-15 09:00', lastConnect: '2024-11-22 17:30' },
      ],
      deleted: [
        { id: 1, filename: 'document.pdf', path: 'C:\\Users\\John\\Documents', size: '2.4 MB', deletedDate: '2024-11-23 11:20' },
        { id: 2, filename: 'image.jpg', path: 'C:\\Users\\John\\Pictures', size: '1.8 MB', deletedDate: '2024-11-22 15:45' },
      ],
    };

    const data = mockData[type] || [];

    if (data.length === 0) {
      return (
        <Box textAlign="center" py={8}>
          <Typography variant="h6" color={colors.text.secondary}>
            No {type} artifacts found
          </Typography>
        </Box>
      );
    }

    return (
      <TableContainer component={Paper} elevation={0}>
        <Table>
          <TableHead>
            <TableRow>
              {Object.keys(data[0]).filter(k => k !== 'id').map((key) => (
                <TableCell key={key}>
                  <Typography variant="body2" fontWeight={600} textTransform="capitalize">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </Typography>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, index) => (
              <motion.tr
                key={row.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                component={TableRow}
                sx={{
                  '&:hover': {
                    backgroundColor: colors.background.hover,
                  },
                }}
              >
                {Object.entries(row).filter(([key]) => key !== 'id').map(([key, value]) => (
                  <TableCell key={key}>
                    <Typography variant="body2">{value}</Typography>
                  </TableCell>
                ))}
              </motion.tr>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" fontWeight={700} color={colors.text.primary}>
              Forensic Artifacts
            </Typography>
            <Typography variant="body1" color={colors.text.secondary} sx={{ mt: 1 }}>
              Comprehensive view of all collected digital evidence
            </Typography>
          </Box>
          <Box display="flex" gap={2}>
            {currentCase.id && (
              <ReExtractButton 
                caseId={currentCase.id} 
                onExtractionComplete={handleExtractionComplete}
              />
            )}
            <Tooltip title="Refresh artifacts">
              <IconButton
                onClick={fetchArtifacts}
                sx={{
                  background: colors.gradients.primary,
                  color: 'white',
                  '&:hover': {
                    background: colors.gradients.primary,
                    transform: 'rotate(180deg)',
                  },
                }}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
        >
          <TextField
            fullWidth
            placeholder="Search artifacts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search sx={{ color: colors.primary.main }} />
                </InputAdornment>
              ),
            }}
            sx={{
              mb: 4,
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'white',
                '&:hover': {
                  boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.08)',
                },
              },
            }}
          />
        </motion.div>
      </motion.div>

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Artifact Cards Grid */}
      {activeTab === 0 && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {Object.entries(stats).map(([type, count], index) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={type}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
              >
                {renderArtifactCard(type, count)}
              </motion.div>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Tabs */}
      <Paper elevation={0} sx={{ mb: 3, borderRadius: 2 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              fontWeight: 600,
              textTransform: 'none',
              minHeight: 64,
            },
            '& .Mui-selected': {
              color: colors.primary.main,
            },
          }}
        >
          {artifactTypes.map((type, index) => (
            <Tab
              key={type.key}
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  {type.icon}
                  <span>{type.label}</span>
                  {type.key !== 'all' && (
                    <Chip
                      label={stats[type.key]?.toLocaleString() || 0}
                      size="small"
                      sx={{
                        backgroundColor: activeTab === index ? type.color : colors.background.lighter,
                        color: activeTab === index ? 'white' : colors.text.secondary,
                        fontWeight: 600,
                      }}
                    />
                  )}
                </Box>
              }
            />
          ))}
        </Tabs>
      </Paper>

      {/* Artifact Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab > 0 && (
            <Paper elevation={0} sx={{ p: 3, borderRadius: 2 }}>
              {renderArtifactTable(artifactTypes[activeTab].key)}
            </Paper>
          )}
        </motion.div>
      </AnimatePresence>
    </Box>
  );
};

export default Artifacts;
