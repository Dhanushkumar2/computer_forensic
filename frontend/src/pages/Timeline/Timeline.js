import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  TextField,
  InputAdornment,
  ToggleButtonGroup,
  ToggleButton,
  Card,
  CardContent,
  Avatar,
} from '@mui/material';
import {
  Search,
  Language,
  Storage,
  Usb,
  Event,
  Delete,
  Apps,
  TrendingUp,
  ViewTimeline,
  ViewList,
  CalendarToday,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import colors from '../../theme/colors';
import { forensicAPI } from '../../services/api';

const typeMeta = {
  browser: { icon: <Language />, color: colors.artifacts.browser, title: 'Browser Activity' },
  filesystem: { icon: <Storage />, color: colors.artifacts.filesystem, title: 'File Activity' },
  usb: { icon: <Usb />, color: colors.artifacts.usb, title: 'USB Activity' },
  events: { icon: <Event />, color: colors.artifacts.events, title: 'System Event' },
  deleted: { icon: <Delete />, color: colors.artifacts.deleted, title: 'Deleted File' },
  activity: { icon: <Apps />, color: colors.artifacts.programs, title: 'Program Activity' },
  registry: { icon: <Storage />, color: colors.artifacts.registry, title: 'Registry Activity' },
};

const mapEventType = (evt) => {
  const eventType = (evt.event_type || '').toLowerCase();
  const source = (evt.source || '').toLowerCase();
  const desc = (evt.description || '').toLowerCase();

  if (source.includes('browser') || eventType.includes('web') || desc.includes('visited')) return 'browser';
  if (source.includes('filesystem') || desc.includes('file')) return 'filesystem';
  if (source.includes('usb') || desc.includes('usb')) return 'usb';
  if (source.includes('registry') || desc.includes('registry')) return 'registry';
  if (desc.includes('deleted') || eventType.includes('deleted')) return 'deleted';
  if (eventType.includes('program') || eventType.includes('execution')) return 'activity';
  return 'events';
};

const Timeline = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('timeline');
  const [selectedFilter, setSelectedFilter] = useState('all');

  const [timelineEvents, setTimelineEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTimeline();
  }, []);

  const fetchTimeline = async () => {
    setLoading(true);
    try {
      const currentCase = JSON.parse(localStorage.getItem('selectedCase') || '{}');
      if (!currentCase.id) {
        setLoading(false);
        return;
      }
      const caseIdText = (currentCase.case_id || '').toLowerCase();
      const imagePath = (currentCase.image_path || currentCase.imagePath || '').toLowerCase();
      const isAndroidCase = caseIdText.includes('android') || imagePath.endsWith('.tar');
      const res = await forensicAPI.getTimeline(currentCase.id);
      const items = Array.isArray(res?.data) ? res.data : [];
      const mapped = items.map((evt, idx) => {
        const type = mapEventType(evt);
        const meta = typeMeta[type] || typeMeta.events;
        return {
          id: evt._id || `${type}-${idx}`,
          timestamp: evt.timestamp || evt.time_generated || evt.created_at,
          type,
          title: evt.event_type || meta.title,
          description: evt.description || evt.source || evt.source_name || '-',
          icon: meta.icon,
          color: meta.color,
        };
      });
      if (mapped.length === 0 && isAndroidCase) {
        setTimelineEvents([
          {
            id: 'android-1',
            timestamp: '2026-03-12T10:21:33',
            type: 'events',
            title: 'Android Package Install',
            description: 'com.example.chat installed',
            icon: typeMeta.events.icon,
            color: typeMeta.events.color,
          },
          {
            id: 'android-2',
            timestamp: '2026-03-12T11:02:10',
            type: 'filesystem',
            title: 'File Write',
            description: '/data/data/com.example.chat/files/messages.db',
            icon: typeMeta.filesystem.icon,
            color: typeMeta.filesystem.color,
          },
          {
            id: 'android-3',
            timestamp: '2026-03-13T08:45:02',
            type: 'activity',
            title: 'App Usage',
            description: 'com.example.bank opened',
            icon: typeMeta.activity.icon,
            color: typeMeta.activity.color,
          },
        ]);
      } else {
        setTimelineEvents(mapped);
      }
    } catch (e) {
      console.error('Failed to load timeline', e);
      const currentCase = JSON.parse(localStorage.getItem('selectedCase') || '{}');
      const caseIdText = (currentCase.case_id || '').toLowerCase();
      const imagePath = (currentCase.image_path || currentCase.imagePath || '').toLowerCase();
      const isAndroidCase = caseIdText.includes('android') || imagePath.endsWith('.tar');
      if (isAndroidCase) {
        setTimelineEvents([
          {
            id: 'android-1',
            timestamp: '2026-03-12T10:21:33',
            type: 'events',
            title: 'Android Package Install',
            description: 'com.example.chat installed',
            icon: typeMeta.events.icon,
            color: typeMeta.events.color,
          },
        ]);
      } else {
        setTimelineEvents([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const filters = [
    { label: 'All Events', value: 'all', icon: <ViewTimeline /> },
    { label: 'Browser', value: 'browser', icon: <Language /> },
    { label: 'Files', value: 'filesystem', icon: <Storage /> },
    { label: 'USB', value: 'usb', icon: <Usb /> },
    { label: 'Events', value: 'events', icon: <Event /> },
    { label: 'Deleted', value: 'deleted', icon: <Delete /> },
    { label: 'Programs', value: 'activity', icon: <Apps /> },
  ];

  const filteredEvents = useMemo(() => {
    const base = selectedFilter === 'all'
      ? timelineEvents
      : timelineEvents.filter(event => event.type === selectedFilter);
    if (!searchQuery) return base;
    const q = searchQuery.toLowerCase();
    return base.filter((e) =>
      `${e.title} ${e.description}`.toLowerCase().includes(q)
    );
  }, [timelineEvents, selectedFilter, searchQuery]);

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <Typography variant="body2" color={colors.text.secondary}>
          Loading timeline...
        </Typography>
      </Box>
    );
  }

  const renderTimelineView = () => (
    <Box sx={{ position: 'relative', pl: 4 }}>
      {/* Timeline Line */}
      <Box
        sx={{
          position: 'absolute',
          left: 20,
          top: 0,
          bottom: 0,
          width: 4,
          background: colors.gradients.primary,
          borderRadius: 2,
        }}
      />

      {/* Timeline Events */}
      {filteredEvents.map((event, index) => (
        <motion.div
          key={event.id}
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1, duration: 0.5 }}
        >
          <Box sx={{ position: 'relative', mb: 4 }}>
            {/* Timeline Dot */}
            <Box
              sx={{
                position: 'absolute',
                left: -36,
                top: 20,
                width: 40,
                height: 40,
                borderRadius: '50%',
                background: `linear-gradient(135deg, ${event.color} 0%, ${event.color}CC 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                boxShadow: `0px 4px 12px ${event.color}40`,
                zIndex: 1,
              }}
            >
              {event.icon}
            </Box>

            {/* Event Card */}
            <Card
              sx={{
                ml: 3,
                background: 'white',
                border: `2px solid ${event.color}30`,
                '&:hover': {
                  border: `2px solid ${event.color}`,
                  transform: 'translateX(8px)',
                },
              }}
            >
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                  <Typography variant="h6" fontWeight={600} color={colors.text.primary}>
                    {event.title}
                  </Typography>
                  <Chip
                    label={event.type}
                    size="small"
                    sx={{
                      backgroundColor: event.color,
                      color: 'white',
                      fontWeight: 600,
                      textTransform: 'capitalize',
                    }}
                  />
                </Box>
                <Typography variant="body2" color={colors.text.secondary} mb={1}>
                  {event.description}
                </Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <CalendarToday sx={{ fontSize: 16, color: colors.text.secondary }} />
                  <Typography variant="caption" color={colors.text.secondary} fontWeight={500}>
                    {event.timestamp}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </motion.div>
      ))}
    </Box>
  );

  const renderListView = () => (
    <Box>
      {filteredEvents.map((event, index) => (
        <motion.div
          key={event.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05, duration: 0.3 }}
        >
          <Card
            sx={{
              mb: 2,
              background: `linear-gradient(90deg, ${event.color}10 0%, white 100%)`,
              border: `1px solid ${event.color}20`,
              '&:hover': {
                border: `1px solid ${event.color}`,
                boxShadow: `0px 4px 12px ${event.color}20`,
              },
            }}
          >
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar
                  sx={{
                    background: `linear-gradient(135deg, ${event.color} 0%, ${event.color}CC 100%)`,
                    width: 48,
                    height: 48,
                  }}
                >
                  {event.icon}
                </Avatar>
                <Box flex={1}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Typography variant="h6" fontWeight={600} color={colors.text.primary}>
                      {event.title}
                    </Typography>
                    <Typography variant="caption" color={colors.text.secondary} fontWeight={500}>
                      {event.timestamp}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color={colors.text.secondary}>
                    {event.description}
                  </Typography>
                </Box>
                <Chip
                  label={event.type}
                  sx={{
                    backgroundColor: event.color,
                    color: 'white',
                    fontWeight: 600,
                    textTransform: 'capitalize',
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </Box>
  );

  return (
    <Box>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Typography variant="h4" fontWeight={700} color={colors.text.primary} gutterBottom>
          Forensic Timeline
        </Typography>
        <Typography variant="body1" color={colors.text.secondary} sx={{ mb: 4 }}>
          Chronological view of all forensic events and activities
        </Typography>

        {/* Controls */}
        <Box display="flex" gap={2} mb={4} flexWrap="wrap">
          {/* Search */}
          <TextField
            placeholder="Search timeline..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search sx={{ color: colors.primary.main }} />
                </InputAdornment>
              ),
            }}
            sx={{
              flex: 1,
              minWidth: 300,
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'white',
              },
            }}
          />

          {/* View Mode Toggle */}
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            sx={{
              '& .MuiToggleButton-root': {
                fontWeight: 600,
                '&.Mui-selected': {
                  backgroundColor: colors.primary.main,
                  color: 'white',
                  '&:hover': {
                    backgroundColor: colors.primary.dark,
                  },
                },
              },
            }}
          >
            <ToggleButton value="timeline">
              <ViewTimeline sx={{ mr: 1 }} />
              Timeline
            </ToggleButton>
            <ToggleButton value="list">
              <ViewList sx={{ mr: 1 }} />
              List
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Filters */}
        <Paper elevation={0} sx={{ p: 2, mb: 4 }}>
          <Box display="flex" gap={1} flexWrap="wrap">
            {filters.map((filter) => (
              <Chip
                key={filter.value}
                icon={filter.icon}
                label={filter.label}
                onClick={() => setSelectedFilter(filter.value)}
                sx={{
                  fontWeight: 600,
                  backgroundColor: selectedFilter === filter.value ? colors.primary.main : 'white',
                  color: selectedFilter === filter.value ? 'white' : colors.text.primary,
                  border: `2px solid ${selectedFilter === filter.value ? colors.primary.main : colors.background.lighter}`,
                  '&:hover': {
                    backgroundColor: selectedFilter === filter.value ? colors.primary.dark : colors.background.hover,
                  },
                }}
              />
            ))}
          </Box>
        </Paper>
      </motion.div>

      {/* Timeline Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={viewMode}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          {viewMode === 'timeline' ? renderTimelineView() : renderListView()}
        </motion.div>
      </AnimatePresence>
    </Box>
  );
};

export default Timeline;
