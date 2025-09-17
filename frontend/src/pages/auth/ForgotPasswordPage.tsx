import React, { useState, useEffect } from "react"
import { Link, useNavigate } from "react-router-dom"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [submitted, setSubmitted] = useState(false)
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // In a real app, you'd send a password reset email
    setSubmitted(true)
    setTimeout(() => {
      navigate("/login")
    }, 3000)
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
          <h2 className="text-center text-4xl font-bold text-white mb-6">Forgot Password</h2>
          
          {submitted ? (
            <div className="text-center">
              <div className="bg-[#1e88e5] bg-opacity-20 rounded-lg p-4 mb-6">
                <i className="fas fa-check-circle text-4xl text-[#1e88e5] mb-3"></i>
                <p className="text-white">Password reset link sent! Check your email.</p>
              </div>
              <p className="text-white mb-4">You'll be redirected to the login page shortly.</p>
              <Link to="/login">
                <button className="w-full bg-[#1e88e5] text-white py-4 rounded-full hover:bg-[#1565c0] transition-colors">
                  Return to Login
                </button>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label htmlFor="email" className="block text-white mb-2">Email Address</label>
                <div className="flex items-center bg-white rounded-full overflow-hidden">
                  <div className="flex items-center justify-center w-10 h-10 ml-2">
                    <i className="fas fa-envelope text-gray-600"></i>
                  </div>
                  <input 
                    type="email" 
                    id="email" 
                    className="flex-1 px-2 py-3 rounded-full focus:outline-none text-gray-800 bg-white" 
                    placeholder="Enter your email address" 
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required 
                  />
                </div>
                <p className="text-white text-sm mt-2">
                  We'll send you a link to reset your password.
                </p>
              </div>
              
              <button 
                type="submit" 
                className="w-full bg-[#1e88e5] text-white py-4 rounded-full mb-6 hover:bg-[#1565c0] transition-colors"
              >
                Reset Password
              </button>
              
              <p className="text-center text-sm text-white">
                <Link to="/login" className="text-[#1e88e5] hover:text-[#1565c0] transition-colors">
                  Back to Login
                </Link>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
