/**
 * Frontend Error Recovery Service
 * Provides comprehensive error handling, user-friendly messages, and automatic recovery for the frontend
 */

interface ErrorDetails {
  id: string;
  type: ErrorType;
  message: string;
  timestamp: Date;
  context?: Record<string, any>;
  recoveryAction?: string;
  userMessage?: string;
  canRetry?: boolean;
}

enum ErrorType {
  NETWORK_ERROR = 'network_error',
  AUTHENTICATION_ERROR = 'authentication_error', 
  VALIDATION_ERROR = 'validation_error',
  SERVER_ERROR = 'server_error',
  TIMEOUT_ERROR = 'timeout_error',
  PERMISSION_ERROR = 'permission_error',
  NOT_FOUND_ERROR = 'not_found_error',
  RATE_LIMIT_ERROR = 'rate_limit_error',
  UNKNOWN_ERROR = 'unknown_error'
}

interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffFactor: number;
}

interface FallbackData {
  questions: Question[];
  userProgress: UserProgress;
  leaderboard: LeaderboardEntry[];
  studyPlans: StudyPlan[];
}

class ErrorRecoveryService {
  private errorQueue: ErrorDetails[] = [];
  private retryCounters: Map<string, number> = new Map();
  private circuitBreakers: Map<string, CircuitBreakerState> = new Map();
  private fallbackData: Partial<FallbackData> = {};
  private recoveryListeners: Set<(error: ErrorDetails) => void> = new Set();
  
