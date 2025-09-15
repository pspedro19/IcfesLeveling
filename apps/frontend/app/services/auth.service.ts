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
      // Validate credentials before sending
      if (!credentials.username?.trim()) {
        throw new Error('El nombre de usuario es requerido');
      }
      if (!credentials.password) {
        throw new Error('La contraseña es requerida');
      }

      // Send form data as backend expects OAuth2PasswordRequestForm
      const formData = new URLSearchParams();
      formData.append('username', credentials.username.trim());
      formData.append('password', credentials.password);

      const response = await apiClient.post<LoginResponse>('/api/v1/auth-simple/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      // Store token and user data
      if (response.access_token) {
        tokenManager.setToken(response.access_token);
        
        // Store additional user data in localStorage
        if (response.user) {
          localStorage.setItem('currentUser', JSON.stringify(response.user));
        }
      }
      
      return response;
    } catch (error: any) {
      console.error('Login error:', error);
      
      // Enhanced error handling with user-friendly messages
      if (error.response?.status === 401) {
        const detail = error.response?.data?.detail || '';
        if (detail.includes('Usuario no encontrado') || detail.includes('not found')) {
          throw new Error('Usuario no encontrado. Verifica tu nombre de usuario.');
        } else if (detail.includes('Contraseña incorrecta') || detail.includes('password')) {
          throw new Error('Contraseña incorrecta. Intenta nuevamente.');
        } else {
          throw new Error('Credenciales incorrectas. Verifica tu usuario y contraseña.');
        }
      } else if (error.response?.status === 422) {
        throw new Error('Datos de login inválidos. Verifica los campos.');
      } else if (error.response?.status === 500) {
        throw new Error('Error del servidor. Intenta nuevamente en unos momentos.');
      } else if (error.code === 'NETWORK_ERROR' || !error.response) {
        throw new Error('Sin conexión al servidor. Verifica tu conexión a internet.');
      } else {
        throw new Error(error.response?.data?.detail || error.message || 'Error desconocido durante el login');
      }
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
    try {
      // Clear token and cached data
      tokenManager.removeToken();
      
      if (typeof window !== 'undefined') {
        // Clear all user-related data from localStorage
        localStorage.removeItem('currentUser');
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        localStorage.removeItem('heroClass');
        localStorage.removeItem('userSubjects');
        localStorage.removeItem('auth-storage');
        
        // Clear session storage as well
        sessionStorage.clear();
        
        console.log('✅ Logout successful - all user data cleared');
      }
    } catch (error) {
      console.error('Error during logout:', error);
    }
  }
  
  isAuthenticated(): boolean {
    const token = tokenManager.getToken();
    if (!token) return false;
    
    try {
      // Check if token is expired (basic check)
      const user = this.getCurrentUserFromStorage();
      return !!user;
    } catch (error) {
      console.error('Error checking authentication:', error);
      return false;
    }
  }

  getCurrentUserFromStorage(): any {
    if (typeof window === 'undefined') return null;
    
    try {
      const userStr = localStorage.getItem('currentUser') || localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Error getting user from storage:', error);
      return null;
    }
  }

  // Helper method to check if user has specific permissions
  hasPermission(permission: string): boolean {
    const user = this.getCurrentUserFromStorage();
    if (!user) return false;
    
    // Admin users have all permissions
    if (user.premium_plan === 'premium' || user.level >= 50) {
      return true;
    }
    
    // Add more permission logic as needed
    return false;
  }
}

export const authService = new AuthService();