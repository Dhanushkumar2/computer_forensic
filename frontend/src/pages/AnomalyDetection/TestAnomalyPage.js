import React from 'react';
import { Container, Typography, Box, Button } from '@mui/material';
import { Security } from '@mui/icons-material';

const TestAnomalyPage = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Security sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
        <Typography variant="h3" gutterBottom>
          AI-Powered Anomaly Detection
        </Typography>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          Test Page - ML Integration Working!
        </Typography>
        <Button variant="contained" size="large" sx={{ mt: 3 }}>
          Test ML Analysis
        </Button>
      </Box>
    </Container>
  );
};

export default TestAnomalyPage;