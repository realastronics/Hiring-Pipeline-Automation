import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API = 'http://localhost:8000'

// eslint-disable-next-line no-unused-vars
export default function Dashboard({ user, logout }) {
  console.log('Dashboard user:', user)
  const [jobTitle, setJobTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [jobId, setJobId] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  

  async function createJob() {
    if (!jobTitle || !companyName) return
    setLoading(true)
    try {
      // First create company
      const company = await axios.post(`${API}/jobs/company`, { name: companyName })
      // Then create job
      const job = await axios.post(`${API}/jobs/`, {
        company_id: company.data.id,
        title: jobTitle
      })
      setJobId(job.data.id)
    } catch (e) {
      alert('Error creating job: ' + e.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ maxWidth: 600, margin: '60px auto', padding: '0 24px' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
        Hiring Pipeline
      </h1>
      <p style={{ color: '#666', marginBottom: 40 }}>
        AI-powered resume screening and interview scheduling
      </p>

      <div style={{ background: '#fff', borderRadius: 12, padding: 32, border: '1px solid #e8e8e8' }}>
        <h2 style={{ fontSize: 18, marginBottom: 24 }}>Create a new role</h2>

        <label style={labelStyle}>Company name</label>
        <input
          style={inputStyle}
          placeholder="e.g. Acme Corp"
          value={companyName}
          onChange={e => setCompanyName(e.target.value)}
        />

        <label style={labelStyle}>Job title</label>
        <input
          style={inputStyle}
          placeholder="e.g. Backend Engineer Intern"
          value={jobTitle}
          onChange={e => setJobTitle(e.target.value)}
        />

        {!jobId ? (
          <button style={btnStyle} onClick={createJob} disabled={loading}>
            {loading ? 'Creating...' : 'Create Role'}
          </button>
        ) : (
          <div>
            <p style={{ color: '#16a34a', marginBottom: 16, fontWeight: 500 }}>
              ✓ Role created
            </p>
            <button style={btnStyle} onClick={() => navigate(`/screen/${jobId}`)}>
              Start Screening →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const labelStyle = {
  display: 'block', fontSize: 14, fontWeight: 500,
  marginBottom: 6, color: '#444'
}
const inputStyle = {
  width: '100%', padding: '10px 14px', borderRadius: 8,
  border: '1px solid #ddd', fontSize: 15, marginBottom: 20,
  outline: 'none'
}
const btnStyle = {
  width: '100%', padding: '12px', borderRadius: 8,
  background: '#1a1a1a', color: '#fff', border: 'none',
  fontSize: 15, fontWeight: 600
}