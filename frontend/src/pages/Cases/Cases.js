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
import { forensicAPI } from '../../services/api';

const Cases = () => {
  const [cases, setCases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const response = await forensicAPI.getMongoCases();
        const data = response.data || [];
        const seen = new Set();
        const deduped = data.filter((c) => {
          if (!c.case_id || seen.has(c.case_id)) return false;
          seen.add(c.case_id);
          return true;
        });
        setCases(deduped);
      } catch (e) {
        console.error('Failed to load cases', e);
      }
    };
    load();
  }, []);

  const getPriorityColor = (priority) => {
    const map = {
      critical: colors.status.critical,
      high: colors.status.warning,
      medium: colors.status.info,
      low: colors.status.success,
    };
    return map[String(priority || '').toLowerCase()] || colors.text.secondary;
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
                      {caseItem.case_id}
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
                    {caseItem.image_path || 'Imported disk image'}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      {caseItem.summary?.counts?.timeline_events || caseItem.summary?.total_event_log_entries || 0} events
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {caseItem.extraction_time ? new Date(caseItem.extraction_time).toLocaleDateString() : '-'}
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