  private readonly defaultRetryConfig: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    backoffFactor: 2
  };

  constructor() {
    this.initializeFallbackData();
    this.setupGlobalErrorHandlers();
  }

  /**
   * Initialize fallback data for offline scenarios
   */
  private initializeFallbackData(): void {
    this.fallbackData = {
      questions: [
        {
          id: 'fallback-math-1',
          subject: 'Matemáticas',
          topic: 'Aritmética básica',
          questionText: '¿Cuál es el resultado de 25 + 17?',
          options: ['40', '41', '42', '43'],
          correctAnswer: 'C',
          explanation: 'La suma de 25 + 17 = 42',
          difficulty: 'easy',
          isFallback: true
        },
        {
          id: 'fallback-spanish-1',
          subject: 'Lenguaje',
          topic: 'Comprensión lectora',
          questionText: 'En la oración "María estudia matemáticas", ¿cuál es el verbo?',
          options: ['María', 'estudia', 'matemáticas', 'la'],
          correctAnswer: 'B',
          explanation: 'El verbo es la palabra que indica la acción: "estudia"',
          difficulty: 'easy',
          isFallback: true
        }
      ],
      userProgress: {
        level: 1,
        xp: 100,
        streakDays: 1,
        completedQuestions: 0,
        accuracy: 0,
        subjectsProgress: {},
        isFallback: true
      },
      leaderboard: [
        { rank: 1, username: 'Estudiante Ejemplo', score: 1000, level: 10 }
      ],
      studyPlans: [
        {
          id: 'fallback-plan-1',
          name: 'Plan de Estudio Básico',
          description: 'Plan básico mientras se restaura la conectividad',
          dailySessions: 2,
          sessionDuration: 25,
          subjects: ['Matemáticas', 'Lenguaje'],
          isFallback: true
        }
      ]
    };
  }

  /**
   * Setup global error handlers for unhandled errors
   */
  private setupGlobalErrorHandlers(): void {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      const error = this.createErrorDetails(
        ErrorType.UNKNOWN_ERROR,
        event.reason?.message || 'Unhandled promise rejection',
        { 
          stack: event.reason?.stack,
          type: 'unhandledrejection'
        }
      );
      this.handleError(error);
    });

    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      const error = this.createErrorDetails(
        ErrorType.UNKNOWN_ERROR,
        event.message || 'JavaScript error',
        {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          stack: event.error?.stack,
          type: 'javascript_error'
        }
      );
      this.handleError(error);
    });

    // Handle network status changes
    window.addEventListener('online', () => {
      this.handleNetworkRecovery();
    });

    window.addEventListener('offline', () => {
      this.handleNetworkFailure();
    });
  }

  /**
   * Create standardized error details
   */
  private createErrorDetails(
    type: ErrorType,
    message: string,
    context?: Record<string, any>
  ): ErrorDetails {
    const id = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      id,
      type,
      message,
      timestamp: new Date(),
      context,
      ...this.getErrorTypeConfig(type)
    };
  }

  /**
   * Get configuration for different error types
   */
  private getErrorTypeConfig(type: ErrorType): Partial<ErrorDetails> {
    const configs: Record<ErrorType, Partial<ErrorDetails>> = {
      [ErrorType.NETWORK_ERROR]: {
        userMessage: 'Problema de conexión. Verificando conectividad...',
        recoveryAction: 'retry_with_backoff',
        canRetry: true
      },
      [ErrorType.AUTHENTICATION_ERROR]: {
        userMessage: 'Tu sesión ha expirado. Por favor inicia sesión nuevamente.',
        recoveryAction: 'redirect_to_login',
        canRetry: false
      },
      [ErrorType.VALIDATION_ERROR]: {
        userMessage: 'Por favor verifica que toda la información esté completa y correcta.',
        recoveryAction: 'show_validation_errors',
        canRetry: true
      },
      [ErrorType.SERVER_ERROR]: {
        userMessage: 'Error temporal del servidor. Reintentando automáticamente...',
        recoveryAction: 'retry_with_fallback',
        canRetry: true
      },
      [ErrorType.TIMEOUT_ERROR]: {
        userMessage: 'La solicitud está tomando más tiempo del esperado. Reintentando...',
        recoveryAction: 'retry_with_longer_timeout',
        canRetry: true
      },
      [ErrorType.PERMISSION_ERROR]: {
        userMessage: 'No tienes permisos para realizar esta acción.',
        recoveryAction: 'show_permission_error',
        canRetry: false
      },
      [ErrorType.NOT_FOUND_ERROR]: {
        userMessage: 'El recurso solicitado no se encontró.',
        recoveryAction: 'redirect_to_home',
        canRetry: false
      },
      [ErrorType.RATE_LIMIT_ERROR]: {
        userMessage: 'Has realizado demasiadas solicitudes. Por favor espera un momento.',
        recoveryAction: 'wait_and_retry',
        canRetry: true
      },
      [ErrorType.UNKNOWN_ERROR]: {
        userMessage: 'Ha ocurrido un error inesperado. Nuestro equipo ha sido notificado.',
        recoveryAction: 'log_and_fallback',
        canRetry: true
      }
    };

    return configs[type] || configs[ErrorType.UNKNOWN_ERROR];
  }

  /**
   * Main error handling function
   */
  public async handleError(error: ErrorDetails): Promise<boolean> {
    try {
      // Log error for monitoring
      this.logError(error);

      // Add to error queue
      this.errorQueue.push(error);

      // Notify listeners
      this.notifyErrorListeners(error);

      // Execute recovery action
      const recovered = await this.executeRecoveryAction(error);

      return recovered;
    } catch (recoveryError) {
      console.error('Error in error recovery:', recoveryError);
      return false;
    }
  }

  /**
   * Handle API errors with automatic classification and recovery
   */
  public async handleApiError(
    error: any,
    endpoint: string,
    context?: Record<string, any>
  ): Promise<any> {
    const errorType = this.classifyApiError(error);
    const errorDetails = this.createErrorDetails(
      errorType,
      error.message || 'API Error',
      {
        ...context,
        endpoint,
        status: error.status,
        response: error.response?.data
      }
    );

    const recovered = await this.handleError(errorDetails);

    if (recovered) {
      // Return fallback data or retry result
      return this.getFallbackDataForEndpoint(endpoint);
    }

    throw error;
  }

  /**
   * Classify API errors based on status codes and error details
   */
  private classifyApiError(error: any): ErrorType {
    if (!error.status) {
      return ErrorType.NETWORK_ERROR;
    }

    const status = error.status;

    if (status === 401) return ErrorType.AUTHENTICATION_ERROR;
    if (status === 403) return ErrorType.PERMISSION_ERROR;
    if (status === 404) return ErrorType.NOT_FOUND_ERROR;
    if (status === 422) return ErrorType.VALIDATION_ERROR;
    if (status === 429) return ErrorType.RATE_LIMIT_ERROR;
    if (status === 408 || status === 504) return ErrorType.TIMEOUT_ERROR;
    if (status >= 500) return ErrorType.SERVER_ERROR;

    return ErrorType.UNKNOWN_ERROR;
  }

  /**
   * Execute recovery actions based on error type
   */
  private async executeRecoveryAction(error: ErrorDetails): Promise<boolean> {
    const action = error.recoveryAction;

    try {
      switch (action) {
        case 'retry_with_backoff':
          return await this.retryWithBackoff(error);
        
        case 'retry_with_fallback':
          return await this.retryWithFallback(error);
        
        case 'redirect_to_login':
          this.redirectToLogin();
          return true;
        
        case 'show_validation_errors':
          this.showValidationErrors(error);
          return true;
        
        case 'show_permission_error':
          this.showPermissionError(error);
          return true;
        
        case 'redirect_to_home':
          this.redirectToHome();
          return true;
        
        case 'wait_and_retry':
          return await this.waitAndRetry(error);
        
        case 'log_and_fallback':
          return this.logAndUseFallback(error);
        
        default:
          return this.logAndUseFallback(error);
      }
    } catch (actionError) {
      console.error('Recovery action failed:', actionError);
      return false;
    }
  }

  /**
   * Retry with exponential backoff
   */
  private async retryWithBackoff(
    error: ErrorDetails,
    config: RetryConfig = this.defaultRetryConfig
  ): Promise<boolean> {
    const retryKey = `${error.context?.endpoint || 'unknown'}_${error.type}`;
    const currentRetries = this.retryCounters.get(retryKey) || 0;

    if (currentRetries >= config.maxRetries) {
      this.retryCounters.delete(retryKey);
      return false;
    }

    const delay = Math.min(
      config.baseDelay * Math.pow(config.backoffFactor, currentRetries),
      config.maxDelay
    );

    await this.sleep(delay);

    this.retryCounters.set(retryKey, currentRetries + 1);

    try {
      // Attempt to retry the original request
      const success = await this.retryOriginalRequest(error);
      if (success) {
        this.retryCounters.delete(retryKey);
        return true;
      }
      return await this.retryWithBackoff(error, config);
    } catch (retryError) {
      return await this.retryWithBackoff(error, config);
    }
  }

  /**
   * Retry with fallback data
   */
  private async retryWithFallback(error: ErrorDetails): Promise<boolean> {
    try {
      // First attempt to retry
      const retrySuccess = await this.retryOriginalRequest(error);
      if (retrySuccess) {
        return true;
      }

      // Use fallback data
      return this.useFallbackData(error);
    } catch {
      return this.useFallbackData(error);
    }
  }

  /**
   * Use fallback data for the error context
   */
  private useFallbackData(error: ErrorDetails): boolean {
    const endpoint = error.context?.endpoint;
    if (!endpoint) return false;

    const fallbackData = this.getFallbackDataForEndpoint(endpoint);
    if (fallbackData) {
      // Store fallback data in appropriate location (state management)
      this.storeFallbackData(endpoint, fallbackData);
      return true;
    }

    return false;
  }

  /**
   * Get appropriate fallback data for an endpoint
   */
  private getFallbackDataForEndpoint(endpoint: string): any {
    if (endpoint.includes('questions')) {
      return this.fallbackData.questions;
    }
    if (endpoint.includes('progress')) {
      return this.fallbackData.userProgress;
    }
    if (endpoint.includes('leaderboard')) {
      return this.fallbackData.leaderboard;
    }
    if (endpoint.includes('study-plan')) {
      return this.fallbackData.studyPlans;
    }
    return null;
  }

  /**
   * Store fallback data in the application state
   */
  private storeFallbackData(endpoint: string, data: any): void {
    // This would integrate with your state management solution
    // For example, Redux, Zustand, or React Context
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('fallback-data-available', {
        detail: { endpoint, data, timestamp: new Date().toISOString() }
      });
      window.dispatchEvent(event);
    }
  }

  /**
   * Attempt to retry the original request
   */
  private async retryOriginalRequest(error: ErrorDetails): Promise<boolean> {
    // This would depend on your HTTP client implementation
    // Return true if retry succeeds, false otherwise
    return false;
  }

  /**
   * Handle network recovery
   */
  private handleNetworkRecovery(): void {
    console.log('Network recovered, clearing circuit breakers');
    this.circuitBreakers.clear();
    this.retryCounters.clear();
    
    // Notify components that network is back
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('network-recovered');
      window.dispatchEvent(event);
    }
  }

  /**
   * Handle network failure
   */
  private handleNetworkFailure(): void {
    console.log('Network failed, activating offline mode');
    
    // Notify components to use offline mode
    if (typeof window !== 'undefined') {
      const event = new CustomEvent('network-failed');
      window.dispatchEvent(event);
    }
  }

  /**
   * Recovery action implementations
   */
  private redirectToLogin(): void {
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  private redirectToHome(): void {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  }

  private showValidationErrors(error: ErrorDetails): void {
    const event = new CustomEvent('show-validation-errors', {
      detail: { error, errors: error.context?.errors }
    });
    window.dispatchEvent(event);
  }

  private showPermissionError(error: ErrorDetails): void {
    const event = new CustomEvent('show-permission-error', {
      detail: { error }
    });
    window.dispatchEvent(event);
  }

  private async waitAndRetry(error: ErrorDetails): Promise<boolean> {
    await this.sleep(5000); // Wait 5 seconds for rate limit
    return await this.retryOriginalRequest(error);
  }

  private logAndUseFallback(error: ErrorDetails): boolean {
    console.error('Unrecoverable error, using fallback:', error);
    return this.useFallbackData(error);
  }

  /**
   * Utility functions
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private logError(error: ErrorDetails): void {
    console.error(`[Error ${error.id}]`, {
      type: error.type,
      message: error.message,
      timestamp: error.timestamp,
      context: error.context
    });

    // Send to monitoring service if available
    this.sendToMonitoring(error);
  }

  private sendToMonitoring(error: ErrorDetails): void {
    // Implementation for sending to monitoring services
    // like Sentry, LogRocket, etc.
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const errorLog = {
          ...error,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: error.timestamp.toISOString()
        };
        
        const existingLogs = JSON.parse(
          window.localStorage.getItem('error_logs') || '[]'
        );
        existingLogs.push(errorLog);
        
        // Keep only last 100 errors
        if (existingLogs.length > 100) {
          existingLogs.splice(0, existingLogs.length - 100);
        }
        
        window.localStorage.setItem('error_logs', JSON.stringify(existingLogs));
      }
    } catch (loggingError) {
      console.error('Failed to log error:', loggingError);
    }
  }

  private notifyErrorListeners(error: ErrorDetails): void {
    this.recoveryListeners.forEach(listener => {
      try {
        listener(error);
      } catch (listenerError) {
        console.error('Error listener failed:', listenerError);
      }
    });
  }

  /**
   * Public API
   */
  public addErrorListener(listener: (error: ErrorDetails) => void): void {
    this.recoveryListeners.add(listener);
  }

  public removeErrorListener(listener: (error: ErrorDetails) => void): void {
    this.recoveryListeners.delete(listener);
  }

  public getErrorHistory(): ErrorDetails[] {
    return [...this.errorQueue];
  }

  public clearErrorHistory(): void {
    this.errorQueue = [];
  }

  public getSystemStatus(): {
    isOnline: boolean;
    hasErrors: boolean;
    activeErrors: number;
    circuitBreakerCount: number;
  } {
    return {
      isOnline: navigator.onLine,
      hasErrors: this.errorQueue.length > 0,
      activeErrors: this.errorQueue.length,
      circuitBreakerCount: this.circuitBreakers.size
    };
  }
}

interface CircuitBreakerState {
  state: 'closed' | 'open' | 'half_open';
  failureCount: number;
  lastFailureTime: Date;
  nextAttemptTime: Date;
}

interface Question {
  id: string;
  subject: string;
  topic: string;
  questionText: string;
  options: string[];
  correctAnswer: string;
  explanation: string;
  difficulty: string;
  isFallback?: boolean;
}

interface UserProgress {
  level: number;
  xp: number;
  streakDays: number;
  completedQuestions: number;
  accuracy: number;
  subjectsProgress: Record<string, any>;
  isFallback?: boolean;
}

interface LeaderboardEntry {
  rank: number;
  username: string;
  score: number;
  level: number;
}

interface StudyPlan {
  id: string;
  name: string;
  description: string;
  dailySessions: number;
  sessionDuration: number;
  subjects: string[];
  isFallback?: boolean;
}

// Export singleton instance
export const errorRecoveryService = new ErrorRecoveryService();
export { ErrorType, ErrorDetails };
export default errorRecoveryService;