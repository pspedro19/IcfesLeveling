import * as Sentry from '@sentry/nextjs';

export interface AppError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

class ErrorHandler {
  private static instance: ErrorHandler;
  
  private constructor() {
    this.setupGlobalHandlers();
  }
  
  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }
  
  private setupGlobalHandlers() {
    // Handle unhandled promise rejections
    if (typeof window !== 'undefined') {
      window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        this.handleError(event.reason);
        event.preventDefault();
      });
      
      // Handle global errors
      window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        this.handleError(event.error);
        event.preventDefault();
      });
    }
  }
  
  handleError(error: any) {
    const appError = this.parseError(error);
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error Handler:', appError);
    }
    
    // Show user notification based on error type
    this.showErrorNotification(appError);
    
    // Send to error tracking service (e.g., Sentry) in production
    if (process.env.NODE_ENV === 'production') {
      Sentry.captureException(error, {
        tags: {
          code: appError.code,
          status: appError.status?.toString(),
        },
        extra: {
          details: appError.details,
        },
        level: this.getSeverityLevel(appError),
      });
    }
  }
  
  private parseError(error: any): AppError {
    // Axios error
    if (error.response) {
      return {
        message: error.response.data?.detail || error.response.data?.message || 'Error del servidor',
        code: error.response.data?.code,
        status: error.response.status,
        details: error.response.data,
      };
    }
    
    // Network error
    if (error.request && !error.response) {
      return {
        message: 'Error de conexión. Verifica tu internet.',
        code: 'NETWORK_ERROR',
      };
    }
    
    // Standard Error object
    if (error instanceof Error) {
      return {
        message: error.message,
        code: error.name,
      };
    }
    
    // Unknown error
    return {
      message: typeof error === 'string' ? error : 'Ha ocurrido un error inesperado',
      code: 'UNKNOWN_ERROR',
    };
  }
  
  private showErrorNotification(error: AppError) {
    // Note: This method should be called from a React component context
    // For now, we'll just log the error. In a real app, you'd use a global notification system
    console.error('Error notification:', {
      type: error.status === 403 ? 'warning' : 'error',
      title: this.getErrorTitle(error),
      message: error.message,
      iconName: error.code === 'NETWORK_ERROR' ? 'WifiOff' : error.status === 403 ? 'ShieldAlert' : 'AlertCircle'
    });
  }
  
  private getErrorTitle(error: AppError): string {
    switch (error.status) {
      case 401:
        return 'Sesión Expirada';
      case 403:
        return 'Acceso Denegado';
      case 404:
        return 'No Encontrado';
      case 500:
      case 502:
      case 503:
        return 'Error del Servidor';
      default:
        return error.code === 'NETWORK_ERROR' ? 'Sin Conexión' : 'Error';
    }
  }
  
  private getErrorActions(error: AppError): any[] {
    const actions = [];
    
    if (error.status === 401) {
      actions.push({
        label: 'Iniciar Sesión',
        onClick: () => {
          window.location.href = '/';
        },
      });
    }
    
    if (error.code === 'NETWORK_ERROR') {
      actions.push({
        label: 'Reintentar',
        onClick: () => {
          window.location.reload();
        },
      });
    }
    
    return actions;
  }
  
  private getSeverityLevel(error: AppError): Sentry.SeverityLevel {
    if (error.status && error.status >= 500) {
      return 'error';
    }
    if (error.status === 401 || error.status === 403) {
      return 'warning';
    }
    if (error.code === 'NETWORK_ERROR') {
      return 'info';
    }
    return 'error';
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();

// React Error Boundary Component
import React, { Component, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    errorHandler.handleError(error);
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 flex items-center justify-center p-8">
          <div className="bg-black/50 backdrop-blur-md rounded-lg p-8 max-w-md text-center">
            <h1 className="text-3xl font-bold text-white mb-4">¡Oops! Portal Inestable</h1>
            <p className="text-purple-300 mb-6">
              El Sistema ha detectado una anomalía. Por favor, recarga la página.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              Recargar Portal
            </button>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}