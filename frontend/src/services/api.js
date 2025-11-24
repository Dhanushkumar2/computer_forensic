import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper to get current case
const getCurrentCase = () => {
  const caseData = localStorage.getItem('selectedCase');
  return caseData ? JSON.parse(caseData) : null;
};

// Request interceptor for adding auth token and case context
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add current case ID to headers
    const currentCase = getCurrentCase();
    if (currentCase) {
      config.headers['X-Case-ID'] = currentCase.case_id;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('selectedCase');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const forensicAPI = {
  // Helper to get current case ID
  getCurrentCaseId: () => {
    const currentCase = getCurrentCase();
    return currentCase ? currentCase.id : null;
  },
  
  // Dashboard
  getDashboardStats: () => {
    const caseId = forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${caseId}/statistics/`);
  },
  getRecentCases: () => api.get('/cases/recent/'),
  
  // Cases
  getCases: (params) => api.get('/cases/', { params }),
  getCase: (id) => api.get(`/cases/${id}/`),
  createCase: (data) => api.post('/cases/', data),
  updateCase: (id, data) => api.put(`/cases/${id}/`, data),
  deleteCase: (id) => api.delete(`/cases/${id}/`),
  
  // Artifacts (use current case if caseId not provided)
  getArtifacts: (caseId, params) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/artifacts/`, { params });
  },
  getArtifactDetails: (id) => api.get(`/artifacts/${id}/`),
  searchArtifacts: (query) => {
    const caseId = forensicAPI.getCurrentCaseId();
    return api.post(`/cases/${caseId}/search/`, query);
  },
  
  // Browser artifacts
  getBrowserHistory: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/browser-history/`);
  },
  getBrowserDownloads: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/browser-downloads/`);
  },
  getBrowserCookies: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/browser-cookies/`);
  },
  
  // Registry artifacts
  getRegistryData: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/registry/`);
  },
  getUSBDevices: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/usb-devices/`);
  },
  
  // File system
  getFileSystem: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/filesystem/`);
  },
  getDeletedFiles: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/deleted-files/`);
  },
  
  // User Activity
  getUserActivity: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/user-activity/`);
  },
  
  // Timeline
  getTimeline: (caseId, params) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/timeline/`, { params });
  },
  
  // Reports
  generateReport: (caseId, format) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.post(`/cases/${id}/report/`, { format });
  },
  getReports: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/reports/`);
  },
  
  // Analytics
  getAnomalies: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/suspicious-activity/`);
  },
  getStatistics: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/statistics/`);
  },
  getBehaviorAnalysis: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/behavior-analysis/`);
  },
  getNetworkAnalysis: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/network-analysis/`);
  },
  
  // Export
  exportData: (caseId, format) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/export/`, {
      params: { format },
      responseType: 'blob',
    });
  },
};

export default api;
