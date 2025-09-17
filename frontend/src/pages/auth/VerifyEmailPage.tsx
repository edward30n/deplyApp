import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { buildApiUrl } from '../../config/api';

const VerifyEmailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  // const navigate = useNavigate(); // No se usa actualmente
  const [verificationStatus, setVerificationStatus] = useState<'loading' | 'success' | 'error' | 'already-verified'>('loading');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');
      
      if (!token) {
        setVerificationStatus('error');
        setErrorMessage('Token de verificación no encontrado');
        setIsLoading(false);
        return;
      }

      try {
        console.log('🔍 Attempting to verify email with token:', token);
        
        const response = await fetch(buildApiUrl(`/api/v1/auth/verify-email?token=${token}`), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        console.log('📡 Response status:', response.status);
        console.log('📡 Response ok:', response.ok);

        const data = await response.json();
        console.log('📦 Response data:', data);

        if (response.ok) {
          console.log('✅ Response is OK, checking message...');
          console.log('📝 Message received:', data.message);
          
          if (data.message.includes('already verified')) {
            console.log('🔄 Email already verified');
            setVerificationStatus('already-verified');
          } else {
            console.log('🎉 Email verified successfully');
            setVerificationStatus('success');
          }
        } else {
          console.log('❌ Response not OK, setting error');
          console.log('🚫 Error detail:', data.detail);
          setVerificationStatus('error');
          setErrorMessage(data.detail || 'Error al verificar el email');
        }
      } catch (error) {
        console.error('🚨 Verification error:', error);
        setVerificationStatus('error');
        setErrorMessage('Error de conexión. Inténtalo de nuevo.');
      } finally {
        setIsLoading(false);
      }
    };

    verifyEmail();
  }, [searchParams]);

  // Add enter animation when the component mounts
  useEffect(() => {
    document.body.classList.remove('page-transition-exit');
    document.body.classList.add('page-transition-enter');
    
    const timer = setTimeout(() => {
      document.body.classList.remove('page-transition-enter');
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);

  const renderContent = () => {
    if (isLoading || verificationStatus === 'loading') {
      return (
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-white text-xl font-semibold mb-2">Verificando tu email...</h3>
          <p className="text-white">Por favor espera mientras verificamos tu cuenta.</p>
        </div>
      );
    }

    if (verificationStatus === 'success') {
      return (
        <div className="text-center">
          <div className="bg-green-100 bg-opacity-20 rounded-lg p-4 mb-6">
            <svg className="w-16 h-16 text-green-400 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <h3 className="text-white text-xl font-semibold mb-2">¡Email Verificado!</h3>
            <p className="text-white mb-4">
              Tu cuenta ha sido verificada exitosamente. Ahora puedes iniciar sesión.
            </p>
          </div>
          <Link to="/login">
            <button className="w-full bg-[#1e88e5] text-white py-4 rounded-full hover:bg-[#1565c0] transition-colors">
              Ir al Login
            </button>
          </Link>
        </div>
      );
    }

    if (verificationStatus === 'already-verified') {
      return (
        <div className="text-center">
          <div className="bg-yellow-100 bg-opacity-20 rounded-lg p-4 mb-6">
            <svg className="w-16 h-16 text-yellow-400 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <h3 className="text-white text-xl font-semibold mb-2">Email Ya Verificado</h3>
            <p className="text-white mb-4">
              Tu email ya había sido verificado anteriormente. Puedes iniciar sesión normalmente.
            </p>
          </div>
          <Link to="/login">
            <button className="w-full bg-[#1e88e5] text-white py-4 rounded-full hover:bg-[#1565c0] transition-colors">
              Ir al Login
            </button>
          </Link>
        </div>
      );
    }

    if (verificationStatus === 'error') {
      return (
        <div className="text-center">
          <div className="bg-red-100 bg-opacity-20 rounded-lg p-4 mb-6">
            <svg className="w-16 h-16 text-red-400 mx-auto mb-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <h3 className="text-white text-xl font-semibold mb-2">Error de Verificación</h3>
            <p className="text-white mb-4">{errorMessage}</p>
          </div>
          <div className="space-y-3">
            <Link to="/signup">
              <button className="w-full bg-[#1e88e5] text-white py-4 rounded-full hover:bg-[#1565c0] transition-colors">
                Crear Nueva Cuenta
              </button>
            </Link>
            <Link to="/login">
              <button className="w-full bg-gray-600 text-white py-4 rounded-full hover:bg-gray-700 transition-colors">
                Volver al Login
              </button>
            </Link>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6" 
      style={{
        background: "linear-gradient(to top right, #1e88e5, rgb(33, 33, 33), #1e3a8a)",
        backgroundSize: "400% 400%",
        animation: "gradient 15s ease infinite"
      }}>
      <style>{`
        @keyframes gradient {
          0% {
              background-position: 0% 50%;
          }
          50% {
              background-position: 100% 50%;
          }
          100% {
              background-position: 0% 50%;
          }
        }
      `}</style>

      <div className="flex items-center justify-center w-full">
        <div className="bg-black bg-opacity-20 backdrop-blur-lg rounded-[30px] shadow-lg p-8 w-full max-w-md"
             style={{boxShadow: "0 4px 30px rgb(255, 255, 255), 0 0 60px rgba(0, 0, 0, 0)"}}>
          <div className="flex justify-center mb-6">
            <img 
              src="/assets/fulllogo_transparent_nobuffer.svg" 
              alt="RecWay Logo" 
              className="h-20 w-auto" 
            />
          </div>
          <h2 className="text-center text-4xl font-bold text-white mb-6">Verificar Email</h2>
          
          {renderContent()}
          
          <div className="mt-6 text-center">
            <Link to="/" className="text-blue-400 hover:text-blue-300 text-sm">
              Volver al inicio
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmailPage;
