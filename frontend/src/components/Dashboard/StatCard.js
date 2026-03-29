import React from 'react';
import { Card, CardContent, Typography, Box, alpha } from '@mui/material';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import colors from '../../theme/colors';

const StatCard = ({ title, value, icon, color, trend }) => {
  const isPositive = trend?.startsWith('+');

  return (
    <motion.div whileHover={{ y: -6 }} transition={{ type: 'spring', stiffness: 280 }}>
      <Card
        className="cyber-panel"
        sx={{
          height: '100%',
          position: 'relative',
          overflow: 'hidden',
          border: `1px solid ${alpha(color, 0.45)}`,
          background: `linear-gradient(145deg, ${alpha(color, 0.16)} 0%, ${alpha(colors.background.card, 0.85)} 70%)`,
          '&::after': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: 3,
            background: `linear-gradient(90deg, ${alpha(color, 0)} 0%, ${color} 50%, ${alpha(color, 0)} 100%)`,
          },
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ letterSpacing: '0.06em' }} gutterBottom>
                {title}
              </Typography>
              <Typography variant="h4" fontWeight={800} color={color} sx={{ mb: 1 }}>
                {value}
              </Typography>
              {trend && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  {isPositive ? (
                    <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
                  ) : (
                    <TrendingDown sx={{ fontSize: 16, color: 'error.main' }} />
                  )}
                  <Typography variant="caption" color={isPositive ? 'success.main' : 'error.main'} fontWeight={700}>
                    {trend}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    threat cycle
                  </Typography>
                </Box>
              )}
            </Box>
            <Box
              sx={{
                width: 54,
                height: 54,
                borderRadius: 2,
                display: 'grid',
                placeItems: 'center',
                bgcolor: alpha(color, 0.16),
                color,
                boxShadow: `0 0 16px ${alpha(color, 0.34)}`,
              }}
            >
              {icon}
            </Box>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default StatCard;
