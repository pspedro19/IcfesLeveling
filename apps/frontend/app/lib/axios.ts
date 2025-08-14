// apps/frontend/app/lib/axios.ts
import axios, { AxiosError, AxiosInstance } from 'axios';

// API base URL from environment or default - FIXED to avoid undefined
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
const FULL_API_URL = `${API_BASE_URL}/api/v1`;

console.log('🔧 Axios Config:', {
  API_BASE_URL,
  FULL_API_URL,
  ENV: process.env.NODE_ENV
});

// Create axios instance with proper configuration
const api: AxiosInstance = axios.create({
  baseURL: FULL_API_URL,
  timeout: 15000, // 15s
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CORS with credentials
});

// Token management utilities
export const tokenManager = {
  getToken: (): string | null => {
    if (typeof window !== 'undefined') {
      // Try both keys for compatibility
      return localStorage.getItem('access_token') || 
             localStorage.getItem('token') || 
             null;
    }
    return null;
  },
  
  setToken: (token: string): void => {
    if (typeof window !== 'undefined') {
      // Save in both keys for compatibility
      localStorage.setItem('access_token', token);
      localStorage.setItem('token', token);
    }
  },
  
  removeToken: (): void => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('token');
    }
  },
};

// Request interceptor - adds auth token
api.interceptors.request.use(
  (config) => {
    const token = tokenManager.getToken();
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 API Request:', {
        method: config.method?.toUpperCase(),
        url: config.url,
        baseURL: config.baseURL,
        hasToken: !!token
      });
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - handles errors
api.interceptors.response.use(
  (response) => {
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ API Response:', {
        url: response.config.url,
        status: response.status,
        data: response.data
      });
    }
    return response;
  },
  
  async (error: AxiosError) => {
    // Don't break for non-critical endpoints
    const ignoredEndpoints = ['/analytics/events', '/health'];
    const isIgnored = ignoredEndpoints.some(endpoint => 
      error.config?.url?.includes(endpoint)
    );
    
    if (isIgnored) {
      console.warn('⚠️ Non-critical endpoint failed (ignored):', error.config?.url);
      return Promise.resolve({ data: { status: 'ignored' } });
    }

    // Log error details
    if (process.env.NODE_ENV === 'development') {
      console.error('❌ API Error:', {
        status: error.response?.status,
        data: error.response?.data,
        url: error.config?.url,
        message: error.message
      });
    }

    // Handle specific error codes
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Unauthorized - clear token and redirect
          tokenManager.removeToken();
          if (typeof window !== 'undefined' && 
              window.location.pathname !== '/' &&
              window.location.pathname !== '/login') {
            window.location.href = '/';
          }
          break;
          
        case 403:
          console.error('Access forbidden');
          break;
          
        case 404:
          console.error('Resource not found:', error.config?.url);
          break;
          
        case 422:
          console.error('Validation error:', error.response.data);
          break;
          
        case 500:
        case 502:
        case 503:
          console.error('Server error - backend may be down');
          break;
      }
    } else if (error.request) {
      console.error('Network error - no response received. Is the backend running?');
    }
    
    return Promise.reject(error);
  }
);

// Typed API client methods
export const apiClient = {
  // GET request
  get: async <T = any>(url: string, config = {}): Promise<T> => {
    const response = await api.get<T>(url, config);
    return response.data;
  },
  
  // POST request
  post: async <T = any>(url: string, data?: any, config = {}): Promise<T> => {
    const response = await api.post<T>(url, data, config);
    return response.data;
  },
  
  // PUT request
  put: async <T = any>(url: string, data?: any, config = {}): Promise<T> => {
    const response = await api.put<T>(url, data, config);
    return response.data;
  },
  
  // PATCH request
  patch: async <T = any>(url: string, data?: any, config = {}): Promise<T> => {
    const response = await api.patch<T>(url, data, config);
    return response.data;
  },
  
  // DELETE request
  delete: async <T = any>(url: string, config = {}): Promise<T> => {
    const response = await api.delete<T>(url, config);
    return response.data;
  },
};

// Export default instance
export default api;