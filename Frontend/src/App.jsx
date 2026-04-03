import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Screening from './pages/Screening'
import Candidates from './pages/Candidates'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/screen/:jobId" element={<Screening />} />
        <Route path="/candidates/:jobId" element={<Candidates />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App