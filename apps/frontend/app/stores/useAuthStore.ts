import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { devtools } from 'zustand/middleware';
import { User, HeroClass } from '@/types/auth';
import { authService } from '@/services/auth.service';

interface AuthState {
  // State
  user: User | null;
  heroClass: HeroClass | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (username: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  setHeroClass: (heroClass: HeroClass) => void;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        user: null,
        heroClass: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        
        // Login action
        login: async (username: string, password: string) => {
          set({ isLoading: true, error: null });
          
          try {
            const response = await authService.login({ username, password });
            
            set({
              user: response.user,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            
            // Track event
            if (typeof window !== 'undefined') {
              const eventData = {
                timestamp: new Date().toISOString(),
                action: 'login_success',
                data: { userId: response.user.id },
              };
              console.log('🎯 User Action Tracked:', eventData);
            }
          } catch (error: any) {
            const errorMessage = error.response?.data?.detail || 'Error al iniciar sesión';
            set({
              isAuthenticated: false,
              isLoading: false,
              error: errorMessage,
            });
            throw error;
          }
        },
        
        // Register action
        register: async (data: any) => {
          set({ isLoading: true, error: null });
          
          try {
            const user = await authService.register(data);
            
            set({
              user,
              isAuthenticated: false, // User needs to login after registration
              isLoading: false,
              error: null,
            });
          } catch (error: any) {
            const errorMessage = error.response?.data?.detail || 'Error al registrar usuario';
            set({
              isLoading: false,
              error: errorMessage,
            });
            throw error;
          }
        },
        
        // Logout action
        logout: () => {
          authService.logout();
          set({
            user: null,
            heroClass: null,
            isAuthenticated: false,
            error: null,
          });
        },
        
        // Set user
        setUser: (user: User) => {
          set({ user, isAuthenticated: true });
        },
        
        // Set hero class
        setHeroClass: (heroClass: HeroClass) => {
          set({ heroClass });
        },
        
        // Check authentication status
        checkAuth: async () => {
          if (!authService.isAuthenticated()) {
            set({ isAuthenticated: false, user: null });
            return;
          }
          
          set({ isLoading: true });
          
          try {
            const user = await authService.getCurrentUser();
            set({
              user,
              isAuthenticated: true,
              isLoading: false,
            });
          } catch (error) {
            set({
              isAuthenticated: false,
              user: null,
              isLoading: false,
            });
          }
        },
        
        // Clear error
        clearError: () => {
          set({ error: null });
        },
      }),
      {
        name: 'auth-storage',
        storage: createJSONStorage(() => localStorage),
        partialize: (state) => ({
          user: state.user,
          heroClass: state.heroClass,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    {
      name: 'auth-store',
    }
  )
);