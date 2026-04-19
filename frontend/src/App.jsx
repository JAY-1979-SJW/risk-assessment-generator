import React, { useState } from 'react'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import KoshaDashboard from './pages/KoshaDashboard'
import KoshaMonitor from './pages/KoshaMonitor'

export default function App() {
  const [pid, setPid] = useState(null)
  const [page, setPage] = useState('projects')

  if (page === 'monitor') return (
    <KoshaMonitor
      onBack={() => setPage('projects')}
      onStats={() => setPage('kosha')}
    />
  )
  if (page === 'kosha') return (
    <KoshaDashboard
      onBack={() => setPage('projects')}
      onMonitor={() => setPage('monitor')}
    />
  )
  if (pid) return <ProjectDetail pid={pid} onBack={() => setPid(null)} />
  return <ProjectList onSelect={setPid} onMonitor={() => setPage('kosha')} />
}
