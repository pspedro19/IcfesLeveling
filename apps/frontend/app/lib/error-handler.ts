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
    this.initializeSentry();
  }
  
  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }
  
  private initializeSentry() {
    // Sentry initialization is handled in sentry config files
  }
  
  handleError(error: unknown, context?: string): AppError {
    const appError = this.normalizeError(error);
    
    // Log error
    console.error(`[${context || 'ErrorHandler'}]`, appError);
    
    // Send to Sentry
    try {
      Sentry.captureException(error, {
        tags: {
          context: context || 'unknown',
          errorCode: appError.code,
        },
        extra: {
          appError,
          originalError: error,
        },
      });
    } catch (sentryError) {
      console.error('Failed to send error to Sentry:', sentryError);
    }
    
    // Show user notification (in development, just log)
    this.showErrorNotification(appError);
    
    return appError;
  }
  
  private normalizeError(error: unknown): AppError {
    if (this.isAppError(error)) {
      return error;
    }
    
    if (error instanceof Error) {
      return {
        message: error.message,
        code: error.name || 'GENERIC_ERROR',
        details: {
          stack: error.stack,
          name: error.name,
        },
      };
    }
    
    if (typeof error === 'object' && error !== null) {
      const err = error as any;
      
      // Handle fetch/axios errors
      if (err.response) {
        return {
          message: err.response.data?.message || err.message || 'Error de red',
          code: 'API_ERROR',
          status: err.response.status,
          details: err.response.data,
        };
      }
      
      // Handle network errors
      if (err.code === 'NETWORK_ERROR' || !navigator.onLine) {
        return {
          message: 'Sin conexión a internet. Verifica tu conexión.',
          code: 'NETWORK_ERROR',
          status: 0,
        };
      }
    }
    
    return {
      message: typeof error === 'string' ? error : 'Ha ocurrido un error inesperado',
      code: 'UNKNOWN_ERROR',
    };
  }
  
  private isAppError(error: unknown): error is AppError {
    return (
      typeof error === 'object' &&
      error !== null &&
      'message' in error &&
      typeof (error as any).message === 'string'
    );
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
        return 'Recurso No Encontrado';
      case 500:
        return 'Error del Servidor';
      default:
        return error.code === 'NETWORK_ERROR' ? 'Sin Conexión' : 'Error del Sistema';
    }
  }
  
  private getErrorActions(error: AppError): Array<{ label: string; action: () => void }> {
    const actions: Array<{ label: string; action: () => void }> = [];
    
    if (error.code === 'NETWORK_ERROR') {
      actions.push({
        label: 'Reintentar',
        action: () => window.location.reload(),
      });
    }
    
    if (error.status === 401) {
      actions.push({
        label: 'Iniciar Sesión',
        action: () => {
          // Navigate to login
          window.location.href = '/auth/login';
        },
      });
    }
    
    return actions;
  }
  
  // Utility methods for common error scenarios
  handleApiError(response: Response, data?: any): AppError {
    const error: AppError = {
      message: data?.message || `Error ${response.status}: ${response.statusText}`,
      code: 'API_ERROR',
      status: response.status,
      details: data,
    };
    
    return this.handleError(error, 'API');
  }
  
  handleNetworkError(): AppError {
    const error: AppError = {
      message: 'Sin conexión a internet. Verifica tu conexión.',
      code: 'NETWORK_ERROR',
      status: 0,
    };
    
    return this.handleError(error, 'Network');
  }
  
  handleValidationError(fields: Record<string, string>): AppError {
    const error: AppError = {
      message: 'Error de validación en el formulario',
      code: 'VALIDATION_ERROR',
      details: fields,
    };
    
    return this.handleError(error, 'Validation');
  }
}

// Create and export singleton instance
export const errorHandler = ErrorHandler.getInstance();

// Export default error handler function
export default function handleError(error: unknown, context?: string): AppError {
  return errorHandler.handleError(error, context);
}