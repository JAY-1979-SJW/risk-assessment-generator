import React, { useState } from 'react'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import KoshaDashboard from './pages/KoshaDashboard'

export default function App() {
  const [pid, setPid] = useState(null)
  const [page, setPage] = useState('projects')

  if (page === 'kosha') return <KoshaDashboard onBack={() => setPage('projects')} />
  if (pid) return <ProjectDetail pid={pid} onBack={() => setPid(null)} />
  return <ProjectList onSelect={setPid} onMonitor={() => setPage('kosha')} />
}
