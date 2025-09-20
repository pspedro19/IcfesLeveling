// Servicio de autenticación simplificado para evitar errores de webpack
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: any;
}

class SimpleAuthService {
  private getApiUrl(): string {
    if (typeof window !== 'undefined') {
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      return `${protocol}//${hostname}:4000`;
    }
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
  }

  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      if (!credentials.username?.trim()) {
        throw new Error('El nombre de usuario es requerido');
      }
      if (!credentials.password) {
        throw new Error('La contraseña es requerida');
      }

      const apiUrl = this.getApiUrl();

      const formData = new URLSearchParams();
      formData.append('username', credentials.username.trim());
      formData.append('password', credentials.password);

      const response = await fetch(`${apiUrl}/api/v1/auth-simple/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        if (response.status === 401) {
          const detail = errorData.detail || '';
          if (detail.includes('Usuario no encontrado')) {
            throw new Error('Usuario no encontrado. Verifica tu nombre de usuario.');
          } else if (detail.includes('Contraseña incorrecta')) {
            throw new Error('Contraseña incorrecta. Intenta nuevamente.');
          } else {
            throw new Error('Credenciales incorrectas. Verifica tu usuario y contraseña.');
          }
        } else if (response.status === 422) {
          throw new Error('Datos de login inválidos. Verifica los campos.');
        } else if (response.status === 500) {
          throw new Error('Error del servidor. Intenta nuevamente en unos momentos.');
        } else {
          throw new Error('Sin conexión al servidor. Verifica tu conexión a internet.');
        }
      }

      const data = await response.json();

      // Store token and user data
      if (data.access_token && typeof window !== 'undefined') {
        localStorage.setItem('access_token', data.access_token);
        if (data.user) {
          localStorage.setItem('currentUser', JSON.stringify(data.user));
        }
      }

      return data;
    } catch (error: any) {
      console.error('Login error:', error);
      throw error;
    }
  }

  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('currentUser');
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      console.log('✅ Logout successful');
    }
  }

  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    const token = localStorage.getItem('access_token');
    return !!token;
  }

  getCurrentUser(): any {
    if (typeof window === 'undefined') return null;
    try {
      const userStr = localStorage.getItem('currentUser') || localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('Error getting user from storage:', error);
      return null;
    }
  }
}

export const authService = new SimpleAuthService();