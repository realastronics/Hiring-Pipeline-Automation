import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Screening from './pages/Screening'
import Candidates from './pages/Candidates'
import Schedule from './pages/Schedule'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/screen/:jobId" element={<Screening />} />
        <Route path="/candidates/:jobId" element={<Candidates />} />
        <Route path="/schedule/:jobId" element={<Schedule />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App