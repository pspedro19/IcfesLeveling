/**
 * Professional UX Error Handling System
 * Handles all errors gracefully with user-friendly messages
 */

import { toast } from 'sonner';
import * as Sentry from '@sentry/nextjs';

export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  NOT_FOUND = 'NOT_FOUND',
  SERVER = 'SERVER',
  RATE_LIMIT = 'RATE_LIMIT',
  MAINTENANCE = 'MAINTENANCE',
  UNKNOWN = 'UNKNOWN'
}

export interface ErrorDetails {
  type: ErrorType;
  message: string;
  code?: string;
  statusCode?: number;
  timestamp: Date;
  requestId?: string;
  metadata?: Record<string, any>;
}

export class AppError extends Error {
  public readonly type: ErrorType;
  public readonly code?: string;
  public readonly statusCode?: number;
  public readonly timestamp: Date;
  public readonly requestId?: string;
  public readonly metadata?: Record<string, any>;

  constructor(details: Partial<ErrorDetails>) {
    super(details.message || 'Ha ocurrido un error');
    this.type = details.type || ErrorType.UNKNOWN;
    this.code = details.code;
    this.statusCode = details.statusCode;
    this.timestamp = details.timestamp || new Date();
    this.requestId = details.requestId;
    this.metadata = details.metadata;
    
    // Preserve stack trace
    Error.captureStackTrace(this, this.constructor);
  }
}

// User-friendly error messages in Spanish
const ERROR_MESSAGES: Record<ErrorType, string> = {
  [ErrorType.NETWORK]: 'Error de conexión. Por favor verifica tu internet y vuelve a intentar.',
  [ErrorType.VALIDATION]: 'Los datos ingresados no son válidos. Por favor revisa y corrige.',
  [ErrorType.AUTHENTICATION]: 'Debes iniciar sesión para continuar.',
  [ErrorType.AUTHORIZATION]: 'No tienes permisos para realizar esta acción.',
  [ErrorType.NOT_FOUND]: 'El recurso solicitado no fue encontrado.',
  [ErrorType.SERVER]: 'Error en el servidor. Nuestro equipo ha sido notificado.',
  [ErrorType.RATE_LIMIT]: 'Has realizado demasiadas solicitudes. Por favor espera un momento.',
  [ErrorType.MAINTENANCE]: 'Sistema en mantenimiento. Volveremos pronto.',
  [ErrorType.UNKNOWN]: 'Ha ocurrido un error inesperado. Por favor intenta nuevamente.'
};

// Recovery suggestions for each error type
const RECOVERY_SUGGESTIONS: Record<ErrorType, string[]> = {
  [ErrorType.NETWORK]: [
    'Verifica tu conexión a internet',
    'Intenta recargar la página',
    'Desactiva temporalmente extensiones del navegador'
  ],
  [ErrorType.VALIDATION]: [
    'Revisa que todos los campos estén completos',
    'Verifica el formato de los datos ingresados',
    'Asegúrate de cumplir con los requisitos mínimos'
  ],
  [ErrorType.AUTHENTICATION]: [
    'Inicia sesión con tu cuenta',
    'Si olvidaste tu contraseña, usa "Recuperar contraseña"',
    'Verifica que tu sesión no haya expirado'
  ],
  [ErrorType.AUTHORIZATION]: [
    'Contacta al administrador si crees que es un error',
    'Verifica que estés usando la cuenta correcta',
    'Revisa tus permisos de usuario'
  ],
  [ErrorType.NOT_FOUND]: [
    'Verifica que la URL sea correcta',
    'El contenido pudo haber sido movido o eliminado',
    'Intenta buscar desde el inicio'
  ],
  [ErrorType.SERVER]: [
    'Espera unos minutos e intenta nuevamente',
    'Si el problema persiste, contacta soporte',
    'Guarda tu trabajo y recarga la página'
  ],
  [ErrorType.RATE_LIMIT]: [
    'Espera 60 segundos antes de intentar nuevamente',
    'Reduce la frecuencia de tus solicitudes',
    'Si necesitas más capacidad, contacta soporte'
  ],
  [ErrorType.MAINTENANCE]: [
    'El sistema volverá pronto',
    'Sigue nuestras redes para actualizaciones',
    'Guarda tu trabajo para cuando regresemos'
  ],
  [ErrorType.UNKNOWN]: [
    'Recarga la página',
    'Limpia el caché del navegador',
    'Si persiste, contacta soporte técnico'
  ]
};

