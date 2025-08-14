// Configuración de puertos para desarrollo local
// ✅ ALINEADO: Configuración actualizada para puertos 4000, 4001, 4002

const config = {
  // URLs del backend
  BACKEND_URL: 'http://localhost:4000',  // ✅ Cambiado de 8000 a 4000
  API_URL: 'http://localhost:4000/api/v1',  // ✅ Cambiado de 8000 a 4000
  
  // Puertos
  FRONTEND_PORT: 4001,  // ✅ Cambiado de 3000 a 4001
  BACKEND_PORT: 4000,   // ✅ Cambiado de 8000 a 4000
  WEBSOCKET_PORT: 4002, // ✅ Agregado puerto WebSocket
  
  // Configuración de desarrollo
  DEV_MODE: true,
  CORS_ENABLED: true,
  
  // Endpoints importantes
  ENDPOINTS: {
    LOGIN: '/api/v1/auth/login',
    HEALTH: '/api/v1/health',
    QUESTIONS: '/api/v1/questions/multimedia',
    DIAGNOSTIC: '/api/v1/diagnostic',
    WEBSOCKET: 'ws://localhost:4002'  // ✅ Agregado endpoint WebSocket
  }
};

// Para navegador
if (typeof window !== 'undefined') {
  window.APP_CONFIG = config;
}

// Para Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = config;
}

export default config;