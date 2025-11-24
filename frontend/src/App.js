import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AnimatePresence } from 'framer-motion';

import theme from './theme/theme';
import Layout from './components/Layout/Layout';
import Login from './pages/Login/Login';
import CaseSelection from './pages/CaseSelection/CaseSelection';
import Dashboard from './pages/Dashboard/Dashboard';
import Cases from './pages/Cases/Cases';
import CaseDetails from './pages/Cases/CaseDetails';
import Artifacts from './pages/Artifacts/Artifacts';
import Timeline from './pages/Timeline/Timeline';
import Analytics from './pages/Analytics/Analytics';
import Reports from './pages/Reports/Reports';
import Settings from './pages/Settings/Settings';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  const selectedCase = localStorage.getItem('selectedCase');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  // For routes that need a selected case
  if (window.location.pathname !== '/case-selection' && !selectedCase) {
    return <Navigate to="/case-selection" replace />;
  }
  
  return children;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AnimatePresence mode="wait">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes */}
            <Route
              path="/case-selection"
              element={
                <ProtectedRoute>
                  <CaseSelection />
                </ProtectedRoute>
              }
            />
            
            {/* Routes with Layout (require case selection) */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/cases" element={<Cases />} />
                      <Route path="/cases/:id" element={<CaseDetails />} />
                      <Route path="/artifacts" element={<Artifacts />} />
                      <Route path="/timeline" element={<Timeline />} />
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/reports" element={<Reports />} />
                      <Route path="/settings" element={<Settings />} />
                    </Routes>
                  </Layout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AnimatePresence>
      </Router>
    </ThemeProvider>
  );
}

export default App;
