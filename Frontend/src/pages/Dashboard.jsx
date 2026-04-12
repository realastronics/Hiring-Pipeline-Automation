import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import toast from 'react-hot-toast'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Dashboard({ user }) {
  const [jobTitle, setJobTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [jobId, setJobId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [jobs, setJobs] = useState([])
  const [companyId, setCompanyId] = useState(null)
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  async function fetchJobs(cId) {
    try {
      const res = await axios.get(`${API}/jobs/company/${cId}`)
      const jobsWithStats = await Promise.all(
        res.data.map(async job => {
          const stats = await axios.get(`${API}/jobs/${job.id}/stats`)
          return { ...job, stats: stats.data }
        })
      )
      setJobs(jobsWithStats)
    } catch (e) {
      console.error(e)
    }
  }

useEffect(() => {
  const init = async () => {
    const stored = localStorage.getItem('company_id')
    if (!stored) return

    try {
      await fetchJobs(stored)
      setCompanyId(stored) // now safe (after async boundary)
    } catch (e) {
      console.error(e)
    }
  }

  init()
}, [])

  async function createJob() {
    if (!jobTitle) return
    setLoading(true)
    try {
      let cId = companyId

      if (!cId) {
        if (!companyName) {
          toast.error('Enter company name for your first job')
          setLoading(false)
          return
        }
        const company = await axios.post(`${API}/jobs/company`, { name: companyName })
        cId = company.data.id
        setCompanyId(cId)
        localStorage.setItem('company_id', cId)
      }

      const job = await axios.post(`${API}/jobs/`, {
        company_id: cId,
        title: jobTitle
      })

      setJobId(job.data.id)
      setJobTitle('')
      setCreating(false)
      fetchJobs(cId)
    } catch (e) {
      toast.error('Error: ' + e.message)

    }
    setLoading(false)
  }

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: '0 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, marginBottom: 4 }}>Active Roles</h1>
          <p style={{ color: '#888', fontSize: 14 }}>{user}</p>
        </div>
        <button style={primaryBtn} onClick={() => setCreating(!creating)}>
          {creating ? 'Cancel' : '+ New Role'}
        </button>
      </div>

      {/* Create job form */}
      {creating && (
        <div style={cardStyle}>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 20 }}>Create new role</h2>
          {!companyId && (
            <>
              <label style={labelStyle}>Company name</label>
              <input style={inputStyle} placeholder="e.g. Acme Corp"
                value={companyName} onChange={e => setCompanyName(e.target.value)} />
            </>
          )}
          <label style={labelStyle}>Job title</label>
          <input style={inputStyle} placeholder="e.g. Backend Engineer Intern"
            value={jobTitle} onChange={e => setJobTitle(e.target.value)} />
          <button style={primaryBtn} onClick={createJob} disabled={loading}>
            {loading ? 'Creating...' : 'Create Role'}
          </button>
        </div>
      )}

      {/* Success state */}
      {jobId && (
        <div style={{ ...cardStyle, background: '#f0fdf4', border: '1px solid #bbf7d0', marginBottom: 16 }}>
          <p style={{ color: '#16a34a', fontWeight: 600, marginBottom: 12 }}>✓ Role created</p>
          <button style={primaryBtn} onClick={() => navigate(`/screen/${jobId}`)}>
            Start Screening →
          </button>
        </div>
      )}

      {/* Jobs list */}
      {jobs.length === 0 && !creating && (
        <div style={{ ...cardStyle, textAlign: 'center', padding: 48 }}>
          <p style={{ color: '#888', marginBottom: 16 }}>No active roles yet</p>
          <button style={primaryBtn} onClick={() => setCreating(true)}>Create your first role</button>
        </div>
      )}

      {jobs.map(job => (
        <JobCard key={job.id} job={job} navigate={navigate} />
      ))}
    </div>
  )
}

function JobCard({ job, navigate }) {
  const s = job.stats || {}
  const stages = [
    { label: 'Screened', value: s.total || 0, color: '#1a1a1a' },
    { label: 'Strong', value: s.strong || 0, color: '#16a34a' },
    { label: 'Moderate', value: s.moderate || 0, color: '#ca8a04' },
    { label: 'Invited', value: s.invited || 0, color: '#2563eb' },
    { label: 'Scheduled', value: s.scheduled || 0, color: '#7c3aed' }
  ]

  return (
    <div style={{ ...cardStyle, marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>{job.title}</h3>
          <span style={{ fontSize: 12, color: '#888' }}>
            Created {new Date(job.created_at).toLocaleDateString()}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={secondaryBtn} onClick={() => navigate(`/screen/${job.id}`)}>
            Screen
          </button>
          <button style={secondaryBtn} onClick={() => navigate(`/candidates/${job.id}`)}>
            Outreach
          </button>
          <button style={secondaryBtn} onClick={() => navigate(`/schedule/${job.id}`)}>
            Schedule
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        {stages.map(stage => (
          <div key={stage.label} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 700, color: stage.color }}>{stage.value}</div>
            <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{stage.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

const cardStyle = { background: '#fff', borderRadius: 12, padding: 24, border: '1px solid #e8e8e8', marginBottom: 20 }
const labelStyle = { display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 6, color: '#444' }
const inputStyle = { width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid #ddd', fontSize: 15, marginBottom: 16, outline: 'none', fontFamily: 'inherit' }
const primaryBtn = { padding: '10px 20px', borderRadius: 8, background: '#2563eb', color: '#fff', border: 'none', fontSize: 14, fontWeight: 600, cursor: 'pointer' }
const secondaryBtn = { padding: '8px 14px', borderRadius: 8, background: '#f5f5f5', color: '#1a1a1a', border: '1px solid #e8e8e8', fontSize: 13, fontWeight: 500, cursor: 'pointer' }