import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Add,
  FolderOpen,
  CloudUpload,
  Search,
  Delete,
  Visibility,
  CalendarToday,
  Person,
  Storage,
  CheckCircle,
  Pending,
  Error as ErrorIcon,
  Logout,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import colors from '../../theme/colors';
import { forensicAPI } from '../../services/api';

const CaseSelection = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [openNewCase, setOpenNewCase] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [availableDiskImages, setAvailableDiskImages] = useState([]);
  const [newCase, setNewCase] = useState({
    title: '',
    description: '',
    priority: 'medium',
    diskImageFilename: '',
  });

  useEffect(() => {
    fetchCases();
    fetchDiskImages();
  }, []);

  const fetchDiskImages = async () => {
    try {
      console.log('Fetching disk images from:', `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/disk-images/`);
      const response = await forensicAPI.getDiskImages();
      console.log('Disk images response:', response);
      console.log('Response data:', response.data);
      const images = response.data.images || [];
      console.log('Extracted images array:', images);
      console.log('Number of images:', images.length);
      setAvailableDiskImages(images);
      
      if (images.length === 0) {
        console.warn('No disk images found. Check if:');
        console.warn('1. Backend server is running on http://localhost:8000');
        console.warn('2. Disk images exist in forensic_ir_app/data/samples/');
        console.warn('3. CORS is properly configured');
      }
    } catch (error) {
      console.error('Error fetching disk images:', error);
      console.error('Error message:', error.message);
      console.error('Error response:', error.response);
      console.error('Error details:', error.response?.data);
      
      // Show user-friendly error
      alert(`Failed to load disk images: ${error.message}\n\nMake sure the backend server is running on http://localhost:8000`);
    }
  };

  const fetchCases = async () => {
    setLoading(true);
    try {
      // Mock cases - replace with actual API call
      const mockCases = [
        {
          id: 1,
          case_id: 'CASE-2024-001',
          title: 'Employee Data Breach Investigation',
          description: 'Investigation of potential data exfiltration',
          status: 'active',
          priority: 'high',
          created_at: '2024-11-20',
          assigned_to: 'John Doe',
          artifacts_count: 5678,
          disk_image: 'nps-2008-jean.E01',
        },
        {
          id: 2,
          case_id: 'CASE-2024-002',
          title: 'Malware Analysis - Workstation 42',
          description: 'Suspected malware infection on employee workstation',
          status: 'completed',
          priority: 'medium',
          created_at: '2024-11-15',
          assigned_to: 'Jane Smith',
          artifacts_count: 3421,
          disk_image: 'workstation-42.dd',
        },
        {
          id: 3,
          case_id: 'CASE-2024-003',
          title: 'Insider Threat Assessment',
          description: 'Behavioral analysis of suspicious user activity',
          status: 'pending',
          priority: 'high',
          created_at: '2024-11-18',
          assigned_to: 'Mike Johnson',
          artifacts_count: 1247,
          disk_image: 'user-laptop.E01',
        },
      ];
      setCases(mockCases);
    } catch (error) {
      console.error('Error fetching cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCase = async () => {
    if (!newCase.title || !newCase.diskImageFilename) {
      alert('Please provide case title and select a disk image');
      return;
    }

    setLoading(true);
    setUploadProgress(0);

    try {
      // Create case data
      const caseData = {
        title: newCase.title,
        description: newCase.description,
        priority: newCase.priority,
        disk_image_filename: newCase.diskImageFilename,
        status: 'processing',
      };

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);

      // Create case via API
      const response = await forensicAPI.createCase(caseData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      const newCaseData = response.data;

      // Add to cases list
      setCases([newCaseData, ...cases]);
      
      // Close modal
      setTimeout(() => {
        setOpenNewCase(false);
        setNewCase({
          title: '',
          description: '',
          priority: 'medium',
          diskImageFilename: '',
        });
        setLoading(false);
        setUploadProgress(0);

        // Navigate to the new case
        handleSelectCase(newCaseData);
      }, 1000);

    } catch (error) {
      console.error('Error creating case:', error);
      alert('Error creating case: ' + (error.response?.data?.error || error.message));
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const handleSelectCase = (caseData) => {
    // Store selected case in localStorage
    localStorage.setItem('selectedCase', JSON.stringify(caseData));
    // Navigate to dashboard
    navigate('/dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('selectedCase');
    navigate('/login');
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <Pending />;
      case 'completed':
        return <CheckCircle />;
      case 'pending':
        return <ErrorIcon />;
      case 'processing':
        return <Storage />;
      default:
        return <FolderOpen />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return colors.status.critical;
      case 'medium':
        return colors.status.warning;
      case 'low':
        return colors.status.info;
      default:
        return colors.text.secondary;
    }
  };

  const filteredCases = cases.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${colors.background.light} 0%, ${colors.background.default} 100%)`,
        py: 4,
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
            <Box>
              <Typography variant="h4" fontWeight={700} color={colors.text.primary}>
                Case Management
              </Typography>
              <Typography variant="body1" color={colors.text.secondary}>
                Select an existing case or create a new investigation
              </Typography>
            </Box>
            <Box display="flex" gap={2}>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setOpenNewCase(true)}
                sx={{
                  background: colors.gradients.primary,
                  fontWeight: 600,
                  px: 3,
                }}
              >
                New Case
              </Button>
              <Tooltip title="Logout">
                <IconButton
                  onClick={handleLogout}
                  sx={{
                    backgroundColor: colors.status.critical,
                    color: 'white',
                    '&:hover': {
                      backgroundColor: colors.status.critical,
                      opacity: 0.9,
                    },
                  }}
                >
                  <Logout />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </motion.div>

        {/* Search Bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.5 }}
        >
          <TextField
            fullWidth
            placeholder="Search cases by title, ID, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: colors.primary.main }} />,
            }}
            sx={{
              mb: 4,
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'white',
              },
            }}
          />
        </motion.div>

        {loading && <LinearProgress sx={{ mb: 3 }} />}

        {/* Cases Grid */}
        <Grid container spacing={3}>
          {filteredCases.map((caseData, index) => (
            <Grid item xs={12} md={6} lg={4} key={caseData.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                whileHover={{ scale: 1.02 }}
              >
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    border: `2px solid ${getStatusColor(caseData.status)}30`,
                    '&:hover': {
                      border: `2px solid ${getStatusColor(caseData.status)}`,
                      boxShadow: `0px 8px 24px ${getStatusColor(caseData.status)}30`,
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    {/* Status Badge */}
                    <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                      <Chip
                        icon={getStatusIcon(caseData.status)}
                        label={caseData.status.toUpperCase()}
                        size="small"
                        sx={{
                          backgroundColor: getStatusColor(caseData.status),
                          color: 'white',
                          fontWeight: 600,
                        }}
                      />
                      <Chip
                        label={caseData.priority.toUpperCase()}
                        size="small"
                        sx={{
                          backgroundColor: getPriorityColor(caseData.priority),
                          color: 'white',
                          fontWeight: 600,
                        }}
                      />
                    </Box>

                    {/* Case ID */}
                    <Typography
                      variant="caption"
                      color={colors.text.secondary}
                      fontWeight={600}
                      display="block"
                      mb={1}
                    >
                      {caseData.case_id}
                    </Typography>

                    {/* Title */}
                    <Typography variant="h6" fontWeight={600} color={colors.text.primary} mb={1}>
                      {caseData.title}
                    </Typography>

                    {/* Description */}
                    <Typography
                      variant="body2"
                      color={colors.text.secondary}
                      mb={2}
                      sx={{
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {caseData.description}
                    </Typography>

                    {/* Metadata */}
                    <Box display="flex" flexDirection="column" gap={1}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <CalendarToday sx={{ fontSize: 16, color: colors.text.secondary }} />
                        <Typography variant="caption" color={colors.text.secondary}>
                          {caseData.created_at}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Person sx={{ fontSize: 16, color: colors.text.secondary }} />
                        <Typography variant="caption" color={colors.text.secondary}>
                          {caseData.assigned_to}
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Storage sx={{ fontSize: 16, color: colors.text.secondary }} />
                        <Typography variant="caption" color={colors.text.secondary}>
                          {caseData.artifacts_count.toLocaleString()} artifacts
                        </Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <FolderOpen sx={{ fontSize: 16, color: colors.text.secondary }} />
                        <Typography variant="caption" color={colors.text.secondary}>
                          {caseData.disk_image}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>

                  <CardActions sx={{ p: 2, pt: 0 }}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<Visibility />}
                      onClick={() => handleSelectCase(caseData)}
                      sx={{
                        background: colors.gradients.primary,
                        fontWeight: 600,
                      }}
                    >
                      Open Case
                    </Button>
                  </CardActions>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        {filteredCases.length === 0 && !loading && (
          <Box textAlign="center" py={8}>
            <Typography variant="h6" color={colors.text.secondary}>
              No cases found
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setOpenNewCase(true)}
              sx={{
                mt: 2,
                background: colors.gradients.primary,
                fontWeight: 600,
              }}
            >
              Create Your First Case
            </Button>
          </Box>
        )}
      </Container>

      {/* New Case Dialog */}
      <Dialog
        open={openNewCase}
        onClose={() => !loading && setOpenNewCase(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Typography variant="h5" fontWeight={600}>
            Create New Case
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Case Title"
              value={newCase.title}
              onChange={(e) => setNewCase({ ...newCase, title: e.target.value })}
              sx={{ mb: 3 }}
              required
            />

            <TextField
              fullWidth
              label="Description"
              multiline
              rows={3}
              value={newCase.description}
              onChange={(e) => setNewCase({ ...newCase, description: e.target.value })}
              sx={{ mb: 3 }}
            />

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Priority</InputLabel>
              <Select
                value={newCase.priority}
                label="Priority"
                onChange={(e) => setNewCase({ ...newCase, priority: e.target.value })}
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
              </Select>
            </FormControl>

            {/* Disk Image Selection */}
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Select Disk Image</InputLabel>
              <Select
                value={newCase.diskImageFilename}
                label="Select Disk Image"
                onChange={(e) => setNewCase({ ...newCase, diskImageFilename: e.target.value })}
              >
                {availableDiskImages.length === 0 && (
                  <MenuItem value="" disabled>
                    No disk images found in data/samples/
                  </MenuItem>
                )}
                {availableDiskImages.map((image) => (
                  <MenuItem key={image.filename} value={image.filename}>
                    <Box>
                      <Typography variant="body1" fontWeight={600}>
                        {image.filename}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {image.size_formatted} • {image.extension}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {availableDiskImages.length === 0 && (
              <Alert severity="info" sx={{ mb: 3 }}>
                Place disk images (.E01, .DD, .RAW, .IMG) in the <strong>data/samples/</strong> directory to make them available for processing.
              </Alert>
            )}

            {uploadProgress > 0 && uploadProgress < 100 && (
              <Box sx={{ mt: 3 }}>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2" color={colors.text.secondary}>
                    Uploading and processing...
                  </Typography>
                  <Typography variant="body2" fontWeight={600} color={colors.primary.main}>
                    {uploadProgress}%
                  </Typography>
                </Box>
                <LinearProgress variant="determinate" value={uploadProgress} />
              </Box>
            )}

            {uploadProgress === 100 && (
              <Alert severity="success" sx={{ mt: 3 }}>
                Case created successfully! Redirecting...
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setOpenNewCase(false)} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateCase}
            disabled={loading || !newCase.title || !newCase.diskImageFilename}
            sx={{
              background: colors.gradients.primary,
              fontWeight: 600,
            }}
          >
            {loading ? 'Creating...' : 'Create Case'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CaseSelection;
