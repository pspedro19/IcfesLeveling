/**
 * Configuración Dinámica para ICFES Leveling
 * Detecta automáticamente las URLs correctas basándose en el entorno
 * Funciona en cualquier servidor sin hardcodear IPs
 */

export interface DynamicConfig {
  apiUrl: string;
  wsUrl: string;
  isDevelopment: boolean;
  isServer: boolean;
}

/**
 * Detecta la URL base del API de forma automática
 */
function getApiBaseUrl(): string {
  // En el servidor (SSR), usar variables de entorno o localhost
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';
  }

  // En el cliente, detectar automáticamente basándose en window.location
  const protocol = window.location.protocol; // http: o https:
  const hostname = window.location.hostname; // IP o dominio actual
  
  // Si hay variable de entorno definida, usarla
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Auto-detección: usar el mismo host pero puerto 4000 para API
  return `${protocol}//${hostname}:4000`;
}

/**
 * Detecta la URL del WebSocket de forma automática
 */
function getWebSocketUrl(): string {
  // En el servidor (SSR), usar variables de entorno o localhost
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:4002';
  }

  // En el cliente, detectar automáticamente
  const hostname = window.location.hostname;
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  // Si hay variable de entorno definida, usarla
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL;
  }
  
  // Auto-detección: usar el mismo host pero puerto 4002 para WebSocket
  return `${wsProtocol}//${hostname}:4002`;
}

/**
 * Configuración dinámica principal
 */
export function getDynamicConfig(): DynamicConfig {
  const apiUrl = getApiBaseUrl();
  const wsUrl = getWebSocketUrl();
  const isDevelopment = process.env.NODE_ENV === 'development';
  const isServer = typeof window === 'undefined';

  const config = {
    apiUrl,
    wsUrl,
    isDevelopment,
    isServer,
  };

  // Log solo en desarrollo y en el cliente
  if (isDevelopment && !isServer) {
    console.log('🔧 Dynamic Config Detected:', config);
  }

  return config;
}

/**
 * Hook de React para usar la configuración dinámica
 */
import { useState, useEffect } from 'react';

export function useDynamicConfig(): DynamicConfig {
  const [config, setConfig] = useState<DynamicConfig>(() => getDynamicConfig());

  useEffect(() => {
    // Actualizar configuración cuando el componente se monte en el cliente
    setConfig(getDynamicConfig());
  }, []);

  return config;
}

/**
 * Función utilitaria para construir URLs de API
 */
export function buildApiUrl(endpoint: string): string {
  const config = getDynamicConfig();
  const baseUrl = config.apiUrl.replace(/\/$/, ''); // Remover slash final si existe
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
}

/**
 * Función utilitaria para construir URLs de WebSocket
 */
export function buildWebSocketUrl(path: string = ''): string {
  const config = getDynamicConfig();
  const baseUrl = config.wsUrl.replace(/\/$/, ''); // Remover slash final si existe
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
}

export default getDynamicConfig;