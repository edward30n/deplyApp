import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import DashboardSecure from './pages/Dashboard/DashboardSecure';
import HomePage from './pages/HomePage';
// Importar los módulos de autenticación adaptados para React Router
import LoginPage from './pages/auth/LoginPage';
import SignupPage from './pages/auth/SignupPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';

// Crear cliente de React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Ruta principal - HomePage */}
            <Route path="/" element={<HomePage />} />
            <Route path="/home" element={<HomePage />} />
            
            {/* Rutas de autenticación (sin layout) */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            
            {/* Ruta de dashboard simple y seguro */}
            <Route 
              path="/dashboard-secure" 
              element={
                <ProtectedRoute>
                  <DashboardSecure />
                </ProtectedRoute>
              }
            />
            
            {/* Rutas protegidas con layout para dashboard completo */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="sensores" element={<div className="p-6">Sensores - En desarrollo</div>} />
              <Route path="segmentos" element={<div className="p-6">Segmentos - En desarrollo</div>} />
              <Route path="muestras" element={<div className="p-6">Muestras - En desarrollo</div>} />
              <Route path="analisis" element={<div className="p-6">Análisis - En desarrollo</div>} />
              <Route path="configuracion" element={<div className="p-6">Configuración - En desarrollo</div>} />
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
