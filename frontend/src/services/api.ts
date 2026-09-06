import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const apiClient = axios.create({ baseURL: API_BASE, headers: { 'Content-Type': 'application/json' } });

apiClient.interceptors.request.use((config) => {
  const stored = localStorage.getItem('auth-storage');
  if (stored) {
    const parsed = JSON.parse(stored);
    const token = parsed?.state?.token;
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  login: (username: string, password: string) => apiClient.post('/auth/login', { username, password }),
  me: () => apiClient.get('/auth/me'),
  logout: () => apiClient.post('/auth/logout'),
};

// Monitoring
export const monitoringApi = {
  getSessions: (params?: any) => apiClient.get('/monitoring/sessions', { params }),
  startSession: (data: any) => apiClient.post('/monitoring/sessions/start', data),
  stopSession: (id: string) => apiClient.put(`/monitoring/sessions/${id}/stop`),
  getSession: (id: string) => apiClient.get(`/monitoring/sessions/${id}`),
  startSimulator: (clientId: string) => apiClient.post('/monitoring/simulate/start', { client_id: clientId }),
  stopSimulator: (clientId: string) => apiClient.post(`/monitoring/simulate/stop/${clientId}`),
  getLiveData: (clientId: string) => apiClient.get(`/monitoring/live/${clientId}`),
};

// Signals
export const signalsApi = {
  getECG: (sessionId: string) => apiClient.get(`/signals/ecg/${sessionId}`),
  getPPG: (sessionId: string) => apiClient.get(`/signals/ppg/${sessionId}`),
  getSPO2: (sessionId: string) => apiClient.get(`/signals/spo2/${sessionId}`),
  getLiveECG: (clientId: string) => apiClient.get(`/signals/ecg/live/${clientId}`),
  getLivePPG: (clientId: string) => apiClient.get(`/signals/ppg/live/${clientId}`),
};

// Anomaly
export const anomalyApi = {
  getEvents: (params?: any) => apiClient.get('/anomaly/events', { params }),
  getEvent: (id: string) => apiClient.get(`/anomaly/events/${id}`),
  getTimeline: (params?: any) => apiClient.get('/anomaly/timeline', { params }),
  getCurrent: (clientId: string) => apiClient.get(`/anomaly/current/${clientId}`),
  getStats: () => apiClient.get('/anomaly/stats'),
};

// Baseline
export const baselineApi = {
  getBaseline: (userId: string) => apiClient.get(`/baseline/${userId}`),
  getDeviation: (userId: string) => apiClient.get(`/baseline/${userId}/deviation`),
  updateBaseline: (userId: string) => apiClient.put(`/baseline/${userId}/update`),
};

// Federated Learning
export const flApi = {
  getStatus: () => apiClient.get('/fl/status'),
  getRounds: (params?: any) => apiClient.get('/fl/rounds', { params }),
  getRound: (id: string) => apiClient.get(`/fl/rounds/${id}`),
  startTraining: (data: any) => apiClient.post('/fl/training/start', data),
  stopTraining: () => apiClient.post('/fl/training/stop'),
  getClients: () => apiClient.get('/fl/clients'),
  getClient: (id: string) => apiClient.get(`/fl/clients/${id}`),
  getAggregation: (roundId: string) => apiClient.get(`/fl/aggregation/${roundId}`),
  getGlobalModel: () => apiClient.get('/fl/global-model'),
  getModelHistory: () => apiClient.get('/fl/global-model/history'),
  getPersonalModels: () => apiClient.get('/fl/personal-models'),
  getPersonalModel: (userId: string) => apiClient.get(`/fl/personal-models/${userId}`),
};

// Experiments
export const experimentsApi = {
  getExperiments: () => apiClient.get('/experiments'),
  createExperiment: (data: any) => apiClient.post('/experiments', data),
  getExperiment: (id: string) => apiClient.get(`/experiments/${id}`),
  runExperiment: (id: string) => apiClient.post(`/experiments/${id}/run`),
  getResults: (id: string) => apiClient.get(`/experiments/${id}/results`),
  runRobustness: (data: any) => apiClient.post('/experiments/robustness/run', data),
  runAblation: (data: any) => apiClient.post('/experiments/ablation/run', data),
};

// Devices
export const devicesApi = {
  getDevices: () => apiClient.get('/devices'),
  createDevice: (data: any) => apiClient.post('/devices', data),
  getDevice: (id: string) => apiClient.get(`/devices/${id}`),
  updateDevice: (id: string, data: any) => apiClient.put(`/devices/${id}`, data),
  deleteDevice: (id: string) => apiClient.delete(`/devices/${id}`),
  connectDevice: (id: string) => apiClient.post(`/devices/${id}/connect`),
  disconnectDevice: (id: string) => apiClient.post(`/devices/${id}/disconnect`),
};

// Alerts
export const alertsApi = {
  getRules: () => apiClient.get('/alerts/rules'),
  createRule: (data: any) => apiClient.post('/alerts/rules', data),
  updateRule: (id: string, data: any) => apiClient.put(`/alerts/rules/${id}`, data),
  deleteRule: (id: string) => apiClient.delete(`/alerts/rules/${id}`),
  getNotifications: (params?: any) => apiClient.get('/alerts/notifications', { params }),
  markRead: (id: string) => apiClient.put(`/alerts/notifications/${id}/read`),
  markAllRead: () => apiClient.put('/alerts/notifications/read-all'),
  dismiss: (id: string) => apiClient.delete(`/alerts/notifications/${id}`),
};

// Reports
export const reportsApi = {
  generateReport: (data: any) => apiClient.post('/reports/generate', data),
  getReports: () => apiClient.get('/reports'),
  downloadReport: (id: string) => apiClient.get(`/reports/${id}/download`, { responseType: 'blob' }),
};

// System
export const systemApi = {
  getHealth: () => apiClient.get('/system/health'),
  getLogs: (params?: any) => apiClient.get('/system/logs', { params }),
  getStats: () => apiClient.get('/system/stats'),
  getSettings: () => apiClient.get('/system/settings'),
  updateSettings: (data: any) => apiClient.put('/system/settings', data),
};

export default apiClient;