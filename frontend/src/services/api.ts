import axios from 'axios';

// Configuración base de axios
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para añadir el token a las requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores globalmente
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o inválido
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Servicios de autenticación
export const authService = {
  // Login
  login: (email: string, password: string) => 
    api.post('/api/v1/auth/login', { email, password }),
  
  // Registro
  register: (email: string, password: string, full_name: string, country_code: string = 'CO') =>
    api.post('/api/v1/auth/register', { email, password, full_name, country_code }),
  
  // Logout
  logout: () => api.post('/api/v1/auth/logout'),
  
  // Validar token
  validate: () => api.get('/api/v1/auth/validate'),
  
  // Información del usuario actual
  me: () => api.get('/api/v1/auth/me'),
};

// Servicios genéricos para CRUD
export const apiService = {
  // GET - Obtener todos los elementos
  getAll: (endpoint: string) => api.get(`/api/v1/${endpoint}`),
  
  // GET - Obtener elemento por ID
  getById: (endpoint: string, id: number) => api.get(`/api/v1/${endpoint}/${id}`),
  
  // POST - Crear nuevo elemento
  create: (endpoint: string, data: any) => api.post(`/api/v1/${endpoint}`, data),
  
  // PUT - Actualizar elemento
  update: (endpoint: string, id: number, data: any) => api.put(`/api/v1/${endpoint}/${id}`, data),
  
  // DELETE - Eliminar elemento
  delete: (endpoint: string, id: number) => api.delete(`/api/v1/${endpoint}/${id}`),
  
  // GET - Buscar con parámetros
  search: (endpoint: string, params: any) => api.get(`/api/v1/${endpoint}`, { params }),
};

export default api;
