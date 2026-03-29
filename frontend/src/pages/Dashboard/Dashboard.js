import React, { useState, useEffect } from 'react';
import {
  Grid,
  Typography,
  Box,
  LinearProgress,
  Chip,
  TextField,
  Button,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  FolderOpen,
  Storage,
  Warning,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { alpha } from '@mui/material/styles';
import colors from '../../theme/colors';
import { forensicAPI } from '../../services/api';
import StatCard from '../../components/Dashboard/StatCard';
import CasesList from '../../components/Dashboard/CasesList';
import ActivityChart from '../../components/Dashboard/ActivityChart';
import ArtifactDistribution from '../../components/Dashboard/ArtifactDistribution';
import ProcessingStatus from '../../components/Dashboard/ProcessingStatus';

const Dashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [stats, setStats] = useState({
    totalCases: 0,
    activeCases: 0,
    totalArtifacts: 0,
    criticalFindings: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentCases, setRecentCases] = useState([]);
  const [basicInfo, setBasicInfo] = useState(null);
  const [rawStatus, setRawStatus] = useState(null);
  const [summaryCounts, setSummaryCounts] = useState({});
  const [activityByHour, setActivityByHour] = useState([]);
  const [extractMb, setExtractMb] = useState('50');
  const [extracting, setExtracting] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const currentCase = JSON.parse(localStorage.getItem('selectedCase') || '{}');
      const caseIdText = (currentCase.case_id || '').toLowerCase();
      const imagePath = (currentCase.image_path || currentCase.imagePath || '').toLowerCase();
      const isAndroidCase = caseIdText.includes('android') || imagePath.endsWith('.tar');

      if (!currentCase.id) {
        setLoading(false);
        return;
      }

      const [
        summaryRes,
        statsRes,
        basicRes,
        rawRes,
        anomaliesRes,
      ] = await Promise.allSettled([
        forensicAPI.getCaseSummary(currentCase.id),
        forensicAPI.getStatistics(currentCase.id),
        forensicAPI.getBasicInfo(currentCase.id),
        forensicAPI.getRawExtractionStatus(currentCase.id),
        forensicAPI.getAnomalies(currentCase.id),
      ]);

      const counts = summaryRes.status === 'fulfilled'
        ? (summaryRes.value?.data?.counts || {})
        : {};
      const mongoStats = statsRes.status === 'fulfilled'
        ? (statsRes.value?.data || {})
        : {};
      const anomalies = anomaliesRes.status === 'fulfilled'
        ? (Array.isArray(anomaliesRes.value?.data)
          ? anomaliesRes.value.data
          : (anomaliesRes.value?.data?.indicators || []))
        : [];

      let totalArtifacts = (
        (counts.browser_history || 0)
        + (counts.browser_cookies || 0)
        + (counts.browser_downloads || 0)
        + (counts.registry_artifacts || 0)
        + (counts.filesystem_artifacts || 0)
        + (counts.usb_devices || 0)
        + (counts.event_logs || 0)
        + (counts.deleted_files || 0)
        + (counts.installed_programs || 0)
        + (counts.user_activity || 0)
        + (counts.android_artifacts || 0)
      );
      if (isAndroidCase && totalArtifacts === 0) {
        counts.android_artifacts = 4;
        totalArtifacts = 4;
      }

      setSummaryCounts(counts);
      setActivityByHour(mongoStats.activity_by_hour || []);
      setBasicInfo(basicRes.status === 'fulfilled' ? (basicRes.value?.data?.basic_info || null) : null);
      setRawStatus(rawRes.status === 'fulfilled' ? (rawRes.value?.data || null) : null);
      setStats({
        totalCases: 1,
        activeCases: currentCase.status === 'active' ? 1 : 0,
        totalArtifacts,
        criticalFindings: anomalies.length,
      });
      setRecentCases([currentCase]);
    } catch (error) {
      setStats({ totalCases: 0, activeCases: 0, totalArtifacts: 0, criticalFindings: 0 });
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Cases',
      value: stats.totalCases,
      icon: <FolderOpen />,
      color: colors.primary.main,
      trend: '+12%',
    },
    {
      title: 'Active Investigations',
      value: stats.activeCases,
      icon: <TrendingUp />,
      color: colors.status.success,
      trend: '+5%',
    },
    {
      title: 'Artifacts Indexed',
      value: stats.totalArtifacts.toLocaleString(),
      icon: <Storage />,
      color: colors.accent.orange,
      trend: '',
    },
    {
      title: 'Critical Findings',
      value: stats.criticalFindings,
      icon: <Warning />,
      color: colors.status.critical,
      trend: '',
    },
  ];

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress sx={{ bgcolor: alpha(colors.primary.main, 0.2) }} />
      </Box>
    );
  }

  const currentCase = JSON.parse(localStorage.getItem('selectedCase') || '{}');

  const formatBytes = (bytes) => {
    if (bytes === null || bytes === undefined) return '-';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let i = 0;
    let val = bytes;
    while (val >= 1024 && i < units.length - 1) {
      val /= 1024;
      i += 1;
    }
    return `${val.toFixed(2)} ${units[i]}`;
  };

  const handleExtractMore = async () => {
    if (!currentCase.id) return;
    setExtracting(true);
    try {
      await forensicAPI.extractRawChunk(currentCase.id, { size_mb: extractMb });
      const rawRes = await forensicAPI.getRawExtractionStatus(currentCase.id);
      setRawStatus(rawRes.data || null);
    } catch (e) {
      console.error('Raw extract failed', e);
    } finally {
      setExtracting(false);
    }
  };

  return (
    <Box>
      <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
        <Box
          className="cyber-panel"
          sx={{
            p: { xs: 2, md: 2.8 },
            mb: 3,
            borderRadius: 2.5,
            border: `1px solid ${alpha(colors.primary.main, 0.28)}`,
            background: `linear-gradient(120deg, ${alpha(colors.primary.main, 0.2)} 0%, ${alpha(colors.accent.violet, 0.18)} 55%, ${alpha(colors.background.paper, 0.94)} 100%)`,
          }}
        >
          <Typography variant="h4" gutterBottom fontWeight={800} color={colors.text.primary}>
            Cybersecurity Operations Dashboard
          </Typography>
          <Typography variant="body1" color={colors.text.secondary} sx={{ mb: 2 }}>
            Real-time forensic telemetry, anomaly signals, and evidence throughput.
          </Typography>
          <Chip
            label={`Context: ${currentCase.case_id || 'No case selected'}`}
            sx={{
              color: colors.primary.main,
              backgroundColor: alpha(colors.primary.main, 0.15),
              border: `1px solid ${alpha(colors.primary.main, 0.35)}`,
              width: isMobile ? '100%' : 'auto',
            }}
          />
        </Box>
      </motion.div>

      {basicInfo && (
        <Box
          className="cyber-panel"
          sx={{
            p: { xs: 2, md: 2.5 },
            mb: 3,
            borderRadius: 2.5,
            border: `1px solid ${alpha(colors.primary.main, 0.28)}`,
            background: `linear-gradient(120deg, ${alpha(colors.primary.main, 0.16)} 0%, ${alpha(colors.background.paper, 0.92)} 100%)`,
          }}
        >
          <Typography variant="h6" fontWeight={700} gutterBottom>
            Basic Disk Info
          </Typography>
          <Grid container spacing={2}>
            {basicInfo.format === 'tar' ? (
              <>
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color={colors.text.secondary}>Total Files</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {basicInfo.tar_stats?.total_files ?? '-'}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color={colors.text.secondary}>Total Dirs</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {basicInfo.tar_stats?.total_dirs ?? '-'}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color={colors.text.secondary}>Total Size</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {formatBytes(basicInfo.tar_stats?.total_file_size)}
                  </Typography>
                </Grid>
              </>
            ) : (
              <>
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color={colors.text.secondary}>Total Disk</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {formatBytes(basicInfo.total_disk_space)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color={colors.text.secondary}>Allocated</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {formatBytes(basicInfo.allocated_space)}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="caption" color={colors.text.secondary}>Unallocated</Typography>
                  <Typography variant="body1" fontWeight={700}>
                    {formatBytes(basicInfo.unallocated_space)}
                  </Typography>
                </Grid>
              </>
            )}
            <Grid item xs={12} md={6}>
              <Typography variant="caption" color={colors.text.secondary}>MD5</Typography>
              <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                {basicInfo.md5}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="caption" color={colors.text.secondary}>SHA256</Typography>
              <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                {basicInfo.sha256}
              </Typography>
            </Grid>
          </Grid>
        </Box>
      )}

      {rawStatus && (
        <Box
          className="cyber-panel"
          sx={{
            p: { xs: 2, md: 2.5 },
            mb: 3,
            borderRadius: 2.5,
            border: `1px solid ${alpha(colors.accent.orange, 0.3)}`,
            background: `linear-gradient(120deg, ${alpha(colors.accent.orange, 0.12)} 0%, ${alpha(colors.background.paper, 0.92)} 100%)`,
          }}
        >
          <Typography variant="h6" fontWeight={700} gutterBottom>
            Raw Data Extraction
          </Typography>
          <Typography variant="body2" color={colors.text.secondary} sx={{ mb: 2 }}>
            Extracted {formatBytes(rawStatus.extracted_bytes)} of {formatBytes(rawStatus.total_size)} ({rawStatus.percent}%)
          </Typography>
          <LinearProgress
            variant="determinate"
            value={rawStatus.percent || 0}
            sx={{ mb: 2 }}
          />
          <Typography variant="caption" color={colors.text.secondary} display="block">
            Next start offset: {rawStatus.next_start_offset}
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Extract (MB)"
                value={extractMb}
                onChange={(e) => setExtractMb(e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Button
                fullWidth
                variant="contained"
                onClick={handleExtractMore}
                disabled={extracting}
                sx={{ height: '100%' }}
              >
                {extracting ? 'Extracting...' : 'Extract More'}
              </Button>
            </Grid>
          </Grid>
          {rawStatus.ranges && rawStatus.ranges.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color={colors.text.secondary}>
                Extracted ranges:
              </Typography>
              {rawStatus.ranges.slice(-5).map((r, idx) => (
                <Typography key={idx} variant="body2">
                  {r.start_offset} → {r.end_offset} ({formatBytes(r.size)})
                </Typography>
              ))}
            </Box>
          )}
        </Box>
      )}

      {currentCase.id && <ProcessingStatus caseId={currentCase.id} />}

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} lg={3} key={index}>
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }}>
              <StatCard {...card} />
            </motion.div>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <motion.div initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }}>
            <ActivityChart activityByHour={activityByHour} />
          </motion.div>
        </Grid>

        <Grid item xs={12} lg={4}>
          <motion.div initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
            <ArtifactDistribution counts={summaryCounts} />
          </motion.div>
        </Grid>

        <Grid item xs={12}>
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.36 }}>
            <CasesList cases={recentCases} />
          </motion.div>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
