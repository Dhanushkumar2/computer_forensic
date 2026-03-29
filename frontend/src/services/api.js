import axios from 'axios';

const normalizeApiUrl = (url) => {
  if (!url) return url;
  return url.replace('http://localhost:8000', 'http://127.0.0.1:8000');
};

const resolveApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return normalizeApiUrl(process.env.REACT_APP_API_URL);
  }
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    const apiHost = hostname === 'localhost' ? '127.0.0.1' : hostname;
    return `${protocol}//${apiHost}:8000/api`;
  }
  return 'http://127.0.0.1:8000/api';
};

export const API_BASE_URL = resolveApiBaseUrl();

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
  
  // Disk Images
  getDiskImages: () => api.get('/disk-images/'),
  
  // Cases
  getCases: (params) => api.get('/cases/', { params }),
  getMongoCases: () => api.get('/cases/mongo-cases/'),
  importMongoCase: (caseId) => api.post('/cases/import-mongo/', { case_id: caseId }),
  getCase: (id) => api.get(`/cases/${id}/`),
  getCaseSummary: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/summary/`);
  },
  createCase: (data) => api.post('/cases/', data),
  updateCase: (id, data) => api.put(`/cases/${id}/`, data),
  deleteCase: (id) => api.delete(`/cases/${id}/`),
  getProcessingStatus: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/processing-status/`);
  },
  getBasicInfo: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/basic-info/`);
  },
  getRawExtractionStatus: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/raw-extraction-status/`);
  },
  extractRawChunk: (caseId, payload) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.post(`/cases/${id}/extract-raw/`, payload);
  },
  
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

  // Event logs
  getEventLogs: (caseId, params) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/event-logs/`, { params });
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
  getInstalledPrograms: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/installed-programs/`);
  },
  
  // User Activity
  getUserActivity: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/user-activity/`);
  },

  // Android artifacts
  getAndroidArtifacts: (caseId, params) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/android-artifacts/`, { params });
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
  
  // ML-based Anomaly Detection
  analyzeAnomalies: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.post(`/cases/${id}/ml-infer/`);
  },
  getAnomalyDetails: (caseId, params) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/ml-anomalies/`, { params });
  },
  runAndroidMlInfer: (caseId, payload) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.post(`/cases/${id}/android-ml-infer/`, payload);
  },
  getAndroidMlAnomalies: (caseId, params) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.get(`/cases/${id}/android-ml-anomalies/`, { params });
  },
  getAnomalyServiceStatus: () => {
    return api.get('/cases/anomaly_service_status/');
  },
  
  // Re-extraction
  reExtractCase: (caseId) => {
    const id = caseId || forensicAPI.getCurrentCaseId();
    return api.post(`/cases/${id}/re-extract/`);
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
