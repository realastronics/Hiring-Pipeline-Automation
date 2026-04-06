import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Screening from './pages/Screening'
import Candidates from './pages/Candidates'
import Schedule from './pages/Schedule'

function App() {
  const [user, setUser] = useState(() => {
    // Read immediately on first render before router processes URL
    const params = new URLSearchParams(window.location.search)
    const emailFromCallback = params.get('user')
    if (emailFromCallback) {
      localStorage.setItem('user_email', emailFromCallback)
      // Clean URL immediately
      window.history.replaceState({}, '', window.location.pathname)
      return emailFromCallback
    }
    return localStorage.getItem('user_email')
  })

  function logout() {
    localStorage.removeItem('user_email')
    setUser(null)
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={user ? <Dashboard user={user} logout={logout} /> : <Navigate to="/login" />} />
        <Route path="/dashboard" element={user ? <Dashboard user={user} logout={logout} /> : <Navigate to="/login" />} />
        <Route path="/screen/:jobId" element={user ? <Screening user={user} /> : <Navigate to="/login" />} />
        <Route path="/candidates/:jobId" element={user ? <Candidates user={user} /> : <Navigate to="/login" />} />
        <Route path="/schedule/:jobId" element={user ? <Schedule user={user} /> : <Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App