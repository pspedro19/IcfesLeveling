const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export interface BackendHealthStatus {
  isConnected: boolean;
  status: 'healthy' | 'unhealthy' | 'unreachable';
  responseTime?: number;
  error?: string;
  details?: any;
}

export class BackendHealthService {
  private static instance: BackendHealthService;
  private lastCheck: number = 0;
  private cacheTimeout: number = 30000; // 30 segundos

  static getInstance(): BackendHealthService {
    if (!BackendHealthService.instance) {
      BackendHealthService.instance = new BackendHealthService();
    }
    return BackendHealthService.instance;
  }

  async checkHealth(forceCheck: boolean = false): Promise<BackendHealthStatus> {
    const now = Date.now();
    
    // Usar cache si no es muy antiguo y no se fuerza la verificación
    if (!forceCheck && (now - this.lastCheck) < this.cacheTimeout) {
      return this.getCachedStatus();
    }

    try {
      console.log('🔍 Verificando salud del backend en:', API_BASE_URL);
      
      const startTime = Date.now();
      const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000), // 5 segundos timeout
      });
      
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        const status: BackendHealthStatus = {
          isConnected: true,
          status: 'healthy',
          responseTime,
          details: data
        };
        
        this.cacheStatus(status);
        return status;
      } else {
        const status: BackendHealthStatus = {
          isConnected: true,
          status: 'unhealthy',
          responseTime,
          error: `HTTP ${response.status}: ${response.statusText}`,
          details: { statusCode: response.status }
        };
        
        this.cacheStatus(status);
        return status;
      }
      
    } catch (error) {
      console.error('❌ Error verificando salud del backend:', error);
      
      const status: BackendHealthStatus = {
        isConnected: false,
        status: 'unreachable',
        error: error instanceof Error ? error.message : 'Error desconocido'
      };
      
      this.cacheStatus(status);
      return status;
    }
  }

  async checkDetailedHealth(): Promise<{
    basic: BackendHealthStatus;
    database: boolean;
    auth: boolean;
    questions: boolean;
  }> {
    const basic = await this.checkHealth(true);
    
    if (!basic.isConnected) {
      return {
        basic,
        database: false,
        auth: false,
        questions: false
      };
    }

    const results = await Promise.allSettled([
      this.checkDatabase(),
      this.checkAuth(),
      this.checkQuestions()
    ]);

    return {
      basic,
      database: results[0].status === 'fulfilled' && results[0].value,
      auth: results[1].status === 'fulfilled' && results[1].value,
      questions: results[2].status === 'fulfilled' && results[2].value
    };
  }

  private async checkDatabase(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000)
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.database === 'connected';
      }
      return false;
    } catch {
      return false;
    }
  }

  private async checkAuth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000)
      });
      
      // Si responde (aunque sea 401), el endpoint está funcionando
      return response.status !== 500;
    } catch {
      return false;
    }
  }

  private async checkQuestions(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/questions/multimedia?limit=1`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000)
      });
      
      return response.status !== 500;
    } catch {
      return false;
    }
  }

  private cacheStatus(status: BackendHealthStatus): void {
    this.lastCheck = Date.now();
    if (typeof window !== 'undefined') {
      localStorage.setItem('backend_health_status', JSON.stringify({
        status,
        timestamp: this.lastCheck
      }));
    }
  }

  private getCachedStatus(): BackendHealthStatus {
    if (typeof window !== 'undefined') {
      const cached = localStorage.getItem('backend_health_status');
      if (cached) {
        try {
          const data = JSON.parse(cached);
          return data.status;
        } catch {
          // Si hay error al parsear, continuar con verificación
        }
      }
    }
    
    return {
      isConnected: false,
      status: 'unreachable',
      error: 'No hay datos en caché'
    };
  }

  getConnectionInfo(): {
    url: string;
    port: number;
    protocol: string;
  } {
    const url = new URL(API_BASE_URL);
    return {
      url: API_BASE_URL,
      port: parseInt(url.port) || (url.protocol === 'https:' ? 443 : 80),
      protocol: url.protocol
    };
  }

  async testConnection(): Promise<{
    success: boolean;
    message: string;
    details?: any;
  }> {
    try {
      const health = await this.checkHealth(true);
      
      if (health.isConnected) {
        return {
          success: true,
          message: `✅ Backend conectado exitosamente en ${API_BASE_URL}`,
          details: health
        };
      } else {
        return {
          success: false,
          message: `❌ No se pudo conectar al backend en ${API_BASE_URL}`,
          details: health
        };
      }
    } catch (error) {
      return {
        success: false,
        message: `❌ Error al verificar conexión: ${error instanceof Error ? error.message : 'Error desconocido'}`,
        details: { error }
      };
    }
  }
}

// Exportar instancia singleton
export const backendHealthService = BackendHealthService.getInstance(); 