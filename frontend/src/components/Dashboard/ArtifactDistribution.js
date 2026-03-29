import React, { useMemo } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import colors from '../../theme/colors';

ChartJS.register(ArcElement, Tooltip, Legend);

const ArtifactDistribution = ({ counts }) => {
  const { data, hasData } = useMemo(() => {
    const normalized = counts || {};
    const browserCount = (normalized.browser_history || 0)
      + (normalized.browser_cookies || 0)
      + (normalized.browser_downloads || 0);

    const buckets = [
      { label: 'Browser', value: browserCount, color: colors.artifacts.browser },
      { label: 'Registry', value: normalized.registry_artifacts || 0, color: colors.artifacts.registry },
      { label: 'File System', value: normalized.filesystem_artifacts || 0, color: colors.artifacts.filesystem },
      { label: 'USB', value: normalized.usb_devices || 0, color: colors.artifacts.usb },
      { label: 'Events', value: normalized.event_logs || 0, color: colors.artifacts.events },
      { label: 'Programs', value: normalized.installed_programs || 0, color: colors.artifacts.programs },
      { label: 'Deleted', value: normalized.deleted_files || 0, color: colors.artifacts.deleted },
      { label: 'Activity', value: normalized.user_activity || 0, color: colors.artifacts.activity },
      { label: 'Android', value: normalized.android_artifacts || 0, color: colors.artifacts.android },
    ];

    const filtered = buckets.filter((b) => b.value > 0);
    const hasData = filtered.length > 0;
    const dataset = hasData ? filtered : buckets.slice(0, 6);

    return {
      hasData,
      data: {
        labels: dataset.map((b) => b.label),
        datasets: [
          {
            data: dataset.map((b) => b.value),
            backgroundColor: dataset.map((b) => b.color),
            borderColor: colors.background.paper,
            borderWidth: 2,
          },
        ],
      },
    };
  }, [counts]);

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: colors.text.secondary,
          usePointStyle: true,
          padding: 14,
          font: { size: 11, family: 'Rajdhani', weight: '700' },
        },
      },
      tooltip: {
        backgroundColor: '#04111F',
        callbacks: {
          label: (context) => `${context.label}: ${context.parsed}`,
        },
      },
    },
    cutout: '64%',
  };

  return (
    <Card sx={{ height: '100%' }} className="cyber-panel">
      <CardContent>
        <Typography variant="h6" gutterBottom fontWeight={700}>
          Evidence Mix
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {hasData ? 'Distribution of indexed forensic artifacts.' : 'No artifacts indexed yet.'}
        </Typography>
        <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Doughnut data={data} options={options} />
        </Box>
      </CardContent>
    </Card>
  );
};

export default ArtifactDistribution;
