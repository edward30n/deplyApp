import React from 'react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import RecWayNavigation from './RecWayNavigation';
import './RecWayNavigation.css';

const Layout: React.FC = () => {
  const { logout } = useAuth();

  const handleAccountClick = () => {
    // En Layout, el usuario ya está autenticado, así que hacemos logout
    logout();
    window.location.href = '/home';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* RecWay Navigation */}
      <RecWayNavigation 
        logoText="RecWay"
        onAccountClick={handleAccountClick}
      />
      
      {/* Main Content - Sin sidebar por ahora */}
      <main className="p-6 pt-20">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
