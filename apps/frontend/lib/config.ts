/**
 * Configuración centralizada de la aplicación
 * Todas las variables de entorno y configuraciones en un solo lugar
 */

interface Config {
  // API Configuration
  api: {
    baseUrl: string;
    timeout: number;
    version: string;
  };
  
  // WebSocket Configuration
  websocket: {
    url: string;
    reconnectAttempts: number;
    reconnectDelay: number;
  };
  
  // Authentication
  auth: {
    tokenKey: string;
    refreshTokenKey: string;
    tokenExpiry: number;
  };
  
  // Media Configuration
  media: {
    baseUrl: string;
    maxFileSize: number;
    allowedFormats: string[];
  };
  
  // Analytics
  analytics: {
    clickhouseUrl: string;
    sentryDsn: string;
    googleAnalyticsId: string;
  };
  
  // Features Flags
  features: {
    enableAI: boolean;
    enablePayments: boolean;
    enableWebSocket: boolean;
    enableAnalytics: boolean;
    enableMaintenance: boolean;
  };
  
  // App Settings
  app: {
    name: string;
    version: string;
    environment: 'development' | 'staging' | 'production';
    debug: boolean;
  };
  
  // Cache Settings
  cache: {
    ttl: number;
    maxSize: number;
    strategy: 'memory' | 'localStorage' | 'sessionStorage';
  };
  
  // Rate Limiting
  rateLimit: {
    maxRequests: number;
    windowMs: number;
  };
  
  // External Services
  services: {
    openaiApiKey: string;
    youtubeApiKey: string;
    stripePublicKey: string;
    redisUrl: string;
  };
}

const getEnvVar = (key: string, defaultValue: string = ''): string => {
  if (typeof window === 'undefined') {
    // Server-side
    return process.env[key] || defaultValue;
  }
  // Client-side
  return process.env[`NEXT_PUBLIC_${key}`] || defaultValue;
};

const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';
const isStaging = process.env.NEXT_PUBLIC_ENVIRONMENT === 'staging';

const config: Config = {
  // API Configuration
  api: {
    baseUrl: getEnvVar('API_URL', ''), // Empty for auto-detection
    timeout: parseInt(getEnvVar('API_TIMEOUT', '15000')),
    version: 'v1',
  },
  
  // WebSocket Configuration
  websocket: {
    url: getEnvVar('WS_URL', 'ws://localhost:4002'),
    reconnectAttempts: parseInt(getEnvVar('WS_RECONNECT_ATTEMPTS', '5')),
    reconnectDelay: parseInt(getEnvVar('WS_RECONNECT_DELAY', '3000')),
  },
  
  // Authentication
  auth: {
    tokenKey: 'icfes_access_token',
    refreshTokenKey: 'icfes_refresh_token',
    tokenExpiry: parseInt(getEnvVar('TOKEN_EXPIRY', '3600')),
  },
  
  // Media Configuration
  media: {
    baseUrl: getEnvVar('MEDIA_URL', 'http://localhost:4000/media'),
    maxFileSize: parseInt(getEnvVar('MAX_FILE_SIZE', '5242880')), // 5MB
    allowedFormats: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'],
  },
  
  // Analytics
  analytics: {
    clickhouseUrl: getEnvVar('CLICKHOUSE_URL', 'http://localhost:8123'),
    sentryDsn: getEnvVar('SENTRY_DSN', ''),
    googleAnalyticsId: getEnvVar('GA_ID', ''),
  },
  
  // Feature Flags
  features: {
    enableAI: getEnvVar('ENABLE_AI', 'true') === 'true',
    enablePayments: getEnvVar('ENABLE_PAYMENTS', 'false') === 'true',
    enableWebSocket: getEnvVar('ENABLE_WEBSOCKET', 'true') === 'true',
    enableAnalytics: getEnvVar('ENABLE_ANALYTICS', 'true') === 'true',
    enableMaintenance: getEnvVar('ENABLE_MAINTENANCE', 'false') === 'true',
  },
  
  // App Settings
  app: {
    name: 'ICFES Leveling',
    version: '2.0.0',
    environment: isProduction ? 'production' : isStaging ? 'staging' : 'development',
    debug: isDevelopment || getEnvVar('DEBUG', 'false') === 'true',
  },
  
  // Cache Settings
  cache: {
    ttl: parseInt(getEnvVar('CACHE_TTL', '3600000')), // 1 hour
    maxSize: parseInt(getEnvVar('CACHE_MAX_SIZE', '50')), // 50 items
    strategy: (getEnvVar('CACHE_STRATEGY', 'memory') as Config['cache']['strategy']),
  },
  
  // Rate Limiting
  rateLimit: {
    maxRequests: parseInt(getEnvVar('RATE_LIMIT_MAX', '100')),
    windowMs: parseInt(getEnvVar('RATE_LIMIT_WINDOW', '60000')), // 1 minute
  },
  
  // External Services
  services: {
    openaiApiKey: getEnvVar('OPENAI_API_KEY', ''),
    youtubeApiKey: getEnvVar('YOUTUBE_API_KEY', ''),
    stripePublicKey: getEnvVar('STRIPE_PUBLIC_KEY', ''),
    redisUrl: getEnvVar('REDIS_URL', 'redis://localhost:6379'),
  },
};

// Validate required configuration
const validateConfig = () => {
  const errors: string[] = [];
  
  if (isProduction) {
    if (!config.analytics.sentryDsn) {
      errors.push('Sentry DSN is required in production');
    }
    if (!config.services.openaiApiKey) {
      errors.push('OpenAI API key is required');
    }
    if (config.api.baseUrl.includes('localhost')) {
      errors.push('API URL should not be localhost in production');
    }
  }
  
  if (errors.length > 0) {
    console.error('Configuration validation errors:', errors);
    if (isProduction) {
      throw new Error('Invalid configuration for production');
    }
  }
};

// Run validation
if (typeof window !== 'undefined') {
  validateConfig();
}

// Helper functions
export const getApiUrl = (path: string = ''): string => {
  const base = `${config.api.baseUrl}/api/${config.api.version}`;
  return path ? `${base}${path}` : base;
};

export const getMediaUrl = (path: string): string => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `${config.media.baseUrl}/${path}`;
};

export const getImageUrl = (imagePath: string): string => {
  if (!imagePath || imagePath === 'No Aplica' || imagePath.trim() === '') {
    return '';
  }
  if (imagePath.startsWith('http')) {
    return imagePath;
  }
  
  // Auto-detect API URL for images
  const baseUrl = config.api.baseUrl || 
    (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:4000` : 'http://localhost:4000');
  
  return `${baseUrl}/api/images/${imagePath}`;
};

export const isFeatureEnabled = (feature: keyof Config['features']): boolean => {
  return config.features[feature];
};

export const getWebSocketUrl = (): string => {
  if (!isFeatureEnabled('enableWebSocket')) {
    throw new Error('WebSocket is disabled');
  }
  return config.websocket.url;
};

// Export configuration
export default config;

// Type exports
export type { Config };