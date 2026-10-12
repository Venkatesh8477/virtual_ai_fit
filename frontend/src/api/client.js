import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token automatically
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('tryon_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const authAPI = {
  register: (name, email, password) => client.post('/api/auth/register', { name, email, password }),
  login: (email, password) => client.post('/api/auth/login', { email, password }),
  getProfile: () => client.get('/api/auth/me'),
};

export const tryonAPI = {
  analyzePerson: (personImageFile) => {
    const formData = new FormData();
    formData.append('person_image', personImageFile);
    return client.post('/api/tryon/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  generateTryOn: (personFile, dressFile, colabUrl = '') => {
    const formData = new FormData();
    formData.append('person_image', personFile);
    formData.append('dress_image', dressFile);
    if (colabUrl) {
      formData.append('colab_url', colabUrl);
    }
    return client.post('/api/tryon/generate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const historyAPI = {
  getHistory: () => client.get('/api/history'),
  deleteHistoryItem: (itemId) => client.delete(`/api/history/${itemId}`),
};

export default client;
