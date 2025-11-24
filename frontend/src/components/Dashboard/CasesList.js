import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Box,
} from '@mui/material';
import { Visibility, MoreVert } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import colors from '../../theme/colors';

const CasesList = ({ cases = [] }) => {
  const navigate = useNavigate();

  const getStatusColor = (status) => {
    const statusColors = {
      active: colors.status.success,
      pending: colors.status.warning,
      closed: colors.text.disabled,
      critical: colors.status.critical,
    };
    return statusColors[status?.toLowerCase()] || colors.text.secondary;
  };

  const mockCases = cases.length > 0 ? cases : [
    { id: 1, name: 'Case-2024-001', status: 'Active', artifacts: 1250, date: '2024-11-20' },
    { id: 2, name: 'Case-2024-002', status: 'Pending', artifacts: 850, date: '2024-11-19' },
    { id: 3, name: 'Case-2024-003', status: 'Critical', artifacts: 2100, date: '2024-11-18' },
    { id: 4, name: 'Case-2024-004', status: 'Active', artifacts: 950, date: '2024-11-17' },
    { id: 5, name: 'Case-2024-005', status: 'Closed', artifacts: 1500, date: '2024-11-15' },
  ];

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Box>
            <Typography variant="h6" fontWeight={600}>
              Recent Cases
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Latest forensic investigations
            </Typography>
          </Box>
        </Box>

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Case ID</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Artifacts</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockCases.map((caseItem, index) => (
                <motion.tr
                  key={caseItem.id}
                  component={TableRow}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 }}
                  whileHover={{ backgroundColor: colors.background.card }}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/cases/${caseItem.id}`)}
                >
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {caseItem.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={caseItem.status}
                      size="small"
                      sx={{
                        bgcolor: `${getStatusColor(caseItem.status)}20`,
                        color: getStatusColor(caseItem.status),
                        fontWeight: 500,
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {caseItem.artifacts.toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(caseItem.date).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/cases/${caseItem.id}`);
                      }}
                    >
                      <Visibility fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={(e) => e.stopPropagation()}>
                      <MoreVert fontSize="small" />
                    </IconButton>
                  </TableCell>
                </motion.tr>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

export default CasesList;
