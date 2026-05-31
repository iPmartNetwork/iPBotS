import { Routes, Route, Navigate } from 'react-router-dom'
import { useState } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Users from './pages/Users'
import Plans from './pages/Plans'
import Servers from './pages/Servers'
import Payments from './pages/Payments'
import Layout from './components/Layout'

function App() {
  const [apiKey, setApiKey] = useState<string>(
    localStorage.getItem('apiKey') || ''
  )

  if (!apiKey) {
    return <Login onLogin={(key) => {
      localStorage.setItem('apiKey', key)
      setApiKey(key)
    }} />
  }

  return (
    <Layout onLogout={() => {
      localStorage.removeItem('apiKey')
      setApiKey('')
    }}>
      <Routes>
        <Route path="/" element={<Dashboard apiKey={apiKey} />} />
        <Route path="/users" element={<Users apiKey={apiKey} />} />
        <Route path="/plans" element={<Plans apiKey={apiKey} />} />
        <Route path="/servers" element={<Servers apiKey={apiKey} />} />
        <Route path="/payments" element={<Payments apiKey={apiKey} />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  )
}

export default App
