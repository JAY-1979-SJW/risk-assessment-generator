import React, { useState } from 'react'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'

export default function App() {
  const [pid, setPid] = useState(null)

  return pid
    ? <ProjectDetail pid={pid} onBack={() => setPid(null)} />
    : <ProjectList onSelect={setPid} />
}
