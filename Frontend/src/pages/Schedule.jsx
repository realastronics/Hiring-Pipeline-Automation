import { useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Schedule({ user }) {
  const { jobId } = useParams()
  const [slots, setSlots] = useState([{ interviewer_name: '', interviewer_email: '', slot_datetime: '' }])
  const [schedule, setSchedule] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  async function addSlots() {
    setLoading(true)
    try {
      await axios.post(`${API}/schedule/slots`, { job_id: jobId, slots })
      setMessage('✓ Slots saved')
    } catch (e) {
      setMessage('Failed: ' + e.message)
    }
    setLoading(false)
  }

  async function matchAndBook() {
    setLoading(true)
    setMessage('')
    try {
      const res = await axios.post(`${API}/schedule/match`, {
        job_id: jobId,
        user_email: user
      })
      setSchedule(res.data)
      if (res.data.error) {
        setMessage(`Error: ${res.data.error}`)
      }
    } catch (e) {
      setMessage('Failed: ' + e.message)
    }
    setLoading(false)
  }

  function addSlotRow() {
    setSlots([...slots, { interviewer_name: '', interviewer_email: '', slot_datetime: '' }])
  }

  function updateSlot(index, field, value) {
    const updated = [...slots]
    updated[index][field] = value
    setSlots(updated)
  }

  return (
    <div style={{ maxWidth: 700, margin: '40px auto', padding: '0 24px' }}>
      <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Interview Scheduling</h1>
      <p style={{ color: '#888', marginBottom: 32 }}>Job ID: {jobId}</p>

      <div style={cardStyle}>
        <h2 style={{ fontSize: 17, fontWeight: 600, marginBottom: 20 }}>Interviewer Availability</h2>
        {slots.map((slot, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, marginBottom: 12 }}>
            <input style={inputStyle} placeholder="Interviewer name"
              value={slot.interviewer_name}
              onChange={e => updateSlot(i, 'interviewer_name', e.target.value)} />
            <input style={inputStyle} placeholder="interviewer@email.com"
              value={slot.interviewer_email}
              onChange={e => updateSlot(i, 'interviewer_email', e.target.value)} />
            <input style={inputStyle} type="datetime-local"
              value={slot.slot_datetime}
              onChange={e => updateSlot(i, 'slot_datetime', e.target.value)} />
          </div>
        ))}
        <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
          <button style={secondaryBtn} onClick={addSlotRow}>+ Add Row</button>
          <button style={primaryBtn} onClick={addSlots} disabled={loading}>Save Slots</button>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ fontSize: 17, fontWeight: 600, marginBottom: 8 }}>Auto-Match & Book</h2>
        <p style={{ color: '#888', fontSize: 14, marginBottom: 20 }}>
          Matches invited candidates to available slots and books Google Calendar events.
        </p>
        <button style={primaryBtn} onClick={matchAndBook} disabled={loading}>
          {loading ? 'Booking...' : '📅 Match & Book All'}
        </button>
      </div>

      {message && (
        <p style={{ color: message.startsWith('Error') ? '#dc2626' : '#16a34a', fontWeight: 500, marginBottom: 16 }}>
          {message}
        </p>
      )}

      {schedule && !schedule.error && (
        <div style={cardStyle}>
          <h2 style={{ fontSize: 17, fontWeight: 600, marginBottom: 16 }}>
            Booked ({schedule.booked?.length || 0})
          </h2>
          {schedule.booked?.map((b, i) => (
            <div key={i} style={{ padding: '12px 16px', background: '#f0fdf4', borderRadius: 8, marginBottom: 8 }}>
              <strong>{b.candidate}</strong> — {b.interviewer}
              <br />
              <span style={{ fontSize: 13, color: '#666' }}>
                {new Date(b.slot).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
              </span>
              {b.calendar_link && (
                <a href={b.calendar_link} target="_blank" rel="noreferrer"
                  style={{ float: 'right', fontSize: 13, color: '#16a34a' }}>
                  View Event →
                </a>
              )}
            </div>
          ))}
          {schedule.failed?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h3 style={{ fontSize: 15, color: '#dc2626', marginBottom: 8 }}>
                No slot found ({schedule.failed.length})
              </h3>
              {schedule.failed.map((name, i) => (
                <div key={i} style={{ padding: '8px 12px', background: '#fef2f2', borderRadius: 8, marginBottom: 6, fontSize: 14 }}>
                  {name}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const cardStyle = { background: '#fff', borderRadius: 12, padding: 24, border: '1px solid #e8e8e8', marginBottom: 20 }
const inputStyle = { width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #ddd', fontSize: 14, outline: 'none', fontFamily: 'inherit' }
const primaryBtn = { padding: '11px 20px', borderRadius: 8, background: '#1a1a1a', color: '#fff', border: 'none', fontSize: 14, fontWeight: 600, cursor: 'pointer' }
const secondaryBtn = { padding: '11px 20px', borderRadius: 8, background: '#f5f5f5', color: '#1a1a1a', border: '1px solid #ddd', fontSize: 14, fontWeight: 600, cursor: 'pointer' }