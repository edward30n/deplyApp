import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Database, 
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Droplets,
  Thermometer,
  Wind
} from 'lucide-react';

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard RecWay</h1>
          <p className="text-gray-600 mt-1">
            Monitoreo ambiental en tiempo real
          </p>
        </div>
        <Button>
          <TrendingUp className="mr-2 h-4 w-4" />
          Nuevo Reporte
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Sensores Activos
            </CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">24</div>
            <p className="text-xs text-gray-600">
              +2 desde ayer
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Segmentos
            </CardTitle>
            <Database className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">8</div>
            <p className="text-xs text-gray-600">
              Todos funcionando
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Muestras Hoy
            </CardTitle>
            <Droplets className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">1,247</div>
            <p className="text-xs text-gray-600">
              +125 desde ayer
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Estado Sistema
            </CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">Óptimo</div>
            <p className="text-xs text-gray-600">
              Todos los sistemas OK
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Environmental Status */}
        <Card>
          <CardHeader>
            <CardTitle>Estado Ambiental</CardTitle>
            <CardDescription>
              Parámetros en tiempo real
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Thermometer className="h-4 w-4 text-red-500" />
                  <span className="text-sm font-medium">Temperatura</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">23.5°C</span>
                  <Badge variant="secondary">Normal</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Droplets className="h-4 w-4 text-blue-500" />
                  <span className="text-sm font-medium">pH</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">7.2</span>
                  <Badge variant="default">Óptimo</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Wind className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium">Oxígeno Disuelto</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">8.5 mg/L</span>
                  <Badge variant="default">Bueno</Badge>
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm font-medium">Turbidez</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium">12 NTU</span>
                  <Badge variant="outline">Advertencia</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Actividad Reciente</CardTitle>
            <CardDescription>
              Últimas actividades del sistema
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                {
                  id: 1,
                  action: 'Sensor pH actualizado',
                  time: 'Hace 5 min',
                  status: 'success',
                  location: 'Segmento A-01'
                },
                {
                  id: 2,
                  action: 'Alerta de temperatura',
                  time: 'Hace 12 min',
                  status: 'warning',
                  location: 'Segmento B-03'
                },
                {
                  id: 3,
                  action: 'Reporte generado',
                  time: 'Hace 1 hora',
                  status: 'info',
                  location: 'Sistema Central'
                },
                {
                  id: 4,
                  action: 'Sensor reconectado',
                  time: 'Hace 2 horas',
                  status: 'success',
                  location: 'Segmento C-02'
                }
              ].map((activity) => (
                <div key={activity.id} className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      activity.status === 'success' ? 'bg-green-500' :
                      activity.status === 'warning' ? 'bg-yellow-500' :
                      activity.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                    }`} />
                    <div>
                      <span className="text-sm font-medium">{activity.action}</span>
                      <p className="text-xs text-gray-500">{activity.location}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">{activity.time}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Tendencias de Calidad</CardTitle>
            <CardDescription>
              Evolución de parámetros clave
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg">
              <div className="text-center">
                <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">Gráfico de tendencias</p>
                <p className="text-xs text-gray-400">Se integrará con Chart.js</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Distribución de Sensores</CardTitle>
            <CardDescription>
              Estado por segmento
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg">
              <div className="text-center">
                <Database className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">Mapa de distribución</p>
                <p className="text-xs text-gray-400">Vista interactiva próximamente</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
