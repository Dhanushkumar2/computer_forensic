import React, { useMemo } from 'react';
import { Card, CardContent, Typography, Box, alpha } from '@mui/material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import colors from '../../theme/colors';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const ActivityChart = ({ activityByHour }) => {
  const { labels, values } = useMemo(() => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const counts = new Array(24).fill(0);

    if (Array.isArray(activityByHour)) {
      activityByHour.forEach((entry) => {
        const hour = Number(entry?._id);
        const count = Number(entry?.count || 0);
        if (!Number.isNaN(hour) && hour >= 0 && hour <= 23) {
          counts[hour] = count;
        }
      });
    }

    return {
      labels: hours.map((h) => `${h}:00`),
      values: counts,
    };
  }, [activityByHour]);

  const data = {
    labels,
    datasets: [
      {
        label: 'Timeline Events',
        data: values,
        borderColor: colors.primary.main,
        backgroundColor: alpha(colors.primary.main, 0.18),
        fill: true,
        tension: 0.35,
        pointRadius: 3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: colors.text.secondary,
          usePointStyle: true,
          padding: 14,
          font: { size: 11, family: 'Rajdhani', weight: '700' },
        },
      },
      tooltip: {
        backgroundColor: '#04111F',
        borderColor: alpha(colors.primary.main, 0.4),
        borderWidth: 1,
        padding: 10,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: alpha(colors.primary.main, 0.12) },
        ticks: { color: colors.text.secondary },
      },
      x: {
        grid: { color: alpha(colors.primary.main, 0.05) },
        ticks: { color: colors.text.secondary },
      },
    },
  };

  return (
    <Card className="cyber-panel">
      <CardContent>
        <Typography variant="h6" gutterBottom fontWeight={700}>
          Live SOC Activity Stream
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
          Hourly activity based on recorded timeline events.
        </Typography>
        <Box sx={{ height: 310 }}>
          <Line data={data} options={options} />
        </Box>
      </CardContent>
    </Card>
  );
};

export default ActivityChart;
