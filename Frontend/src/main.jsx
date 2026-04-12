import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.jsx'
import React from 'react'
import ReactDOM from 'react-dom/client'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
    <Toaster
      position="bottom-right"
      toastOptions={{
        duration: 4000,
        style: {
          fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
          fontSize: '14px',
          borderRadius: '8px',
          border: '1px solid #e8e8e8',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)'
        },
        success: {
          iconTheme: { primary: '#2563eb', secondary: '#fff' }
        }
      }}
    />
  </React.StrictMode>
)

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
