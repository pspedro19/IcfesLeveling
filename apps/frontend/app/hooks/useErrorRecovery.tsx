/**
 * React Hook for Error Recovery
 * Provides easy integration with the error recovery service for React components
 */

import { useCallback, useEffect, useState } from 'react';
import { errorRecoveryService, ErrorDetails, ErrorType } from '../services/errorRecovery.service';

interface UseErrorRecoveryReturn {
  // State
  hasError: boolean;
  currentError: ErrorDetails | null;
  isRecovering: boolean;
  systemStatus: {
    isOnline: boolean;
    hasErrors: boolean;
    activeErrors: number;
  };
  
  // Actions
  handleError: (error: any, context?: Record<string, any>) => Promise<boolean>;
  clearError: () => void;
  retry: () => Promise<void>;
  
  // Utilities
  showUserFriendlyMessage: (message: string, type?: 'error' | 'warning' | 'info') => void;
}

export const useErrorRecovery = (
  component?: string,
  fallbackData?: any
): UseErrorRecoveryReturn => {
  const [hasError, setHasError] = useState(false);
  const [currentError, setCurrentError] = useState<ErrorDetails | null>(null);
  const [isRecovering, setIsRecovering] = useState(false);
  const [systemStatus, setSystemStatus] = useState(() => 
    errorRecoveryService.getSystemStatus()
  );

  // Update system status periodically
  useEffect(() => {
    const updateStatus = () => {
      setSystemStatus(errorRecoveryService.getSystemStatus());
    };

    const interval = setInterval(updateStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Listen for error events
  useEffect(() => {
    const handleErrorEvent = (error: ErrorDetails) => {
      setCurrentError(error);
      setHasError(true);
    };

    errorRecoveryService.addErrorListener(handleErrorEvent);

    return () => {
      errorRecoveryService.removeErrorListener(handleErrorEvent);
    };
  }, []);

  // Listen for network events
  useEffect(() => {
    const handleNetworkRecovered = () => {
      setHasError(false);
      setCurrentError(null);
      setIsRecovering(false);
    };

    const handleNetworkFailed = () => {
      setHasError(true);
      setCurrentError({
        id: 'network_offline',
        type: ErrorType.NETWORK_ERROR,
        message: 'Network connection lost',
        timestamp: new Date(),
        userMessage: 'Sin conexión a internet. Usando modo offline.',
        canRetry: true
      });
    };

    window.addEventListener('network-recovered', handleNetworkRecovered);
    window.addEventListener('network-failed', handleNetworkFailed);

    return () => {
      window.removeEventListener('network-recovered', handleNetworkRecovered);
      window.removeEventListener('network-failed', handleNetworkFailed);
    };
  }, []);

  const handleError = useCallback(async (
    error: any,
    context?: Record<string, any>
  ): Promise<boolean> => {
    setIsRecovering(true);
    
    try {
      const errorDetails: ErrorDetails = {
        id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: classifyError(error),
        message: error.message || 'Unknown error occurred',
        timestamp: new Date(),
        context: {
          ...context,
          component,
          url: window.location.href,
          userAgent: navigator.userAgent
        }
      };

      const recovered = await errorRecoveryService.handleError(errorDetails);
      
      if (!recovered) {
        setCurrentError(errorDetails);
        setHasError(true);
      }

      return recovered;
    } finally {
      setIsRecovering(false);
    }
  }, [component]);

  const clearError = useCallback(() => {
    setHasError(false);
    setCurrentError(null);
  }, []);

  const retry = useCallback(async () => {
    if (!currentError) return;
    
    setIsRecovering(true);
    
    try {
      const recovered = await errorRecoveryService.handleError(currentError);
      
      if (recovered) {
        clearError();
      }
    } finally {
      setIsRecovering(false);
    }
  }, [currentError, clearError]);

  const showUserFriendlyMessage = useCallback((
    message: string,
    type: 'error' | 'warning' | 'info' = 'error'
  ) => {
    // Dispatch custom event for toast notifications or other UI components
    const event = new CustomEvent('show-user-message', {
      detail: { message, type, timestamp: new Date().toISOString() }
    });
    window.dispatchEvent(event);
  }, []);

  return {
    hasError,
    currentError,
    isRecovering,
    systemStatus,
    handleError,
    clearError,
    retry,
    showUserFriendlyMessage
  };
};

/**
 * Classify errors for appropriate handling
 */
function classifyError(error: any): ErrorType {
  if (error?.response?.status) {
    const status = error.response.status;
    if (status === 401) return ErrorType.AUTHENTICATION_ERROR;
    if (status === 403) return ErrorType.PERMISSION_ERROR;
    if (status === 404) return ErrorType.NOT_FOUND_ERROR;
    if (status === 422) return ErrorType.VALIDATION_ERROR;
    if (status === 429) return ErrorType.RATE_LIMIT_ERROR;
    if (status >= 500) return ErrorType.SERVER_ERROR;
  }

  if (error?.code === 'NETWORK_ERROR' || !navigator.onLine) {
    return ErrorType.NETWORK_ERROR;
  }

  if (error?.name === 'ValidationError') {
    return ErrorType.VALIDATION_ERROR;
  }

  if (error?.name === 'TimeoutError') {
    return ErrorType.TIMEOUT_ERROR;
  }

  return ErrorType.UNKNOWN_ERROR;
}

/**
 * Higher-order component for automatic error boundary with recovery
 */
export function withErrorRecovery<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: {
    fallbackComponent?: React.ComponentType<{ error: ErrorDetails; retry: () => void }>;
    componentName?: string;
  } = {}
) {
  const ErrorRecoveryWrapper = (props: P) => {
    const { hasError, currentError, retry } = useErrorRecovery(
      options.componentName || WrappedComponent.name
    );

    if (hasError && currentError) {
      if (options.fallbackComponent) {
        const FallbackComponent = options.fallbackComponent;
        return <FallbackComponent error={currentError} retry={retry} />;
      }

      return (
        <div className="error-boundary p-6 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">
                Algo salió mal
              </h3>
              <p className="mt-1 text-sm text-red-700">
                {currentError.userMessage || currentError.message}
              </p>
              {currentError.canRetry && (
                <div className="mt-3">
                  <button
                    onClick={retry}
                    className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm font-medium transition-colors"
                  >
                    Reintentar
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      );
    }

    return <WrappedComponent {...props} />;
  };

  ErrorRecoveryWrapper.displayName = `withErrorRecovery(${WrappedComponent.displayName || WrappedComponent.name})`;

  return ErrorRecoveryWrapper;
}

/**
 * Hook for handling async operations with automatic error recovery
 */
export const useAsyncWithRecovery = <T,>(
  asyncFn: () => Promise<T>,
  dependencies: React.DependencyList = []
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const { handleError, isRecovering } = useErrorRecovery();

  const execute = useCallback(async () => {
    setLoading(true);
    try {
      const result = await asyncFn();
      setData(result);
      return result;
    } catch (error) {
      const recovered = await handleError(error, {
        operation: 'async_operation',
        function: asyncFn.name
      });
      
      if (!recovered) {
        throw error;
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [asyncFn, handleError]);

  useEffect(() => {
    execute();
  }, dependencies);

  return {
    data,
    loading: loading || isRecovering,
    error: null, // Errors are handled by the error recovery service
    retry: execute
  };
};

/**
 * Hook for form error handling with validation recovery
 */
export const useFormErrorRecovery = (formName: string) => {
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const { handleError, showUserFriendlyMessage } = useErrorRecovery(formName);

  const handleFormError = useCallback(async (error: any) => {
    if (error.response?.data?.errors) {
      // Handle validation errors
      setFieldErrors(error.response.data.errors);
      showUserFriendlyMessage(
        'Por favor corrige los errores en el formulario',
        'warning'
      );
      return true;
    }

    // Handle other types of errors
    return await handleError(error, {
      form: formName,
      fields: Object.keys(fieldErrors)
    });
  }, [handleError, showUserFriendlyMessage, formName, fieldErrors]);

  const clearFieldError = useCallback((fieldName: string) => {
    setFieldErrors(prev => {
      const { [fieldName]: removed, ...rest } = prev;
      return rest;
    });
  }, []);

  const clearAllErrors = useCallback(() => {
    setFieldErrors({});
  }, []);

  return {
    fieldErrors,
    handleFormError,
    clearFieldError,
    clearAllErrors,
    hasErrors: Object.keys(fieldErrors).length > 0
  };
};