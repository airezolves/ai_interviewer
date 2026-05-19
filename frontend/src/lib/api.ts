"""API client for frontend-to-backend communication."""

import axios from 'axios';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

const http = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 minutes for kit generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
http.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle errors
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
      }
    }
    const message = error.response?.data?.error || error.message || 'Request failed';
    return Promise.reject(new Error(message));
  }
);

export const apiClient = {
  // Auth
  async register(data: { email: string; name: string; password: string }) {
    const resp = await http.post('/api/auth/register', data);
    return resp.data;
  },

  async login(data: { email: string; password: string }) {
    const resp = await http.post('/api/auth/login', data);
    return resp.data;
  },

  // Resume
  async parseResumeFile(formData: FormData) {
    const resp = await http.post('/api/resume/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return resp.data;
  },

  async parseResumeText(text: string) {
    const resp = await http.post('/api/resume/parse-text', { text });
    return resp.data;
  },

  // Kit Generation
  async generateKit(data: { jd_text: string; resume_data: any; role_type: string }) {
    const resp = await http.post('/api/ai/generate-kit-full', data);
    return resp.data;
  },

  // Kit Management
  async listKits(page: number = 1) {
    const resp = await http.get(`/api/kits?page=${page}`);
    return resp.data;
  },

  async getKit(kitId: string) {
    const resp = await http.get(`/api/kits/${kitId}`);
    return resp.data;
  },

  async deleteKit(kitId: string) {
    const resp = await http.delete(`/api/kits/${kitId}`);
    return resp.data;
  },

  // PDF
  async generatePDF(kitId: string, kitData: any, title: string) {
    const resp = await http.post('/api/pdf/generate', {
      kit_id: kitId,
      kit_data: kitData,
      title,
    });
    return resp.data;
  },

  async downloadPDF(jobId: string) {
    const resp = await http.get(`/api/pdf/${jobId}/download`, {
      responseType: 'blob',
    });
    return resp.data;
  },
};
