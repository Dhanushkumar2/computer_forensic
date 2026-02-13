import React, { useState } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Box,
  CircularProgress,
  Alert,
  LinearProgress,
} from '@mui/material';
import { Refresh, CheckCircle, Error } from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import colors from '../../theme/colors';
import { forensicAPI } from '../../services/api';

const ReExtractButton = ({ caseId, onExtractionComplete }) => {
  const [open, setOpen] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // idle, extracting, success, error
  const [message, setMessage] = useState('');
  const [jobId, setJobId] = useState(null);

  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    if (!extracting) {
      setOpen(false);
      setStatus('idle');
      setMessage('');
      setProgress(0);
    }
  };

  const startExtraction = async () => {
    setExtracting(true);
    setStatus('extracting');
    setMessage('Starting extraction...');
    setProgress(10);

    try {
      // Call the re-extract API endpoint
      const response = await forensicAPI.reExtractCase(caseId);
      
      if (response.data.job_id) {
        setJobId(response.data.job_id);
        setMessage('Extraction job started. Processing disk image...');
        setProgress(30);
        
        // Poll for extraction status
        pollExtractionStatus(response.data.job_id);
      }
    } catch (error) {
      console.error('Error starting extraction:', error);
      setStatus('error');
      setMessage(error.response?.data?.error || 'Failed to start extraction');
      setExtracting(false);
    }
  };

  const pollExtractionStatus = async (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const statusResponse = await forensicAPI.getProcessingStatus(caseId);
        const jobStatus = statusResponse.data.status;
        const artifactsCount = statusResponse.data.artifacts_extracted || 0;

        if (jobStatus === 'running') {
          setProgress(Math.min(50 + (artifactsCount / 100), 90));
          setMessage(`Extracting artifacts... (${artifactsCount} found)`);
        } else if (jobStatus === 'completed') {
          clearInterval(pollInterval);
          setProgress(100);
          setStatus('success');
          setMessage(`Extraction completed! ${artifactsCount} artifacts extracted.`);
          setExtracting(false);
          
          // Notify parent component
          if (onExtractionComplete) {
            onExtractionComplete(artifactsCount);
          }
          
          // Auto-close after 2 seconds
          setTimeout(() => {
            handleClose();
          }, 2000);
        } else if (jobStatus === 'failed') {
          clearInterval(pollInterval);
          setStatus('error');
          setMessage(statusResponse.data.error_message || 'Extraction failed');
          setExtracting(false);
        }
      } catch (error) {
        console.error('Error polling status:', error);
        clearInterval(pollInterval);
        setStatus('error');
        setMessage('Failed to check extraction status');
        setExtracting(false);
      }
    }, 2000); // Poll every 2 seconds

    // Timeout after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (extracting) {
        setStatus('error');
        setMessage('Extraction timeout');
        setExtracting(false);
      }
    }, 600000);
  };

  return (
    <>
      <Button
        variant="contained"
        startIcon={<Refresh />}
        onClick={handleOpen}
        sx={{
          background: colors.gradients.primary,
          color: 'white',
          fontWeight: 600,
          textTransform: 'none',
          px: 3,
          py: 1.5,
          borderRadius: 2,
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.15)',
          '&:hover': {
            background: colors.gradients.primary,
            transform: 'translateY(-2px)',
            boxShadow: '0px 6px 16px rgba(0, 0, 0, 0.2)',
          },
          transition: 'all 0.3s ease',
        }}
      >
        Extract More Data
      </Button>

      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            background: colors.background.default,
          },
        }}
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                background: colors.gradients.primary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
              }}
            >
              <Refresh />
            </Box>
            <Box>
              <Typography variant="h6" fontWeight={700}>
                Re-Extract Forensic Data
              </Typography>
              <Typography variant="body2" color={colors.text.secondary}>
                Extract additional artifacts from disk image
              </Typography>
            </Box>
          </Box>
        </DialogTitle>

        <DialogContent>
          <AnimatePresence mode="wait">
            {status === 'idle' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <Alert severity="info" sx={{ mb: 2 }}>
                  This will re-scan the disk image and extract any new or updated artifacts.
                </Alert>
                <Typography variant="body2" color={colors.text.secondary}>
                  The extraction process may take several minutes depending on the size of the disk image.
                  All newly found artifacts will be automatically added to the database and displayed on the website.
                </Typography>
              </motion.div>
            )}

            {status === 'extracting' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <Box textAlign="center" py={3}>
                  <CircularProgress
                    size={60}
                    sx={{
                      color: colors.primary.main,
                      mb: 2,
                    }}
                  />
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    {message}
                  </Typography>
                  <Box sx={{ width: '100%', mt: 3 }}>
                    <LinearProgress
                      variant="determinate"
                      value={progress}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: colors.background.lighter,
                        '& .MuiLinearProgress-bar': {
                          background: colors.gradients.primary,
                          borderRadius: 4,
                        },
                      }}
                    />
                    <Typography variant="body2" color={colors.text.secondary} sx={{ mt: 1 }}>
                      {progress}% complete
                    </Typography>
                  </Box>
                </Box>
              </motion.div>
            )}

            {status === 'success' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
              >
                <Box textAlign="center" py={3}>
                  <CheckCircle
                    sx={{
                      fontSize: 80,
                      color: colors.status.success,
                      mb: 2,
                    }}
                  />
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Extraction Completed!
                  </Typography>
                  <Typography variant="body2" color={colors.text.secondary}>
                    {message}
                  </Typography>
                  <Alert severity="success" sx={{ mt: 2 }}>
                    New artifacts are now available in the database and will be displayed automatically.
                  </Alert>
                </Box>
              </motion.div>
            )}

            {status === 'error' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
              >
                <Box textAlign="center" py={3}>
                  <Error
                    sx={{
                      fontSize: 80,
                      color: colors.status.error,
                      mb: 2,
                    }}
                  />
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Extraction Failed
                  </Typography>
                  <Typography variant="body2" color={colors.text.secondary}>
                    {message}
                  </Typography>
                  <Alert severity="error" sx={{ mt: 2 }}>
                    Please check the disk image path and try again.
                  </Alert>
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3 }}>
          {status === 'idle' && (
            <>
              <Button
                onClick={handleClose}
                sx={{
                  color: colors.text.secondary,
                  textTransform: 'none',
                  fontWeight: 600,
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={startExtraction}
                variant="contained"
                sx={{
                  background: colors.gradients.primary,
                  color: 'white',
                  fontWeight: 600,
                  textTransform: 'none',
                  px: 3,
                }}
              >
                Start Extraction
              </Button>
            </>
          )}
          {(status === 'success' || status === 'error') && (
            <Button
              onClick={handleClose}
              variant="contained"
              sx={{
                background: colors.gradients.primary,
                color: 'white',
                fontWeight: 600,
                textTransform: 'none',
                px: 3,
              }}
            >
              Close
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ReExtractButton;
