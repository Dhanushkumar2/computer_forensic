import React, { useEffect, useState } from 'react';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import Sidebar from './Sidebar';
import Header from './Header';
import { motion } from 'framer-motion';
import colors from '../../theme/colors';

const Layout = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const drawerWidth = 280;
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  useEffect(() => {
    setSidebarOpen(!isMobile);
  }, [isMobile]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh',
        bgcolor: 'background.default',
        backgroundImage: `radial-gradient(circle at 8% 2%, rgba(0,229,255,0.14), transparent 20%), radial-gradient(circle at 88% 92%, rgba(155,109,255,0.14), transparent 22%)`,
      }}
    >
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isMobile={isMobile}
        drawerWidth={drawerWidth}
      />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          transition: 'margin 0.3s ease',
          marginLeft: sidebarOpen && !isMobile ? `${drawerWidth}px` : 0,
        }}
      >
        <Header
          onMenuClick={toggleSidebar}
          drawerWidth={drawerWidth}
          sidebarOpen={sidebarOpen}
          isMobile={isMobile}
        />

        <Box
          sx={{
            flexGrow: 1,
            p: { xs: 1.5, sm: 2.5, md: 3.5 },
            mt: { xs: '56px', sm: '64px' },
            position: 'relative',
            '&::before': {
              content: '""',
              position: 'absolute',
              inset: 0,
              pointerEvents: 'none',
              backgroundImage:
                'linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px)',
              backgroundSize: '26px 26px',
            },
          }}
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.35 }}
            style={{ position: 'relative', zIndex: 1, color: colors.text.primary }}
          >
            {children}
          </motion.div>
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;
