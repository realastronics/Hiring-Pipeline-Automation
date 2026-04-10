import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Screening() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [mode, setMode] = useState('upload')
  const [jdText, setJdText] = useState('')
  const [resumes, setResumes] = useState([])
  const [sheetId, setSheetId] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)

  async function runScreening() {
    if (!jdText) return
    if (mode === 'upload' && resumes.length === 0) return
    setLoading(true)
    try {
      const form = new FormData()
      form.append('job_id', jobId)
      form.append('jd_text', jdText)

      let res
      if (mode === 'upload') {
        resumes.forEach(f => form.append('resumes', f))
        res = await axios.post(`${API}/screen/`, form)
      } else {
        form.append('sheet_id', sheetId)
        res = await axios.post(`${API}/screen/from-sheet`, form)
      }
      setResults(res.data)
    } catch (e) {
      alert('Screening failed: ' + e.message)
    }
    setLoading(false)
  }

  async function clearAndRescreen() {
    if (!confirm('This will delete all screening results for this job. Continue?')) return
    try {
        await axios.delete(`${API}/jobs/${jobId}/clear`)
        setResults(null)
    } catch (e) {
        alert('Failed to clear: ' + e.message)
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: '40px auto', padding: '0 24px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>Screen Resumes</h1>
      <p style={{ color: '#888', marginBottom: 32 }}>Job ID: {jobId}</p>

      {!results ? (
        <div style={{ background: '#fff', borderRadius: 12, padding: 32, border: '1px solid #e8e8e8' }}>

          {/* Mode toggle */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
            <button
              style={mode === 'upload' ? primaryBtn : secondaryBtn}
              onClick={() => setMode('upload')}>
              Manual Upload
            </button>
            <button
              style={mode === 'sheet' ? primaryBtn : secondaryBtn}
              onClick={() => setMode('sheet')}>
              From Google Form
            </button>
          </div>

          {/* JD input — always shown */}
          <label style={labelStyle}>Job Description</label>
          <textarea
            style={{ ...inputStyle, height: 160, resize: 'vertical' }}
            placeholder="Paste the full job description here..."
            value={jdText}
            onChange={e => setJdText(e.target.value)}
          />

          {/* Conditional input based on mode */}
          {mode === 'upload' ? (
            <div>
              <label style={labelStyle}>Upload Resumes (PDF)</label>
              <input
                type="file"
                multiple
                accept=".pdf"
                style={{ marginBottom: 24 }}
                onChange={e => setResumes(Array.from(e.target.files))}
              />
              {resumes.length > 0 && (
                <p style={{ color: '#666', fontSize: 14, marginBottom: 16 }}>
                  {resumes.length} file(s) selected
                </p>
              )}
            </div>
          ) : (
            <div>
              <label style={labelStyle}>Google Sheet ID</label>
              <input
                style={inputStyle}
                placeholder="Paste the Sheet ID from the URL"
                value={sheetId}
                onChange={e => setSheetId(e.target.value)}
              />
              <p style={{ fontSize: 13, color: '#888', marginBottom: 16 }}>
                Make sure the sheet has columns: Full Name, Email, Resume
              </p>
            </div>
          )}

          <button style={primaryBtn} onClick={runScreening} disabled={loading}>
            {loading ? 'Screening...' : '▶ Run AI Screening'}
          </button>
        </div>
      ) : (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginBottom: 24 }}>
            <StatCard label="Strong Fit" value={results.results.filter(r => r.recommendation === 'Strong Fit').length} color="#16a34a" />
            <StatCard label="Moderate Fit" value={results.results.filter(r => r.recommendation === 'Moderate Fit').length} color="#ca8a04" />
            <StatCard label="Not Fit" value={results.results.filter(r => r.recommendation === 'Not Fit').length} color="#dc2626" />
          </div>

          {results.results.map((r, i) => (
            <CandidateCard key={i} candidate={r} />
          ))}

          <button style={{ ...secondaryBtn, width: '100%', marginTop: 8 }} onClick={clearAndRescreen}>
            ↺ Clear & Re-screen
          </button> 

          <button style={{ ...primaryBtn, width: '100%', marginTop: 24 }}
            onClick={() => navigate(`/candidates/${jobId}`)}>
            Go to Outreach →
          </button>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: '#fff', borderRadius: 10, padding: '16px 20px', border: '1px solid #e8e8e8', textAlign: 'center' }}>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: 13, color: '#888', marginTop: 4 }}>{label}</div>
    </div>
  )
}

function CandidateCard({ candidate: c }) {
  const colors = { 'Strong Fit': '#16a34a', 'Moderate Fit': '#ca8a04', 'Not Fit': '#dc2626' }
  const bgColors = { 'Strong Fit': '#f0fdf4', 'Moderate Fit': '#fefce8', 'Not Fit': '#fef2f2' }
  return (
    <div style={{ background: '#fff', borderRadius: 12, padding: 20, border: '1px solid #e8e8e8', marginBottom: 12, borderLeft: `4px solid ${colors[c.recommendation]}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div>
          <div style={{ fontSize: 13, color: '#888' }}>Rank #{c.rank}</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>{c.candidate_name}</div>
        </div>
        <span style={{ background: bgColors[c.recommendation], color: colors[c.recommendation], padding: '4px 12px', borderRadius: 20, fontSize: 13, fontWeight: 600 }}>
          {c.recommendation}
        </span>
      </div>
      <div style={{ background: '#f5f5f5', borderRadius: 6, height: 6, marginBottom: 12 }}>
        <div style={{ width: `${c.score}%`, background: colors[c.recommendation], height: 6, borderRadius: 6 }} />
      </div>
      <div style={{ fontSize: 13, color: '#555', background: '#f9f9f9', borderRadius: 8, padding: '8px 12px' }}>
        {c.reasoning}
      </div>
    </div>
  )
}

const labelStyle = { display: 'block', fontSize: 14, fontWeight: 500, marginBottom: 6, color: '#444' }
const inputStyle = { width: '100%', padding: '10px 14px', borderRadius: 8, border: '1px solid #ddd', fontSize: 15, marginBottom: 20, outline: 'none', fontFamily: 'inherit' }
const primaryBtn = { padding: '11px 20px', borderRadius: 8, background: '#1a1a1a', color: '#fff', border: 'none', fontSize: 15, fontWeight: 600, cursor: 'pointer' }
const secondaryBtn = { padding: '11px 20px', borderRadius: 8, background: '#f5f5f5', color: '#1a1a1a', border: '1px solid #ddd', fontSize: 15, fontWeight: 600, cursor: 'pointer' }