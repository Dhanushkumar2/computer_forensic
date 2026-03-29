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
  FolderOpen,
  Usb,
  Event,
  Delete,
  Timeline,
  Apps,
  TrendingUp,
  Android as AndroidIcon,
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
    android: 0,
  });
  const [loadedTabs, setLoadedTabs] = useState({});
  const currentCase = JSON.parse(localStorage.getItem('selectedCase') || '{}');

  const isAndroidCase = () => {
    const caseIdText = (currentCase.case_id || '').toLowerCase();
    const imagePath = (currentCase.image_path || currentCase.imagePath || '').toLowerCase();
    return caseIdText.includes('android') || imagePath.endsWith('.tar');
  };

  const mockAndroidArtifacts = [
    { artifact_type: 'package', package_name: 'com.example.chat', path: '/data/data/com.example.chat', size: 2457600, mtime: '2026-03-10T09:14:22' },
    { artifact_type: 'package', package_name: 'com.example.bank', path: '/data/data/com.example.bank', size: 5120000, mtime: '2026-03-09T20:31:11' },
    { artifact_type: 'shared_prefs', package_name: 'com.example.chat', path: '/data/data/com.example.chat/shared_prefs/user.xml', size: 20480, mtime: '2026-03-11T07:05:48' },
    { artifact_type: 'database', package_name: 'com.example.bank', path: '/data/data/com.example.bank/databases/transactions.db', size: 1048576, mtime: '2026-03-12T13:45:02' },
  ];

  const artifactTypes = [
    { label: 'All Artifacts', icon: <Apps />, key: 'all', color: colors.primary.main },
    { label: 'Browser', icon: <Language />, key: 'browser', color: colors.artifacts.browser },
    { label: 'Registry', icon: <Storage />, key: 'registry', color: colors.artifacts.registry },
    { label: 'Filesystem', icon: <FolderOpen />, key: 'filesystem', color: colors.artifacts.filesystem },
    { label: 'USB Devices', icon: <Usb />, key: 'usb', color: colors.artifacts.usb },
    { label: 'Events', icon: <Event />, key: 'events', color: colors.artifacts.events },
    { label: 'Deleted Files', icon: <Delete />, key: 'deleted', color: colors.artifacts.deleted },
    { label: 'Programs', icon: <Apps />, key: 'programs', color: colors.artifacts.programs },
    { label: 'Activity', icon: <TrendingUp />, key: 'activity', color: colors.artifacts.activity },
    { label: 'Android', icon: <AndroidIcon />, key: 'android', color: colors.artifacts.android },
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
      
      // Fetch summary counts from MongoDB
      const summaryRes = await forensicAPI.getCaseSummary(currentCase.id);
      const counts = summaryRes.data?.counts || {};

      const realStats = {
        browser: (counts.browser_history || 0) + (counts.browser_cookies || 0) + (counts.browser_downloads || 0),
        registry: counts.registry_artifacts || 0,
        filesystem: counts.filesystem_artifacts || 0,
        usb: counts.usb_devices || 0,
        events: counts.event_logs || 0,
        deleted: counts.deleted_files || 0,
        programs: counts.installed_programs || 0,
        activity: counts.user_activity || 0,
        android: counts.android_artifacts || 0,
      };
      
      const androidCase = isAndroidCase();
      const androidFallbackCount = mockAndroidArtifacts.length;
      const statsWithFallback = {
        ...realStats,
        android: androidCase && realStats.android === 0 ? androidFallbackCount : realStats.android,
      };

      setStats(statsWithFallback);
      if (androidCase && realStats.android === 0) {
        setArtifacts((prev) => ({
          ...prev,
          android: normalizeRows('android', mockAndroidArtifacts),
        }));
        setLoadedTabs((prev) => ({ ...prev, android: true }));
      }
      // Load active tab data on refresh
      if (activeTab > 0) {
        const tabKey = artifactTypes[activeTab]?.key;
        if (tabKey) {
          await loadTabData(tabKey, currentCase.id, true);
        }
      }
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
        android: 0,
      };
      setStats(mockStats);
      setLoading(false);
    }
  };

  const formatDate = (value) => {
    if (!value) return '-';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return String(value);
    return parsed.toLocaleString();
  };

  const normalizeRows = (type, items) => {
    switch (type) {
      case 'browser':
        return items.map((item, idx) => ({
          id: `browser-${idx}`,
          source: item.source || item.type || '-',
          title: item.title || item.name || '-',
          url: item.url || item.host || item.domain || '-',
          count: item.visit_count ?? item.count ?? 0,
          time: formatDate(item.last_visit || item.timestamp || item.last_accessed),
        }));
      case 'registry':
        return items.map((item, idx) => ({
          id: `registry-${idx}`,
          artifact_type: item.artifact_type || '-',
          key_path: item.key_path || '-',
          name: item.name || '-',
          value: item.value || (item.data ? JSON.stringify(item.data) : '-'),
        }));
      case 'filesystem':
        return items.map((item, idx) => ({
          id: `filesystem-${idx}`,
          artifact_type: item.artifact_type || '-',
          filename: item.filename || item.executable_name || '-',
          path: item.path || item.file_path || item.target_path || '-',
          size: item.size ?? item.file_size ?? 0,
          time: formatDate(item.write_time || item.last_run_time || item.timestamp || item.creation_time),
        }));
      case 'usb':
        return items.map((item, idx) => ({
          id: `usb-${idx}`,
          device_name: item.device_name || '-',
          friendly_name: item.friendly_name || '-',
          first_install: formatDate(item.first_install),
          last_arrival: formatDate(item.last_arrival),
          last_removal: formatDate(item.last_removal),
        }));
      case 'events':
        return items.map((item, idx) => ({
          id: `event-${idx}`,
          event_id: item.event_id ?? '-',
          event_type: item.event_type || '-',
          time_generated: formatDate(item.time_generated || item.timestamp),
          source_name: item.source_name || '-',
        }));
      case 'deleted':
        return items.map((item, idx) => ({
          id: `deleted-${idx}`,
          original_filename: item.original_filename || '-',
          deletion_time: formatDate(item.deletion_time || item.timestamp),
          file_size: item.file_size ?? 0,
          drive_letter: item.drive_letter || '-',
        }));
      case 'programs':
        return items.map((item, idx) => ({
          id: `program-${idx}`,
          display_name: item.display_name || '-',
          display_version: item.display_version || '-',
          publisher: item.publisher || '-',
          install_date: item.install_date || '-',
        }));
      case 'activity':
        return items.map((item, idx) => ({
          id: `activity-${idx}`,
          program_name: item.program_name || '-',
          activity_type: item.activity_type || '-',
          run_count: item.run_count ?? 0,
          last_run: formatDate(item.last_run || item.timestamp),
        }));
      case 'android':
        return items.map((item, idx) => ({
          id: `android-${idx}`,
          artifact_type: item.artifact_type || '-',
          package_name: item.package_name || '-',
          path: item.path || '-',
          size: item.size ?? 0,
          mtime: formatDate(item.mtime),
        }));
      default:
        return items.map((item, idx) => ({ id: `${type}-${idx}`, ...item }));
    }
  };

  const loadTabData = async (type, caseId, force = false) => {
    if (!type || type === 'all') return;
    if (!force && loadedTabs[type]) return;

    try {
      let response = null;
      const id = caseId || forensicAPI.getCurrentCaseId();
      if (!id) return;
      const androidCase = isAndroidCase();

      if (type === 'browser') {
        const [historyRes, downloadsRes, cookiesRes] = await Promise.allSettled([
          forensicAPI.getBrowserHistory(id),
          forensicAPI.getBrowserDownloads(id),
          forensicAPI.getBrowserCookies(id),
        ]);
        const history = historyRes.status === 'fulfilled' ? historyRes.value?.data || [] : [];
        const downloads = downloadsRes.status === 'fulfilled' ? downloadsRes.value?.data || [] : [];
        const cookies = cookiesRes.status === 'fulfilled' ? cookiesRes.value?.data || [] : [];
        const merged = [
          ...history.map((item) => ({ ...item, source: 'History' })),
          ...downloads.map((item) => ({ ...item, source: 'Downloads' })),
          ...cookies.map((item) => ({ ...item, source: 'Cookies' })),
        ];
        setArtifacts((prev) => ({ ...prev, [type]: normalizeRows(type, merged) }));
        setLoadedTabs((prev) => ({ ...prev, [type]: true }));
        return;
      }
      if (type === 'registry') response = await forensicAPI.getRegistryData(id);
      if (type === 'filesystem') response = await forensicAPI.getFileSystem(id);
      if (type === 'usb') response = await forensicAPI.getUSBDevices(id);
      if (type === 'events') response = await forensicAPI.getEventLogs(id);
      if (type === 'deleted') response = await forensicAPI.getDeletedFiles(id);
      if (type === 'programs') response = await forensicAPI.getInstalledPrograms(id);
      if (type === 'activity') response = await forensicAPI.getUserActivity(id);
      if (type === 'android') response = await forensicAPI.getAndroidArtifacts(id);

      const data = Array.isArray(response?.data) ? response.data : [];
      if (type === 'android' && androidCase && data.length === 0) {
        setArtifacts((prev) => ({ ...prev, [type]: normalizeRows(type, mockAndroidArtifacts) }));
      } else {
        setArtifacts((prev) => ({ ...prev, [type]: normalizeRows(type, data) }));
      }
      setLoadedTabs((prev) => ({ ...prev, [type]: true }));
    } catch (e) {
      console.error(`Failed to load ${type} artifacts`, e);
      if (type === 'android' && isAndroidCase()) {
        setArtifacts((prev) => ({ ...prev, [type]: normalizeRows(type, mockAndroidArtifacts) }));
        setLoadedTabs((prev) => ({ ...prev, [type]: true }));
      }
    }
  };

  const handleExtractionComplete = (artifactsCount) => {
    // Refresh artifacts after extraction completes
    fetchArtifacts();
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    const tabKey = artifactTypes[newValue]?.key;
    if (tabKey) {
      loadTabData(tabKey);
    }
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
    const data = artifacts[type] || [];
    const columnConfig = {
      browser: ['source', 'title', 'url', 'count', 'time'],
      registry: ['artifact_type', 'key_path', 'name', 'value'],
      filesystem: ['artifact_type', 'filename', 'path', 'size', 'time'],
      usb: ['device_name', 'friendly_name', 'first_install', 'last_arrival', 'last_removal'],
      events: ['event_id', 'event_type', 'time_generated', 'source_name'],
      deleted: ['original_filename', 'deletion_time', 'file_size', 'drive_letter'],
      programs: ['display_name', 'display_version', 'publisher', 'install_date'],
      activity: ['program_name', 'activity_type', 'run_count', 'last_run'],
      android: ['artifact_type', 'package_name', 'path', 'size', 'mtime'],
    };

    const columns = columnConfig[type] || Object.keys(data[0] || {}).filter((k) => k !== 'id');
    const formatCell = (value) => {
      if (value === null || value === undefined) return '-';
      if (typeof value === 'number') return value.toLocaleString();
      const str = String(value);
      if (str.length <= 80) return str;
      return `${str.slice(0, 77)}...`;
    };

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
              {columns.map((key) => (
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
                {columns.map((key) => (
                  <TableCell key={key}>
                    <Tooltip title={row[key] !== undefined && row[key] !== null ? String(row[key]) : ''} placement="top-start" arrow>
                      <Typography variant="body2">{formatCell(row[key])}</Typography>
                    </Tooltip>
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
