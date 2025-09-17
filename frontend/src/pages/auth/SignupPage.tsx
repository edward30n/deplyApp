import React, { useState, useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"
import { buildApiUrl } from '../../config/api'

export default function SignupPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("")
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState("")
  
  const [countryCode, setCountryCode] = useState("")
  const [countries, setCountries] = useState<{ code: string; name: string }[]>([])
  
  // Estados para manejar el proceso de registro
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState("")
  const [registrationSuccess, setRegistrationSuccess] = useState(false)
  
  // Estado para el teléfono
  const [phone, setPhone] = useState("")

  const navigate = useNavigate()

  // Add enter animation when the component mounts
  useEffect(() => {
    document.body.classList.remove('page-transition-exit')
    document.body.classList.add('page-transition-enter')
    
    const timer = setTimeout(() => {
      document.body.classList.remove('page-transition-enter')
    }, 500)
    
    return () => clearTimeout(timer)
  }, [])

  useEffect(() => {
    // Fetch countries from the backend
    const fetchCountries = async () => {
      try {
        const response = await fetch(buildApiUrl("/api/v1/countries"))
        const data = await response.json()
        setCountries(data)
      } catch (error) {
        console.error("Error fetching countries:", error)
      }
    }
    fetchCountries()
  }, [])

  const togglePassword = () => {
    setShowPassword(!showPassword)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Verificar que las contraseñas coincidan
    if (password !== confirmPassword) {
      setErrorMessage("Passwords do not match.")
      return
    }
    
    // Validación básica
    if (!acceptedTerms) {
      setErrorMessage("You must accept the Terms and Conditions to create an account.")
      return
    }

    // Validar que todos los campos requeridos estén completos
    if (!email || !password || !name || !phone || !countryCode) {
      setErrorMessage("Please fill in all required fields.")
      return
    }

    setIsLoading(true)
    setErrorMessage("")

    try {
      // Payload para registro de usuario general
      const payload = {
        email,
        password,
        full_name: name,
        phone,
        country_code: countryCode,
        user_type: "general",
        company_id: null  // Usuario general sin compañía
      }

      const response = await fetch(buildApiUrl("/api/v1/auth/register"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      // Registro exitoso
      setRegistrationSuccess(true);
      
      // Reset del formulario
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      setName("");
      setPhone("");
      setCountryCode("");
      setAcceptedTerms(false);
      
      // Redirección al login después de un retraso
      setTimeout(() => {
        navigate("/login");
      }, 5000);
      
    } catch (error: any) {
      console.error("Registration error:", error);
      setErrorMessage(error.message || "Failed to create account. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

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
          <h2 className="text-center text-4xl font-bold text-white mb-6">Sign Up</h2>
          
          {registrationSuccess ? (
            <div className="text-center">
              <div className="bg-green-100 bg-opacity-20 rounded-lg p-4 mb-6">
                <i className="fas fa-envelope-open-text text-4xl text-green-400 mb-3"></i>
                <h3 className="text-white text-xl font-semibold mb-2">Registration Successful!</h3>
                <p className="text-white mt-2">
                  We've sent a verification email to <strong>{email}</strong>
                </p>
                <p className="text-white mt-2">
                  Please check your inbox and click the verification link to activate your account.
                </p>
                <div className="mt-4 text-sm text-gray-300">
                  <p>Don't forget to check your spam folder if you can't find the email.</p>
                </div>
              </div>
              <p className="text-white mb-4">You'll be redirected to the login page shortly.</p>
              <Link to="/login">
                <button className="w-full bg-[#1e88e5] text-white py-4 rounded-full hover:bg-[#1565c0] transition-colors">
                  Go to Login
                </button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label htmlFor="name" className="block text-white mb-2">Full Name</label>
                <div className="flex items-center bg-white rounded-full overflow-hidden">
                  <div className="flex items-center justify-center w-10 h-10 ml-2">
                    <i className="fas fa-user text-gray-600"></i>
                  </div>
                  <input 
                    type="text" 
                    id="name" 
                    className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                    placeholder="Enter your full name" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required 
                  />
                </div>
              </div>

              <div className="mb-4">
                <label htmlFor="email" className="block text-white mb-2">Email</label>
                <div className="flex items-center bg-white rounded-full overflow-hidden">
                  <div className="flex items-center justify-center w-10 h-10 ml-2">
                    <i className="fas fa-envelope text-gray-600"></i>
                  </div>
                  <input 
                    type="email" 
                    id="email" 
                    className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                    placeholder="Enter your email" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required 
                  />
                </div>
              </div>

              <div className="mb-4">
                <label htmlFor="country" className="block text-white mb-2">Country</label>
                <div className="flex items-center bg-white rounded-full overflow-hidden">
                  <div className="flex items-center justify-center w-10 h-10 ml-2">
                    <i className="fas fa-globe text-gray-600"></i>
                  </div>
                  <select 
                    id="country" 
                    className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                    value={countryCode}
                    onChange={(e) => setCountryCode(e.target.value)}
                    required
                  >
                    <option value="">Select your country</option>
                    {countries.map((country) => (
                      <option key={country.code} value={country.code}>
                        {country.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label htmlFor="phone" className="block text-white mb-2">Phone Number</label>
                <div className="flex items-center bg-white rounded-full overflow-hidden">
                  <div className="flex items-center justify-center w-10 h-10 ml-2">
                    <i className="fas fa-phone text-gray-600"></i>
                  </div>
                  <input 
                    type="tel" 
                    id="phone" 
                    className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                    placeholder="Enter your phone number" 
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required 
                  />
                </div>
              </div>
              
              <div className="mb-4">
                <label htmlFor="password" className="block text-white mb-2">Password</label>
                <div className="flex items-center bg-white rounded-full overflow-hidden">
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
              </div>

              <div className="mb-4">
                <label htmlFor="confirmPassword" className="block text-white mb-2">Confirm Password</label>
                <div className="flex items-center bg-white rounded-full overflow-hidden">
                  <div className="flex items-center justify-center w-10 h-10 ml-2">
                    <i className="fas fa-lock text-gray-600"></i>
                  </div>
                  <input 
                    type={showPassword ? "text" : "password"} 
                    id="confirmPassword" 
                    className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                    placeholder="Confirm your password" 
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required 
                  />
                </div>
              </div>

              {/* Los campos de compañía han sido removidos ya que solo nos enfocamos en el registro de usuario general */}

              {/* Display error message */}
              {errorMessage && (
                <div className="mb-4 text-red-500 text-sm text-center bg-red-100 bg-opacity-20 rounded p-2">
                  {errorMessage}
                </div>
              )}

              {/* Terms and Conditions Checkbox */}
              <div className="mb-6">
                <label className="flex items-center text-white text-sm">
                  <input
                    type="checkbox"
                    checked={acceptedTerms}
                    onChange={(e) => setAcceptedTerms(e.target.checked)}
                    className="mr-2"
                  />
                  I accept the <Link to="/terms" className="text-[#1e88e5] hover:text-[#1565c0] transition-colors ml-1">Terms and Conditions</Link>
                </label>
              </div>
              
              <button 
                type="submit" 
                className="w-full bg-[#1e88e5] text-white py-4 rounded-full mb-6 hover:bg-[#1565c0] transition-colors"
                disabled={isLoading || !acceptedTerms}
              >
                {isLoading ? "Creating Account..." : "Create Account"}
              </button>
              
              <div className="flex items-center justify-center mb-6">
                <hr className="border-gray-300 flex-grow" />
                <span className="mx-2 text-white">or</span>
                <hr className="border-gray-300 flex-grow" />
              </div>
              
              <p className="text-center text-sm text-white">
                Already have an account? <Link to="/login" className="text-[#1e88e5] hover:text-[#1565c0] transition-colors">Login</Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
