/**
 * Authentication service tests
 */
import { AuthService } from '@/services/auth.service';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
  });

  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const mockResponse = {
        data: {
          access_token: 'valid-token',
          token_type: 'bearer',
          user: {
            id: 'user-123',
            username: 'testuser',
            email: 'test@example.com',
            display_name: 'Test User',
            rank: 'B',
            level: 5,
          }
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await AuthService.login('testuser', 'password123');

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/login', {
        username: 'testuser',
        password: 'password123'
      });

      expect(result).toEqual(mockResponse.data);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'valid-token');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockResponse.data.user));
    });

    it('should handle login failure with invalid credentials', async () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            detail: 'Invalid credentials'
          }
        }
      };

      mockedAxios.post.mockRejectedValue(mockError);

      await expect(AuthService.login('wronguser', 'wrongpass')).rejects.toThrow('Invalid credentials');
      expect(localStorageMock.setItem).not.toHaveBeenCalled();
    });

    it('should handle network errors during login', async () => {
      const networkError = new Error('Network Error');
      mockedAxios.post.mockRejectedValue(networkError);

      await expect(AuthService.login('testuser', 'password123')).rejects.toThrow('Network Error');
    });

    it('should handle server errors during login', async () => {
      const serverError = {
        response: {
          status: 500,
          data: {
            detail: 'Internal server error'
          }
        }
      };

      mockedAxios.post.mockRejectedValue(serverError);

      await expect(AuthService.login('testuser', 'password123')).rejects.toThrow('Internal server error');
    });
  });

  describe('register', () => {
    it('should register a new user successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'new-user-token',
          token_type: 'bearer',
          user: {
            id: 'user-456',
            username: 'newuser',
            email: 'newuser@example.com',
            display_name: 'New User',
            rank: 'E',
            level: 1,
          }
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const userData = {
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'securepass123',
        display_name: 'New User'
      };

      const result = await AuthService.register(userData);

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/register', userData);
      expect(result).toEqual(mockResponse.data);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-user-token');
    });

    it('should handle registration failure with duplicate username', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            detail: 'Username already exists'
          }
        }
      };

      mockedAxios.post.mockRejectedValue(mockError);

      const userData = {
        username: 'existinguser',
        email: 'test@example.com',
        password: 'password123',
        display_name: 'Test User'
      };

      await expect(AuthService.register(userData)).rejects.toThrow('Username already exists');
    });

    it('should validate email format before registration', async () => {
      const userData = {
        username: 'testuser',
        email: 'invalid-email',
        password: 'password123',
        display_name: 'Test User'
      };

      await expect(AuthService.register(userData)).rejects.toThrow('Invalid email format');
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });

    it('should validate password strength before registration', async () => {
      const userData = {
        username: 'testuser',
        email: 'test@example.com',
        password: '123', // Too weak
        display_name: 'Test User'
      };

      await expect(AuthService.register(userData)).rejects.toThrow('Password too weak');
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });
  });

  describe('logout', () => {
    it('should logout and clear local storage', async () => {
      localStorageMock.getItem.mockReturnValue('valid-token');
      mockedAxios.post.mockResolvedValue({ data: { message: 'Logged out successfully' } });

      await AuthService.logout();

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/logout');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user');
    });

    it('should clear local storage even if API call fails', async () => {
      localStorageMock.getItem.mockReturnValue('invalid-token');
      mockedAxios.post.mockRejectedValue(new Error('Token invalid'));

      await AuthService.logout();

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user');
    });
  });

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      const mockResponse = {
        data: {
          access_token: 'new-refreshed-token',
          token_type: 'bearer'
        }
      };

      localStorageMock.getItem.mockReturnValue('old-token');
      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await AuthService.refreshToken();

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/refresh');
      expect(result).toEqual(mockResponse.data);
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-refreshed-token');
    });

    it('should handle refresh token failure', async () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            detail: 'Token expired'
          }
        }
      };

      localStorageMock.getItem.mockReturnValue('expired-token');
      mockedAxios.post.mockRejectedValue(mockError);

      await expect(AuthService.refreshToken()).rejects.toThrow('Token expired');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('user');
    });
  });

  describe('getCurrentUser', () => {
    it('should get current user info successfully', async () => {
      const mockResponse = {
        data: {
          id: 'user-123',
          username: 'testuser',
          email: 'test@example.com',
          display_name: 'Test User',
          rank: 'B',
          level: 5,
          xp: 1250,
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await AuthService.getCurrentUser();

      expect(mockedAxios.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle unauthorized access', async () => {
      const mockError = {
        response: {
          status: 401,
          data: {
            detail: 'Token invalid'
          }
        }
      };

      mockedAxios.get.mockRejectedValue(mockError);

      await expect(AuthService.getCurrentUser()).rejects.toThrow('Token invalid');
    });
  });

  describe('token management', () => {
    it('should get token from localStorage', () => {
      localStorageMock.getItem.mockReturnValue('stored-token');

      const token = AuthService.getToken();

      expect(localStorageMock.getItem).toHaveBeenCalledWith('access_token');
      expect(token).toBe('stored-token');
    });

    it('should return null when no token stored', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const token = AuthService.getToken();

      expect(token).toBeNull();
    });

    it('should check if user is authenticated', () => {
      localStorageMock.getItem.mockReturnValue('valid-token');

      const isAuth = AuthService.isAuthenticated();

      expect(isAuth).toBe(true);
    });

    it('should return false when not authenticated', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const isAuth = AuthService.isAuthenticated();

      expect(isAuth).toBe(false);
    });

    it('should get stored user data', () => {
      const mockUser = {
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com'
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser));

      const user = AuthService.getStoredUser();

      expect(user).toEqual(mockUser);
    });

    it('should return null when no user stored', () => {
      localStorageMock.getItem.mockReturnValue(null);

      const user = AuthService.getStoredUser();

      expect(user).toBeNull();
    });

    it('should handle corrupted user data', () => {
      localStorageMock.getItem.mockReturnValue('corrupted-json');

      const user = AuthService.getStoredUser();

      expect(user).toBeNull();
    });
  });

  describe('password change', () => {
    it('should change password successfully', async () => {
      const mockResponse = {
        data: {
          message: 'Password changed successfully'
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await AuthService.changePassword('oldpass123', 'newpass456');

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/change-password', {
        old_password: 'oldpass123',
        new_password: 'newpass456'
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle incorrect old password', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            detail: 'Current password is incorrect'
          }
        }
      };

      mockedAxios.post.mockRejectedValue(mockError);

      await expect(AuthService.changePassword('wrongpass', 'newpass456')).rejects.toThrow('Current password is incorrect');
    });
  });

  describe('password reset', () => {
    it('should request password reset successfully', async () => {
      const mockResponse = {
        data: {
          message: 'Password reset email sent'
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await AuthService.requestPasswordReset('test@example.com');

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/reset-password-request', {
        email: 'test@example.com'
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle non-existent email', async () => {
      const mockError = {
        response: {
          status: 404,
          data: {
            detail: 'Email not found'
          }
        }
      };

      mockedAxios.post.mockRejectedValue(mockError);

      await expect(AuthService.requestPasswordReset('nonexistent@example.com')).rejects.toThrow('Email not found');
    });

    it('should reset password with token successfully', async () => {
      const mockResponse = {
        data: {
          message: 'Password reset successfully'
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await AuthService.resetPassword('reset-token-123', 'newpassword123');

      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/reset-password', {
        token: 'reset-token-123',
        new_password: 'newpassword123'
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should handle invalid reset token', async () => {
      const mockError = {
        response: {
          status: 400,
          data: {
            detail: 'Invalid or expired reset token'
          }
        }
      };

      mockedAxios.post.mockRejectedValue(mockError);

      await expect(AuthService.resetPassword('invalid-token', 'newpass123')).rejects.toThrow('Invalid or expired reset token');
    });
  });

  describe('automatic token refresh', () => {
    it('should automatically refresh token before expiry', async () => {
      // Mock token that expires in 1 minute
      const tokenPayload = {
        exp: Math.floor(Date.now() / 1000) + 60, // 1 minute from now
        sub: 'user-123'
      };
      
      const mockToken = `header.${btoa(JSON.stringify(tokenPayload))}.signature`;
      localStorageMock.getItem.mockReturnValue(mockToken);

      const mockRefreshResponse = {
        data: {
          access_token: 'new-auto-refreshed-token',
          token_type: 'bearer'
        }
      };
      mockedAxios.post.mockResolvedValue(mockRefreshResponse);

      const result = await AuthService.checkAndRefreshToken();

      expect(result).toBe(true);
      expect(mockedAxios.post).toHaveBeenCalledWith('/auth/refresh');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('access_token', 'new-auto-refreshed-token');
    });

    it('should not refresh token if not near expiry', async () => {
      // Mock token that expires in 1 hour
      const tokenPayload = {
        exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
        sub: 'user-123'
      };
      
      const mockToken = `header.${btoa(JSON.stringify(tokenPayload))}.signature`;
      localStorageMock.getItem.mockReturnValue(mockToken);

      const result = await AuthService.checkAndRefreshToken();

      expect(result).toBe(false);
      expect(mockedAxios.post).not.toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should handle malformed tokens gracefully', () => {
      localStorageMock.getItem.mockReturnValue('malformed.token');

      expect(() => AuthService.isTokenExpired()).not.toThrow();
    });

    it('should handle network timeouts', async () => {
      const timeoutError = new Error('timeout of 5000ms exceeded');
      timeoutError.name = 'TimeoutError';
      
      mockedAxios.post.mockRejectedValue(timeoutError);

      await expect(AuthService.login('testuser', 'password123')).rejects.toThrow('timeout of 5000ms exceeded');
    });

    it('should retry failed requests once', async () => {
      mockedAxios.post
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce({
          data: {
            access_token: 'retry-token',
            user: { id: 'user-123', username: 'testuser' }
          }
        });

      const result = await AuthService.login('testuser', 'password123');

      expect(mockedAxios.post).toHaveBeenCalledTimes(2);
      expect(result.access_token).toBe('retry-token');
    });
  });
});