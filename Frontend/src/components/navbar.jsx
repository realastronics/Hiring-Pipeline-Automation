import { useNavigate, useLocation } from 'react-router-dom'

const BREADCRUMBS = {
  '/': 'Dashboard',
  '/dashboard': 'Dashboard',
  '/screen': 'Screen Resumes',
  '/candidates': 'Candidate Outreach',
  '/schedule': 'Schedule Interviews'
}

export default function Navbar({ user, logout }) {
  const navigate = useNavigate()
  const location = useLocation()

  const pathBase = '/' + location.pathname.split('/')[1]
  const currentPage = BREADCRUMBS[pathBase]
  const isOnDashboard = pathBase === '/' || pathBase === '/dashboard'

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
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          onClick={() => navigate('/')}
          style={{
            fontWeight: 700,
            fontSize: 15,
            cursor: 'pointer',
            color: '#1a1a1a'
          }}>
          Hiring Pipeline
        </span>

        {currentPage && !isOnDashboard && (
          <>
            <span style={{ color: '#ccc', fontSize: 16 }}>›</span>
            <span style={{ fontSize: 14, color: '#666' }}>
              {currentPage}
            </span>
          </>
        )}
      </div>

      {user && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 13, color: '#888' }}>{user}</span>
          <button
            onClick={logout}
            style={{
              padding: '6px 14px',
              borderRadius: 6,
              background: '#f5f5f5',
              border: '1px solid #e8e8e8',
              fontSize: 13,
              fontWeight: 500
            }}>
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}