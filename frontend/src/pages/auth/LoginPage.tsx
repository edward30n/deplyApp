import React, { useState, useEffect } from "react"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { useAuth } from "../../contexts/AuthContext"
import { buildApiUrl } from '../../config/api'

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [errorMessage, setErrorMessage] = useState("") 
  const [showForgotPassword, setShowForgotPassword] = useState(false)
  const [resetEmail, setResetEmail] = useState("")
  const [resetEmailSent, setResetEmailSent] = useState(false)
  const [resetEmailLoading, setResetEmailLoading] = useState(false)
  const [resetEmailError, setResetEmailError] = useState("")
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isLoading, isAuthenticated } = useAuth()

  // Redirigir si ya está autenticado
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard-secure';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Add enter animation when the component mounts
  useEffect(() => {
    document.body.classList.remove('page-transition-exit')
    document.body.classList.add('page-transition-enter')
    
    const timer = setTimeout(() => {
      document.body.classList.remove('page-transition-enter')
    }, 500)
    
    return () => clearTimeout(timer)
  }, [])

  const togglePassword = () => {
    setShowPassword(!showPassword)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(""); 

    try {
      const success = await login(email, password);
      
      if (success) {
        // Redirigir al dashboard seguro
        const from = location.state?.from?.pathname || '/dashboard-secure';
        navigate(from, { replace: true });
      }
      
    } catch (error: any) {
      console.error("Login error:", error);
      
      // Manejar errores específicos
      if (error.message && error.message.includes("Email not verified")) {
        setErrorMessage("Tu email no ha sido verificado. Por favor, revisa tu bandeja de entrada y verifica tu cuenta antes de iniciar sesión.");
      } else if (error.message && error.message.includes("Invalid email or password")) {
        setErrorMessage("Email o contraseña incorrectos. Verifica tus credenciales.");
      } else if (error.message && error.message.includes("inactive")) {
        setErrorMessage("Tu cuenta está inactiva. Contacta al soporte.");
      } else {
        setErrorMessage(error.message || "Error al iniciar sesión. Inténtalo de nuevo.");
      }
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setResetEmailLoading(true)
    setResetEmailError("")

    try {
      const response = await fetch(buildApiUrl("/api/v1/auth/request-password-reset"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: resetEmail }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to request password reset");
      }

      setResetEmailSent(true)
    } catch (error: any) {
      console.error("Password reset request error:", error);
      setResetEmailError(error.message || "Something went wrong. Please try again.");
    } finally {
      setResetEmailLoading(false);
    }
  }

  const closeForgotPasswordModal = () => {
    setShowForgotPassword(false)
    setResetEmailSent(false)
    setResetEmailError("")
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 bg-gradient-to-tr from-blue-600 via-gray-800 to-blue-900 animate-gradient-x">
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
          <h2 className="text-center text-4xl font-bold text-white mb-6">Login</h2>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="email" className="block text-white mb-2">Email or Username</label>
              <div className="flex items-center bg-white rounded-full overflow-hidden">
                <div className="flex items-center justify-center w-10 h-10 ml-2">
                  <i className="fas fa-user text-gray-600"></i>
                </div>
                <input 
                  type="text" 
                  id="email" 
                  className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                  placeholder="Enter your email or username" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required 
                />
              </div>
            </div>
            
            <div className="mb-4">
              <label htmlFor="password" className="block text-white mb-2">Password</label>
              <div className="flex items-center border bg-white border-gray-300 rounded-full focus-within:border-gray-500 relative">
                <div className="flex items-center justify-center w-10 h-10 ml-2">
                  <i className="fas fa-lock text-gray-600"></i>
                </div>
                <input 
                  type={showPassword ? "text" : "password"} 
                  id="password" 
                  className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                  placeholder="Enter your password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required 
                />
                <button 
                  type="button" 
                  className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-600" 
                  onClick={togglePassword}
                >
                  <i className={showPassword ? "fas fa-eye-slash" : "fas fa-eye"}></i>
                </button>
              </div>
              <div className="mt-1 text-right">
                <button 
                  type="button" 
                  className="text-sm text-blue-300 hover:text-white transition-colors"
                  onClick={() => setShowForgotPassword(true)}
                >
                  Forgot password?
                </button>
              </div>
            </div>

            {errorMessage && (
              <div className="mb-4 text-red-500 text-sm text-center">
                {errorMessage}
              </div>
            )}

            <button 
              type="submit" 
              className="w-full bg-[#1e88e5] text-white py-4 rounded-full mb-6 hover:bg-[#1565c0] transition-colors"
              disabled={isLoading}
            >
              {isLoading ? "Logging in..." : "Login"}
            </button>
            
            <div className="flex items-center justify-center mb-6">
              <hr className="border-gray-300 flex-grow" />
              <span className="mx-2 text-white">or</span>
              <hr className="border-gray-300 flex-grow" />
            </div>
            
            <Link to="/">
              <button 
                type="button" 
                className="w-full bg-[#1e88e5] text-white py-4 rounded-full mb-6 hover:bg-[#1565c0] transition-colors"
              >
                Continue as Guest
              </button>
            </Link>
            
            <p className="text-center text-sm text-white">
              Don't have an account? <Link to="/signup" className="text-[#1e88e5] hover:text-[#1565c0] transition-colors">Sign Up</Link>
            </p>
          </form>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgotPassword && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-md w-full animate-fade-in">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-800">Reset Password</h2>
              <button 
                className="text-gray-500 hover:text-gray-700" 
                onClick={closeForgotPasswordModal}
              >
                <i className="fas fa-times"></i>
              </button>
            </div>

            {resetEmailSent ? (
              <div className="text-center py-6">
                <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <i className="fas fa-check text-green-600 text-2xl"></i>
                </div>
                <h3 className="text-xl font-semibold mb-2 text-gray-800">Reset Email Sent</h3>
                <p className="text-gray-600 mb-4">
                  We've sent instructions to reset your password to {resetEmail}.
                  Please check your inbox.
                </p>
                <button 
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  onClick={closeForgotPasswordModal}
                >
                  Back to Login
                </button>
              </div>
            ) : (
              <>
                <p className="text-gray-600 mb-4">
                  Enter your email address below and we'll send you instructions to reset your password.
                </p>
                
                {resetEmailError && (
                  <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4">
                    {resetEmailError}
                  </div>
                )}
                
                <form onSubmit={handleResetPassword}>
                  <div className="mb-4">
                    <label className="block text-gray-700 text-sm font-bold mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                      placeholder="Enter your email"
                      required
                    />
                  </div>
                  <div className="flex space-x-3">
                    <button
                      type="button"
                      onClick={closeForgotPasswordModal}
                      className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={resetEmailLoading}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                      {resetEmailLoading ? "Sending..." : "Send Reset Link"}
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
