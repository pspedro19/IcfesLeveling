import { apiClient, tokenManager } from '@/lib/axios';
import { UserResponse, LoginResponse } from '@/types/auth';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  display_name?: string;
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      // API expects form data for OAuth2
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      // Intentar primero con la ruta simplificada para testing
      const response = await apiClient.post<LoginResponse>('/auth-simple/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      // Store token
      if (response.access_token) {
        tokenManager.setToken(response.access_token);
      }
      
      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }
  
  async register(data: RegisterData): Promise<UserResponse> {
    try {
      const response = await apiClient.post<UserResponse>('/auth/register', data);
      return response;
    } catch (error) {
      console.error('Register error:', error);
      throw error;
    }
  }
  
  async getCurrentUser(): Promise<UserResponse> {
    try {
      const response = await apiClient.get<UserResponse>('/auth/me');
      return response;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  }
  
  async logout(): Promise<void> {
    tokenManager.removeToken();
    // Clear any cached data
    if (typeof window !== 'undefined') {
      localStorage.removeItem('currentUser');
      localStorage.removeItem('heroClass');
      localStorage.removeItem('userSubjects');
      // Redirect to home
      window.location.href = '/';
    }
  }
  
  isAuthenticated(): boolean {
    return !!tokenManager.getToken();
  }
}

export const authService = new AuthService();