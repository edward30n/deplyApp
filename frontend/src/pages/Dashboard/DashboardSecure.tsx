import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import RoadQualityMap from '../../components/RoadQualityMap';
import { buildApiUrl } from '../../config/api';

interface SystemStatus {
  servidor: {
    status: string;
    online: boolean;
  };
  base_de_datos: {
    status: string;
    online: boolean;
  };
  api: {
    status: string;
    online: boolean;
  };
}

const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    servidor: { status: 'Verificando...', online: false },
    base_de_datos: { status: 'Verificando...', online: false },
    api: { status: 'Verificando...', online: false }
  });

  // Función para obtener el estado del sistema
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(buildApiUrl('/api/v1/auth/health'));
      const data = await response.json();
      
      if (data.components) {
        setSystemStatus(data.components);
      }
    } catch (error) {
      console.error('Error fetching system status:', error);
      setSystemStatus({
        servidor: { status: 'Error', online: false },
        base_de_datos: { status: 'Error', online: false },
        api: { status: 'Error', online: false }
      });
    }
  };

  // Cargar estado del sistema al montar el componente
  useEffect(() => {
    fetchSystemStatus();
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <img 
                src="/assets/fulllogo_transparent_nobuffer.svg" 
                alt="RecWay Logo" 
                className="h-8 w-auto mr-4" 
              />
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Bienvenido, {user?.name}</span>
              <button
                onClick={handleLogout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          
          {/* Welcome Card */}
          <div className="bg-white rounded-lg shadow-md p-6 col-span-1 md:col-span-2 lg:col-span-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  ¡Bienvenido a RecWay!
                </h2>
                <p className="text-gray-600">
                  Tu cuenta ha sido verificada exitosamente. Ahora puedes acceder a todas las funcionalidades de la plataforma.
                </p>
              </div>
              <div className="text-green-500">
                <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </div>

          {/* User Info Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Información del Usuario</h3>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-500">Email</label>
                <p className="text-gray-900">{user?.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Nombre</label>
                <p className="text-gray-900">{user?.name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Estado</label>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✓ Email Verificado
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Acciones Rápidas</h3>
            <div className="space-y-3">
              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors">
                Nuevo Análisis
              </button>
              <button className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md text-sm font-medium transition-colors">
                Ver Reportes
              </button>
              <button className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-md text-sm font-medium transition-colors">
                Configuración
              </button>
            </div>
          </div>

          {/* Status Card */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Estado del Sistema</h3>
              <button
                onClick={fetchSystemStatus}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                title="Refrescar estado"
              >
                🔄
              </button>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Servidor</span>
                <span className={`text-sm font-medium ${systemStatus.servidor.online ? 'text-green-600' : 'text-red-600'}`}>
                  ● {systemStatus.servidor.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Base de Datos</span>
                <span className={`text-sm font-medium ${systemStatus.base_de_datos.online ? 'text-green-600' : 'text-red-600'}`}>
                  ● {systemStatus.base_de_datos.status}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API</span>
                <span className={`text-sm font-medium ${systemStatus.api.online ? 'text-green-600' : 'text-red-600'}`}>
                  ● {systemStatus.api.status}
                </span>
              </div>
            </div>
          </div>

          {/* Road Quality Analysis Map */}
          <div className="bg-white rounded-lg shadow-md p-6 col-span-1 md:col-span-2 lg:col-span-3">
            <RoadQualityMap height="600px" />
          </div>

        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
