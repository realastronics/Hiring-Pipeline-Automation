import { useNavigate } from 'react-router-dom'

export default function Navbar({ user, logout }) {
  const navigate = useNavigate()

  return (
    <div style={{
      height: 52,
      background: '#fff',
      borderBottom: '1px solid #e8e8e8',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <span
        onClick={() => navigate('/')}
        style={{ fontWeight: 700, fontSize: 15, cursor: 'pointer' }}>
        Hiring Pipeline
      </span>

      {user && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 13, color: '#888' }}>{user}</span>
          <button
            onClick={logout}
            style={{
              padding: '6px 14px', borderRadius: 6,
              background: '#f5f5f5', border: '1px solid #ddd',
              fontSize: 13, fontWeight: 500, cursor: 'pointer'
            }}>
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}