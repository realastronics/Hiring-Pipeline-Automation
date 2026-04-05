import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Screening from './pages/Screening'
import Candidates from './pages/Candidates'
import Schedule from './pages/Schedule'

function App() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    // Check URL params for user after OAuth callback
    const params = new URLSearchParams(window.location.search)
    const emailFromCallback = params.get('user')
    if (emailFromCallback) {
      localStorage.setItem('user_email', emailFromCallback)
      setUser(emailFromCallback)
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname)
    } else {
      // Check localStorage
      const stored = localStorage.getItem('user_email')
      if (stored) setUser(stored)
    }
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={user ? <Dashboard user={user} /> : <Navigate to="/login" />} />
        <Route path="/dashboard" element={user ? <Dashboard user={user} /> : <Navigate to="/login" />} />
        <Route path="/screen/:jobId" element={user ? <Screening user={user} /> : <Navigate to="/login" />} />
        <Route path="/candidates/:jobId" element={user ? <Candidates user={user} /> : <Navigate to="/login" />} />
        <Route path="/schedule/:jobId" element={user ? <Schedule user={user} /> : <Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App