export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorQueue: ErrorDetails[] = [];
  private maxQueueSize = 50;
  private isOnline = true;

  private constructor() {
    this.setupEventListeners();
    this.setupInterceptors();
  }

  public static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  private setupEventListeners() {
    if (typeof window === 'undefined') return;

    // Global error handler
    window.addEventListener('error', (event) => {
      this.handleError(new AppError({
        type: ErrorType.UNKNOWN,
        message: event.message,
        metadata: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        }
      }));
    });

    // Promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError(new AppError({
        type: ErrorType.UNKNOWN,
        message: event.reason?.message || 'Promise rechazada',
        metadata: { reason: event.reason }
      }));
    });

    // Network status
    window.addEventListener('online', () => {
      this.isOnline = true;
      toast.success('Conexión restaurada');
      this.processQueuedErrors();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      toast.error('Sin conexión a internet');
    });
  }

  private setupInterceptors() {
    if (typeof window === 'undefined') return;

    // Fetch interceptor
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        
        if (!response.ok) {
          const errorType = this.getErrorTypeFromStatus(response.status);
          const errorData = await this.tryParseErrorResponse(response);
          
          throw new AppError({
            type: errorType,
            message: errorData.message || ERROR_MESSAGES[errorType],
            statusCode: response.status,
            requestId: response.headers.get('x-request-id') || undefined,
            metadata: errorData
          });
        }
        
        return response;
      } catch (error) {
        if (error instanceof AppError) {
          throw error;
        }
        
        throw new AppError({
          type: ErrorType.NETWORK,
          message: ERROR_MESSAGES[ErrorType.NETWORK],
          metadata: { originalError: error }
        });
      }
    };
  }

  private getErrorTypeFromStatus(status: number): ErrorType {
    if (status === 401) return ErrorType.AUTHENTICATION;
    if (status === 403) return ErrorType.AUTHORIZATION;
    if (status === 404) return ErrorType.NOT_FOUND;
    if (status === 422) return ErrorType.VALIDATION;
    if (status === 429) return ErrorType.RATE_LIMIT;
    if (status === 503) return ErrorType.MAINTENANCE;
    if (status >= 500) return ErrorType.SERVER;
    if (status >= 400) return ErrorType.VALIDATION;
    return ErrorType.UNKNOWN;
  }

  private async tryParseErrorResponse(response: Response): Promise<any> {
    try {
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return await response.json();
      }
      return { message: await response.text() };
    } catch {
      return { message: 'Error al procesar la respuesta' };
    }
  }

  public handleError(error: Error | AppError, options?: {
    silent?: boolean;
    showToast?: boolean;
    showRecovery?: boolean;
  }): void {
    const appError = error instanceof AppError ? error : new AppError({
      type: ErrorType.UNKNOWN,
      message: error.message,
      metadata: { originalError: error }
    });

    const { silent = false, showToast = true, showRecovery = true } = options || {};

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('[ErrorHandler]', appError);
    }

    // Send to Sentry in production
    if (process.env.NODE_ENV === 'production') {
      Sentry.captureException(appError, {
        tags: {
          errorType: appError.type,
          errorCode: appError.code
        },
        extra: appError.metadata
      });
    }

    // Queue error if offline
    if (!this.isOnline) {
      this.queueError(appError);
    }

    // Show user notification
    if (!silent && showToast) {
      this.showErrorNotification(appError, showRecovery);
    }
  }

  private showErrorNotification(error: AppError, showRecovery: boolean) {
    const message = ERROR_MESSAGES[error.type] || error.message;
    const suggestions = showRecovery ? RECOVERY_SUGGESTIONS[error.type] : [];

    toast.error(message, {
      description: suggestions.length > 0 ? 
        `Sugerencias: ${suggestions[0]}` : undefined,
      duration: 5000,
      action: error.type === ErrorType.AUTHENTICATION ? {
        label: 'Iniciar sesión',
        onClick: () => window.location.href = '/login'
      } : undefined
    });
  }

  private queueError(error: ErrorDetails) {
    this.errorQueue.push(error);
    if (this.errorQueue.length > this.maxQueueSize) {
      this.errorQueue.shift();
    }
  }

  private async processQueuedErrors() {
    if (this.errorQueue.length === 0) return;

    const errors = [...this.errorQueue];
    this.errorQueue = [];

    for (const error of errors) {
      try {
        await this.sendErrorToServer(error);
      } catch {
        // Re-queue if still failing
        this.errorQueue.push(error);
      }
    }
  }

  private async sendErrorToServer(error: ErrorDetails) {
    try {
      await fetch('/api/v1/errors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(error)
      });
    } catch {
      // Silently fail
    }
  }

  public clearErrors() {
    this.errorQueue = [];
  }

  public getErrorHistory(): ErrorDetails[] {
    return [...this.errorQueue];
  }
}

// Export singleton instance
export const errorHandler = ErrorHandler.getInstance();

// React Error Boundary Component
import React, { Component, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
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
    errorHandler.handleError(error, { showToast: true });
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-lg">
            <div className="text-center">
              <div className="text-6xl mb-4">⚠️</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Algo salió mal
              </h2>
              <p className="text-gray-600 mb-4">
                Ha ocurrido un error inesperado. Por favor recarga la página.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Recargar página
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Async error wrapper
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  options?: Parameters<typeof errorHandler.handleError>[1]
): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    errorHandler.handleError(error as Error, options);
    return null;
  }
}

// Hook for error handling
export function useErrorHandler() {
  const handleError = React.useCallback((error: Error | AppError, options?: Parameters<typeof errorHandler.handleError>[1]) => {
    errorHandler.handleError(error, options);
  }, []);

  return { handleError };
}