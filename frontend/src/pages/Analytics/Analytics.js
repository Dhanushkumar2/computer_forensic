import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Paper,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Warning,
  TrendingUp,
  Security,
  Speed,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import colors from '../../theme/colors';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const Analytics = () => {
  const [loading, setLoading] = useState(false);

  // Activity Timeline Data
  const activityData = {
    labels: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
    datasets: [
      {
        label: 'User Activity',
        data: [12, 8, 15, 45, 67, 89, 72, 34],
        borderColor: colors.primary.main,
        backgroundColor: `${colors.primary.main}30`,
        fill: true,
        tension: 0.4,
        borderWidth: 3,
      },
      {
        label: 'System Events',
        data: [8, 12, 20, 35, 52, 71, 58, 28],
        borderColor: colors.accent.cyan,
        backgroundColor: `${colors.accent.cyan}30`,
        fill: true,
        tension: 0.4,
        borderWidth: 3,
      },
    ],
  };

  // Artifact Distribution Data
  const artifactDistribution = {
    labels: ['Browser', 'Registry', 'Files', 'USB', 'Events', 'Programs'],
    datasets: [
      {
        data: [1247, 856, 3421, 12, 5678, 145],
        backgroundColor: [
          colors.artifacts.browser,
          colors.artifacts.registry,
          colors.artifacts.filesystem,
          colors.artifacts.usb,
          colors.artifacts.events,
          colors.artifacts.programs,
        ],
        borderWidth: 0,
      },
    ],
  };

  // Top Programs Data
  const topProgramsData = {
    labels: ['Chrome', 'Firefox', 'Word', 'Excel', 'PowerShell', 'CMD'],
    datasets: [
      {
        label: 'Execution Count',
        data: [234, 189, 156, 142, 98, 87],
        backgroundColor: colors.chart.map(c => `${c}CC`),
        borderRadius: 8,
      },
    ],
  };

  // Suspicious Activity Indicators
  const suspiciousIndicators = [
    {
      title: 'Deleted Executables',
      count: 12,
      severity: 'high',
      icon: <Warning />,
      color: colors.status.critical,
    },
    {
      title: 'Late Night Activity',
      count: 34,
      severity: 'medium',
      icon: <TrendingUp />,
      color: colors.status.warning,
    },
    {
      title: 'System Tools Usage',
      count: 56,
      severity: 'low',
      icon: <Security />,
      color: colors.status.info,
    },
    {
      title: 'Rapid File Access',
      count: 23,
      severity: 'medium',
      icon: <Speed />,
      color: colors.accent.amber,
    },
  ];

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12,
            weight: 600,
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        borderRadius: 8,
        titleFont: {
          size: 14,
          weight: 600,
        },
        bodyFont: {
          size: 13,
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: colors.background.lighter,
        },
        ticks: {
          font: {
            size: 11,
          },
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
          },
        },
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12,
            weight: 600,
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        borderRadius: 8,
      },
    },
    cutout: '65%',
  };

  return (
    <Box>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Typography variant="h4" fontWeight={700} color={colors.text.primary} gutterBottom>
          Advanced Analytics
        </Typography>
        <Typography variant="body1" color={colors.text.secondary} sx={{ mb: 4 }}>
          AI-powered insights and pattern recognition for forensic investigation
        </Typography>
      </motion.div>

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Suspicious Activity Indicators */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {suspiciousIndicators.map((indicator, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              whileHover={{ scale: 1.05 }}
            >
              <Card
                sx={{
                  background: `linear-gradient(135deg, ${indicator.color}15 0%, ${indicator.color}05 100%)`,
                  border: `2px solid ${indicator.color}30`,
                  '&:hover': {
                    border: `2px solid ${indicator.color}`,
                  },
                }}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 2,
                        background: `linear-gradient(135deg, ${indicator.color} 0%, ${indicator.color}CC 100%)`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                      }}
                    >
                      {indicator.icon}
                    </Box>
                    <Chip
                      label={indicator.severity.toUpperCase()}
                      size="small"
                      sx={{
                        backgroundColor: indicator.color,
                        color: 'white',
                        fontWeight: 600,
                      }}
                    />
                  </Box>
                  <Typography variant="h4" fontWeight={700} color={colors.text.primary}>
                    {indicator.count}
                  </Typography>
                  <Typography variant="body2" color={colors.text.secondary}>
                    {indicator.title}
                  </Typography>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Activity Timeline */}
        <Grid item xs={12} lg={8}>
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <Paper elevation={0} sx={{ p: 3, height: 400 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Activity Timeline (24h)
              </Typography>
              <Box sx={{ height: 320 }}>
                <Line data={activityData} options={chartOptions} />
              </Box>
            </Paper>
          </motion.div>
        </Grid>

        {/* Artifact Distribution */}
        <Grid item xs={12} lg={4}>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <Paper elevation={0} sx={{ p: 3, height: 400 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Artifact Distribution
              </Typography>
              <Box sx={{ height: 320 }}>
                <Doughnut data={artifactDistribution} options={doughnutOptions} />
              </Box>
            </Paper>
          </motion.div>
        </Grid>

        {/* Top Programs */}
        <Grid item xs={12}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            <Paper elevation={0} sx={{ p: 3, height: 400 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Most Executed Programs
              </Typography>
              <Box sx={{ height: 320 }}>
                <Bar data={topProgramsData} options={chartOptions} />
              </Box>
            </Paper>
          </motion.div>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics;
