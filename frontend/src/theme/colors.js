// Vibrant color palette for forensic investigation app
// White background with colorful, professional accents

export const colors = {
  // Primary colors - Vibrant blues
  primary: {
    main: '#2563EB',      // Vibrant blue
    light: '#60A5FA',     // Light blue
    dark: '#1E40AF',      // Dark blue
    contrastText: '#FFFFFF',
  },
  
  // Secondary colors - Purple accents
  secondary: {
    main: '#8B5CF6',      // Vibrant purple
    light: '#A78BFA',     // Light purple
    dark: '#6D28D9',      // Dark purple
    contrastText: '#FFFFFF',
  },
  
  // Accent colors - Vibrant and diverse
  accent: {
    cyan: '#06B6D4',      // Cyan
    teal: '#14B8A6',      // Teal
    emerald: '#10B981',   // Emerald green
    amber: '#F59E0B',     // Amber
    rose: '#F43F5E',      // Rose
    pink: '#EC4899',      // Pink
    indigo: '#6366F1',    // Indigo
    orange: '#F97316',    // Orange
  },
  
  // Background colors - White with subtle shades
  background: {
    default: '#FFFFFF',   // Pure white
    paper: '#FFFFFF',     // White
    light: '#F8FAFC',     // Very light gray-blue
    lighter: '#F1F5F9',   // Light gray-blue
    card: '#FAFBFC',      // Slightly off-white
    hover: '#F3F4F6',     // Hover state
  },
  
  // Text colors - Dark and readable
  text: {
    primary: '#0F172A',   // Very dark blue-gray
    secondary: '#475569', // Medium gray
    disabled: '#94A3B8',  // Light gray
    hint: '#CBD5E1',      // Very light gray
  },
  
  // Status colors - Vibrant and clear
  status: {
    critical: '#EF4444',  // Bright red
    warning: '#F59E0B',   // Amber
    info: '#3B82F6',      // Blue
    success: '#10B981',   // Green
  },
  
  // Chart colors - Vibrant and distinguishable
  chart: [
    '#2563EB',  // Blue
    '#8B5CF6',  // Purple
    '#EC4899',  // Pink
    '#F59E0B',  // Amber
    '#10B981',  // Green
    '#06B6D4',  // Cyan
    '#F97316',  // Orange
    '#6366F1',  // Indigo
    '#14B8A6',  // Teal
    '#F43F5E',  // Rose
  ],
  
  // Gradient combinations - Vibrant gradients
  gradients: {
    primary: 'linear-gradient(135deg, #2563EB 0%, #8B5CF6 100%)',
    success: 'linear-gradient(135deg, #10B981 0%, #14B8A6 100%)',
    warning: 'linear-gradient(135deg, #F59E0B 0%, #F97316 100%)',
    danger: 'linear-gradient(135deg, #EF4444 0%, #F43F5E 100%)',
    cool: 'linear-gradient(135deg, #06B6D4 0%, #2563EB 100%)',
    warm: 'linear-gradient(135deg, #F97316 0%, #EC4899 100%)',
  },
  
  // Artifact type colors - Specific colors for each artifact type
  artifacts: {
    browser: '#3B82F6',      // Blue
    registry: '#8B5CF6',     // Purple
    filesystem: '#10B981',   // Green
    network: '#06B6D4',      // Cyan
    usb: '#F59E0B',          // Amber
    events: '#EC4899',       // Pink
    deleted: '#EF4444',      // Red
    timeline: '#6366F1',     // Indigo
    programs: '#14B8A6',     // Teal
    activity: '#F97316',     // Orange
  },
};

export default colors;
