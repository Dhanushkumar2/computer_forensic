import React from 'react';
import { Box, Typography } from '@mui/material';
import { motion } from 'framer-motion';
import colors from '../../theme/colors';

const Settings = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Box>
        <Typography variant="h4" fontWeight={700} color={colors.text.primary}>
          Settings
        </Typography>
        <Typography variant="body1" color={colors.text.secondary} sx={{ mt: 2 }}>
          Configure application settings and preferences.
        </Typography>
      </Box>
    </motion.div>
  );
};

export default Settings;
