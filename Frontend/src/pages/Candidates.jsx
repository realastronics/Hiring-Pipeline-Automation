import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'


const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Candidates({ user }) {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [formLink, setFormLink] = useState('')
  const [jobTitle, setJobTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    axios.get(`${API}/candidates/job/${jobId}`)
      .then(res => setData(res.data))
      .catch(e => console.error(e))
  }, [jobId])

  async function sendEmails(group) {
    if (!formLink || !jobTitle) {
      alert('Please enter the form link and job title first')
      return
    }
    setLoading(true)
    try {
      let targets = []
      if (group === 'strong') targets = data.strong
      if (group === 'both') targets = [...data.strong, ...data.moderate]

      await axios.post(`${API}/email/invite`, {
        targets: targets.map(c => ({
          application_id: c.application_id,
          name: c.name,
          email: c.email
        })),
        form_link: formLink,
        job_title: jobTitle,
        user_email: user
      })
      setMessage(`✓ Invites sent to ${targets.length} candidates`)
    } catch (e) {
      setMessage('Failed: ' + e.message)
    }
    setLoading(false)
  }

  async function sendRejections() {
    if (!jobTitle) { alert('Enter job title first'); return }
    setLoading(true)
    try {
      await axios.post(`${API}/email/reject`, {
        targets: data.not_fit.map(c => ({
          application_id: c.application_id,
          name: c.name,
          email: c.email
        })),
        job_title: jobTitle,
        user_email: user
      })
      setMessage(`✓ Rejections sent to ${data.not_fit.length} candidates`)
    } catch (e) {
      setMessage('Failed: ' + e.message)
    }
    setLoading(false)
  }

  if (!data) return <div style={{ padding: 40 }}>Loading candidates...</div>

  return (
    <div style={{ maxWidth: 700, margin: '40px auto', padding: '0 24px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 32 }}>Candidate Outreach</h1>

      <div style={{ background: '#fff', borderRadius: 12, padding: 24, border: '1px solid #e8e8e8', marginBottom: 24 }}>
        <label style={labelStyle}>Job title (for email)</label>
        <input style={inputStyle} placeholder="e.g. Backend Engineer Intern"
          value={jobTitle} onChange={e => setJobTitle(e.target.value)} />
        <label style={labelStyle}>Availability form link</label>
        <input style={inputStyle} placeholder="https://forms.gle/..."
          value={formLink} onChange={e => setFormLink(e.target.value)} />
      </div>

      <Section title="Strong Fit" candidates={data.strong} color="#16a34a" bg="#f0fdf4" />
      <Section title="Moderate Fit" candidates={data.moderate} color="#ca8a04" bg="#fefce8" />
      <Section title="Not Fit" candidates={data.not_fit} color="#dc2626" bg="#fef2f2" />

      {message && <p style={{ color: '#16a34a', fontWeight: 500, marginBottom: 16 }}>{message}</p>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginTop: 8 }}>
        <button style={btnStyle('#1a1a1a')} onClick={() => sendEmails('strong')} disabled={loading}>
          Invite Strong Only
        </button>
        <button style={btnStyle('#1a1a1a')} onClick={() => sendEmails('both')} disabled={loading}>
          Invite Strong + Moderate
        </button>
        <button style={btnStyle('#dc2626')} onClick={sendRejections} disabled={loading}>
          Send Rejections
        </button>
      </div>

      <button style={{ ...btnStyle('#059669'), marginTop: 12, width: '100%' }}
        onClick={() => navigate(`/schedule/${jobId}`)}>
        Go to Scheduling →
      </button>
    </div>
  )
}

function Section({ title, candidates, color, bg }) {
  if (!candidates?.length) return null
  return (
    <div style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 15, fontWeight: 600, color, marginBottom: 10 }}>
        {title} ({candidates.length})
      </h3>
      {candidates.map((c, i) => (
        <div key={i} style={{ background: bg, borderRadius: 8, padding: '10px 14px', marginBottom: 8, fontSize: 14 }}>
          <strong>{c.name}</strong> — {c.email}
          <span style={{ float: 'right', color: '#888' }}>Score: {c.score}</span>
        </div>
      ))}
    </div>
  )
}

const labelStyle = { display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 6, color: '#444' }
const inputStyle = { width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid #ddd', fontSize: 15, marginBottom: 16, outline: 'none', fontFamily: 'inherit' }
const btnStyle = bg => ({ padding: '11px 0', borderRadius: 8, background: bg, color: '#fff', border: 'none', fontSize: 14, fontWeight: 600, width: '100%' })