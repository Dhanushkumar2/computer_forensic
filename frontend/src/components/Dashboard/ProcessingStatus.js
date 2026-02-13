import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Alert,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  HourglassEmpty,
  PlayArrow,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import colors from '../../theme/colors';
import { forensicAPI } from '../../services/api';

const ProcessingStatus = ({ caseId }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatus();
    // Poll every 5 seconds if processing
    const interval = setInterval(() => {
      if (status?.status === 'running' || status?.status === 'queued') {
        fetchStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [caseId, status?.status]);

  const fetchStatus = async () => {
    try {
      const response = await forensicAPI.getProcessingStatus(caseId);
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching processing status:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !status) {
    return null;
  }

  const getStatusConfig = () => {
    switch (status.status) {
      case 'completed':
        return {
          icon: <CheckCircle />,
          color: colors.status.success,
          label: 'Processing Complete',
          message: `Successfully extracted ${status.artifacts_extracted} artifacts`,
        };
      case 'running':
        return {
          icon: <PlayArrow />,
          color: colors.status.info,
          label: 'Processing',
          message: 'Extracting artifacts from disk image...',
        };
      case 'queued':
        return {
          icon: <HourglassEmpty />,
          color: colors.status.warning,
          label: 'Queued',
          message: 'Waiting to start processing...',
        };
      case 'failed':
        return {
          icon: <Error />,
          color: colors.status.critical,
          label: 'Processing Failed',
          message: status.error_message || 'An error occurred during processing',
        };
      default:
        return null;
    }
  };

  const config = getStatusConfig();
  if (!config) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card
        sx={{
          mb: 3,
          background: `linear-gradient(135deg, ${config.color}15 0%, ${config.color}05 100%)`,
          border: `2px solid ${config.color}30`,
        }}
      >
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                background: `linear-gradient(135deg, ${config.color} 0%, ${config.color}CC 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
              }}
            >
              {config.icon}
            </Box>
            <Box flex={1}>
              <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                <Typography variant="h6" fontWeight={600}>
                  {config.label}
                </Typography>
                <Chip
                  label={status.status.toUpperCase()}
                  size="small"
                  sx={{
                    backgroundColor: config.color,
                    color: 'white',
                    fontWeight: 600,
                  }}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {config.message}
              </Typography>
            </Box>
          </Box>

          {(status.status === 'running' || status.status === 'queued') && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: `${config.color}20`,
                  '& .MuiLinearProgress-bar': {
                    background: `linear-gradient(90deg, ${config.color} 0%, ${config.color}CC 100%)`,
                  },
                }}
              />
            </Box>
          )}

          {status.status === 'completed' && status.artifacts_extracted > 0 && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Disk image processing completed successfully! You can now explore the extracted artifacts.
            </Alert>
          )}

          {status.status === 'failed' && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {status.error_message || 'Processing failed. Please try again or contact support.'}
            </Alert>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ProcessingStatus;
