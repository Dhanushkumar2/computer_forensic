import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  FolderOpen,
  Storage,
  Warning,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import colors from '../../theme/colors';
import { forensicAPI } from '../../services/api';
import StatCard from '../../components/Dashboard/StatCard';
import CasesList from '../../components/Dashboard/CasesList';
import ActivityChart from '../../components/Dashboard/ActivityChart';
import ArtifactDistribution from '../../components/Dashboard/ArtifactDistribution';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalCases: 0,
    activeCases: 0,
    totalArtifacts: 0,
    criticalFindings: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentCases, setRecentCases] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, casesRes] = await Promise.all([
        forensicAPI.getDashboardStats(),
        forensicAPI.getRecentCases(),
      ]);
      
      setStats(statsRes.data);
      setRecentCases(casesRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
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
      title: 'Active Cases',
      value: stats.activeCases,
      icon: <TrendingUp />,
      color: colors.status.success,
      trend: '+5%',
    },
    {
      title: 'Artifacts Collected',
      value: stats.totalArtifacts.toLocaleString(),
      icon: <Storage />,
      color: colors.accent.cyan,
      trend: '+23%',
    },
    {
      title: 'Critical Findings',
      value: stats.criticalFindings,
      icon: <Warning />,
      color: colors.status.critical,
      trend: '-8%',
    },
  ];

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress sx={{ bgcolor: colors.background.card }} />
      </Box>
    );
  }

  return (
    <Box>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Typography variant="h4" gutterBottom fontWeight={700} color={colors.text.primary}>
          Dashboard
        </Typography>
        <Typography variant="body1" color={colors.text.secondary} sx={{ mb: 4 }}>
          Welcome back! Here's what's happening with your investigations.
        </Typography>
      </motion.div>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} lg={3} key={index}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
            >
              <StatCard {...card} />
            </motion.div>
          </Grid>
        ))}
      </Grid>

      {/* Charts and Lists */}
      <Grid container spacing={3}>
        {/* Activity Chart */}
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <ActivityChart />
          </motion.div>
        </Grid>

        {/* Artifact Distribution */}
        <Grid item xs={12} lg={4}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <ArtifactDistribution />
          </motion.div>
        </Grid>

        {/* Recent Cases */}
        <Grid item xs={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            <CasesList cases={recentCases} />
          </motion.div>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
