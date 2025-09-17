import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { buildApiUrl, apiLog, getApiHeaders } from '../config/api';

// Tipos para el contexto de autenticación
interface User {
  id: string;
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Crear el contexto
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider del contexto
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Verificar token al cargar la aplicación
  useEffect(() => {
    const savedToken = localStorage.getItem('recway_token');
    const savedUser = localStorage.getItem('recway_user');
    
    if (savedToken && savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(parsedUser);
      } catch (error) {
        // Si hay error al parsear, limpiar localStorage
        localStorage.removeItem('recway_token');
        localStorage.removeItem('recway_user');
      }
    }
    
    setIsLoading(false);
  }, []);

  // Función de login con API real
  const login = async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      const url = buildApiUrl('/api/v1/auth/login');
      apiLog('🔐 Iniciando sesión', { email, url });
      
      const response = await fetch(url, {
        method: 'POST',
        headers: getApiHeaders(),
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      // Extraer información del usuario y token
      const user: User = {
        id: data.user.id.toString(),
        email: data.user.email,
        name: data.user.full_name || data.user.email
      };

      const token = data.access_token;

      // Guardar en localStorage
      localStorage.setItem('recway_token', token);
      localStorage.setItem('recway_user', JSON.stringify(user));
      localStorage.setItem('recway_refresh_token', data.refresh_token);

      // Actualizar estado
      setToken(token);
      setUser(user);
      setIsLoading(false);

      return true;
    } catch (error: any) {
      setIsLoading(false);
      throw error; // Re-lanzar el error para que el componente pueda manejarlo
    }
  };

  // Función de logout
  const logout = () => {
    localStorage.removeItem('recway_token');
    localStorage.removeItem('recway_user');
    localStorage.removeItem('recway_refresh_token');
    setToken(null);
    setUser(null);
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!token && !!user,
    isLoading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook para usar el contexto
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
