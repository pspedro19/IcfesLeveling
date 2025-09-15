/**
 * Dynamic Configuration System for Frontend
 * ========================================
 * Automatically detects environment and configures URLs dynamically.
 * No hardcoded URLs - fully portable across any server environment.
 */

interface ServerConfig {
  host: string;
  frontendPort: number;
  backendPort: number;
  protocol: string;
  frontendUrl: string;
  backendUrl: string;
  imageApiUrl: string;
}

interface EnvironmentInfo {
  isDevelopment: boolean;
  isProduction: boolean;
  isDocker: boolean;
  nodeEnv: string;
}

class DynamicConfigManager {
  private static instance: DynamicConfigManager;
  private _config: ServerConfig | null = null;
  private _environment: EnvironmentInfo | null = null;

  static getInstance(): DynamicConfigManager {
    if (!DynamicConfigManager.instance) {
      DynamicConfigManager.instance = new DynamicConfigManager();
    }
    return DynamicConfigManager.instance;
  }

  /**
   * Detect current environment
   */
  private detectEnvironment(): EnvironmentInfo {
    const nodeEnv = process.env.NODE_ENV || 'development';
    const isDevelopment = nodeEnv === 'development';
    const isProduction = nodeEnv === 'production';
    
    // Check if running in Docker (browser can't directly detect this, so we use other indicators)
    const isDocker = typeof window !== 'undefined' ? 
      window.location.hostname !== 'localhost' : 
      process.env.DOCKER_ENV === 'true';

    return {
      isDevelopment,
      isProduction,
      isDocker,
      nodeEnv
    };
  }

  /**
   * Get host information based on environment
   */
  private getHost(): string {
    // Server-side rendering
    if (typeof window === 'undefined') {
      return process.env.HOST_IP || 'localhost';
    }

    // Client-side - use current window location
    return window.location.hostname;
  }

  /**
   * Get ports from environment or detect from current URL
   */
  private getPorts(): { frontend: number; backend: number } {
    let frontendPort = 4001;
    let backendPort = 4000;

    // Try environment variables first
    if (process.env.FRONTEND_PORT) {
      frontendPort = parseInt(process.env.FRONTEND_PORT, 10);
    }
    if (process.env.BACKEND_PORT) {
      backendPort = parseInt(process.env.BACKEND_PORT, 10);
    }

    // If in browser, detect from current location
    if (typeof window !== 'undefined') {
      const currentPort = window.location.port;
      if (currentPort) {
        frontendPort = parseInt(currentPort, 10);
        // Backend typically runs on frontend port - 1
        backendPort = frontendPort - 1;
      }
    }

    return { frontend: frontendPort, backend: backendPort };
  }

  /**
   * Determine protocol (http/https)
   */
  private getProtocol(): string {
    // Check environment variable first
    if (process.env.USE_HTTPS === 'true') {
      return 'https';
    }

    // If in browser, use current protocol
    if (typeof window !== 'undefined') {
      return window.location.protocol.replace(':', '');
    }

    // Default to http for development
    return 'http';
  }

  /**
   * Build server configuration
   */
  private buildConfig(): ServerConfig {
    const host = this.getHost();
    const ports = this.getPorts();
    const protocol = this.getProtocol();

    const frontendUrl = `${protocol}://${host}:${ports.frontend}`;
    const backendUrl = `${protocol}://${host}:${ports.backend}`;
    const imageApiUrl = `${backendUrl}/dynamic-images`;

    return {
      host,
      frontendPort: ports.frontend,
      backendPort: ports.backend,
      protocol,
      frontendUrl,
      backendUrl,
      imageApiUrl
    };
  }

  /**
   * Get current server configuration
   */
  getConfig(): ServerConfig {
    if (!this._config) {
      this._config = this.buildConfig();
      console.log('[DynamicConfig] Configuration created:', this._config);
    }
    return this._config;
  }

  /**
   * Get environment information
   */
  getEnvironment(): EnvironmentInfo {
    if (!this._environment) {
      this._environment = this.detectEnvironment();
      console.log('[DynamicConfig] Environment detected:', this._environment);
    }
    return this._environment;
  }

  /**
   * Generate full image URL from relative path
   */
  getImageUrl(relativePath: string | null | undefined): string | null {
    if (!relativePath || relativePath.trim() === '' || relativePath === 'No Aplica') {
      return null;
    }

    const config = this.getConfig();
    const cleanPath = relativePath.replace(/^\/+/, ''); // Remove leading slashes
    return `${config.imageApiUrl}/serve/${encodeURIComponent(cleanPath)}`;
  }

  /**
   * Get API endpoint URL
   */
  getApiUrl(endpoint: string): string {
    const config = this.getConfig();
    const cleanEndpoint = endpoint.replace(/^\/+/, ''); // Remove leading slashes
    return `${config.backendUrl}/api/v1/${cleanEndpoint}`;
  }

  /**
   * Get dynamic images API URL
   */
  getDynamicImagesUrl(endpoint: string = ''): string {
    const config = this.getConfig();
    const cleanEndpoint = endpoint.replace(/^\/+/, ''); // Remove leading slashes
    return `${config.imageApiUrl}${cleanEndpoint ? `/${cleanEndpoint}` : ''}`;
  }

  /**
   * Refresh configuration (useful for testing)
   */
  refresh(): ServerConfig {
    this._config = null;
    this._environment = null;
    return this.getConfig();
  }
}

// Global instance
const configManager = DynamicConfigManager.getInstance();

// Export convenience functions
export const getServerConfig = (): ServerConfig => configManager.getConfig();
export const getEnvironment = (): EnvironmentInfo => configManager.getEnvironment();
export const getImageUrl = (relativePath: string | null | undefined): string | null => 
  configManager.getImageUrl(relativePath);
export const getApiUrl = (endpoint: string): string => configManager.getApiUrl(endpoint);
export const getDynamicImagesUrl = (endpoint?: string): string => 
  configManager.getDynamicImagesUrl(endpoint);

// Development helpers
export const isDevelopment = (): boolean => getEnvironment().isDevelopment;
export const isProduction = (): boolean => getEnvironment().isProduction;
export const isDocker = (): boolean => getEnvironment().isDocker;

// Refresh function for testing
export const refreshConfig = (): ServerConfig => configManager.refresh();

// Default export
export default configManager;

/**
 * React Hook for dynamic configuration
 */
import { useEffect, useState } from 'react';

export const useDynamicConfig = () => {
  const [config, setConfig] = useState<ServerConfig | null>(null);
  const [environment, setEnvironment] = useState<EnvironmentInfo | null>(null);

  useEffect(() => {
    setConfig(getServerConfig());
    setEnvironment(getEnvironment());
  }, []);

  return {
    config,
    environment,
    getImageUrl,
    getApiUrl,
    getDynamicImagesUrl,
    refresh: () => {
      const newConfig = refreshConfig();
      setConfig(newConfig);
      setEnvironment(getEnvironment());
      return newConfig;
    }
  };
};

/**
 * Utility function to check if image URL is available
 */
export const checkImageAvailability = async (relativePath: string): Promise<boolean> => {
  const imageUrl = getImageUrl(relativePath);
  if (!imageUrl) return false;

  try {
    const response = await fetch(imageUrl, { method: 'HEAD' });
    return response.ok;
  } catch {
    return false;
  }
};

/**
 * Batch check multiple images
 */
export const checkMultipleImages = async (relativePaths: (string | null)[]): Promise<boolean[]> => {
  const checkPromises = relativePaths.map(path => 
    path ? checkImageAvailability(path) : Promise.resolve(false)
  );
  
  return Promise.all(checkPromises);
};