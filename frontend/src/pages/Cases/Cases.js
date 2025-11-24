import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  InputAdornment,
  Chip,
} from '@mui/material';
import { Add, Search, FilterList } from '@mui/icons-material';
import { motion } from 'framer-motion';
import colors from '../../theme/colors';

const Cases = () => {
  const [cases, setCases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  const mockCases = [
    {
      id: 1,
      name: 'Case-2024-001',
      description: 'Corporate data breach investigation',
      status: 'Active',
      priority: 'High',
      artifacts: 1250,
      date: '2024-11-20',
    },
    {
      id: 2,
      name: 'Case-2024-002',
      description: 'Malware analysis and containment',
      status: 'Pending',
      priority: 'Medium',
      artifacts: 850,
      date: '2024-11-19',
    },
    {
      id: 3,
      name: 'Case-2024-003',
      description: 'Insider threat investigation',
      status: 'Critical',
      priority: 'Critical',
      artifacts: 2100,
      date: '2024-11-18',
    },
  ];

  useEffect(() => {
    setCases(mockCases);
  }, []);

  const getPriorityColor = (priority) => {
    const colors = {
      Critical: '#B85450',
      High: '#D4A574',
      Medium: '#8B9DAF',
      Low: '#7A9B76',
    };
    return colors[priority] || '#8B9DAF';
  };

  return (
    <Box>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Typography variant="h4" fontWeight={700} color={colors.text.primary}>
              Cases
            </Typography>
            <Typography variant="body1" color={colors.text.secondary}>
              Manage and track forensic investigations
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<Add />}
            sx={{
              bgcolor: colors.primary.main,
              '&:hover': { bgcolor: colors.primary.dark },
            }}
          >
            New Case
          </Button>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
          <TextField
            fullWidth
            placeholder="Search cases..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
          <Button
            variant="outlined"
            startIcon={<FilterList />}
            sx={{ minWidth: 120 }}
          >
            Filters
          </Button>
        </Box>
      </motion.div>

      <Grid container spacing={3}>
        {cases.map((caseItem, index) => (
          <Grid item xs={12} md={6} lg={4} key={caseItem.id}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -8 }}
            >
              <Card
                sx={{
                  cursor: 'pointer',
                  borderLeft: `4px solid ${getPriorityColor(caseItem.priority)}`,
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="h6" fontWeight={600}>
                      {caseItem.name}
                    </Typography>
                    <Chip
                      label={caseItem.status}
                      size="small"
                      sx={{
                        bgcolor: `${getPriorityColor(caseItem.priority)}20`,
                        color: getPriorityColor(caseItem.priority),
                      }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {caseItem.description}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      {caseItem.artifacts} artifacts
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(caseItem.date).toLocaleDateString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default Cases;
