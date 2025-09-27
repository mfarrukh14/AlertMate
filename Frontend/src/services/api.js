import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth services
export const authService = {
  signup: (userData) => api.post('/auth/signup', userData),
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
};

// Chat service
export const chatService = {
  sendMessage: (messageData) => api.post('/chat', messageData),
};

// Admin services
export const adminService = {
  getStats: () => api.get('/admin/stats'),
  getQueue: () => api.get('/admin/queue'),
  getActivity: () => api.get('/admin/activity'),
};

export default api;