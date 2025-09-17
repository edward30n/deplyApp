/**
 * Configuración centralizada del API
 * Maneja la transición automática entre desarrollo local y Azure
 */

// Obtener URL del API desde variables de entorno
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Environment info
export const ENV = import.meta.env.VITE_ENV || 'development';
export const IS_PRODUCTION = ENV === 'production';
export const IS_DEVELOPMENT = ENV === 'development';

// App info
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'RecWay';
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';

// Función helper para construir URLs de API
export const buildApiUrl = (endpoint: string): string => {
  // Asegurar que no haya doble slash
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${API_BASE_URL}${cleanEndpoint}`;
};

// Función helper para logging con contexto de environment
export const apiLog = (message: string, data?: any) => {
  if (IS_DEVELOPMENT) {
    console.log(`[API ${ENV.toUpperCase()}] ${message}`, data || '');
  }
};

// Configuración de headers comunes
export const getApiHeaders = () => ({
  'Content-Type': 'application/json',
  'Accept': 'application/json',
});

// Log de configuración inicial
apiLog(`🚀 API configurado para ${ENV}`, {
  baseUrl: API_BASE_URL,
  isProduction: IS_PRODUCTION
});