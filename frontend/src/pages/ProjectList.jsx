import React, { useEffect, useState } from 'react'
import { api } from '../api/client'
import Layout, { Card, Btn } from '../components/Layout'

export default function ProjectList({ onSelect, onMonitor }) {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { load() }, [])

  function load() {
    setLoading(true)
    api.getProjects()
      .then(d => setProjects(d.projects || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  async function create() {
    if (!newTitle.trim()) return
    try {
      const d = await api.createProject(newTitle.trim())
      setNewTitle('')
      setCreating(false)
      onSelect(d.id)
    } catch (e) { setError(e.message) }
  }

  async function del(id, title) {
    if (!confirm(`"${title}" 프로젝트를 삭제하시겠습니까?`)) return
    await api.deleteProject(id)
    load()
  }

  const statusLabel = { draft: '작성중', active: '진행중', completed: '완료' }
  const statusColor = { draft: '#64748b', active: '#2563eb', completed: '#16a34a' }

  return (
    <Layout title="프로젝트 목록">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>위험성평가 프로젝트</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <Btn onClick={onMonitor} color="gray">DB 모니터링</Btn>
          <Btn onClick={() => setCreating(true)} color="blue">+ 새 프로젝트</Btn>
        </div>
      </div>

      {error && <div style={{ color: '#dc2626', marginBottom: 8, fontSize: '0.85rem' }}>{error}</div>}

      {creating && (
        <Card>
          <div style={{ display: 'flex', gap: 8 }}>
            <input value={newTitle} onChange={e => setNewTitle(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && create()}
              placeholder="프로젝트명 입력 (예: 2026년 소방시설공사 위험성평가)"
              autoFocus
              style={{ flex: 1, padding: '0.4rem 0.6rem', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: '0.875rem' }} />
            <Btn onClick={create} color="green">생성</Btn>
            <Btn onClick={() => setCreating(false)} color="gray">취소</Btn>
          </div>
        </Card>
      )}

      {loading && <div style={{ color: '#94a3b8', padding: '2rem', textAlign: 'center' }}>불러오는 중...</div>}

      {!loading && projects.length === 0 && (
        <Card>
          <div style={{ textAlign: 'center', color: '#94a3b8', padding: '2rem' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📋</div>
            <div>아직 프로젝트가 없습니다.</div>
            <div style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>위의 "+ 새 프로젝트"를 눌러 시작하세요.</div>
          </div>
        </Card>
      )}

      {projects.map(p => (
        <Card key={p.id} style={{ cursor: 'pointer' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ flex: 1 }} onClick={() => onSelect(p.id)}>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{p.title}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 2 }}>
                수정일: {new Date(p.updated_at).toLocaleString('ko-KR')}
              </div>
            </div>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: statusColor[p.status] }}>
              {statusLabel[p.status] || p.status}
            </span>
            <Btn small color="gray" onClick={() => onSelect(p.id)}>열기</Btn>
            <Btn small color="red" onClick={() => del(p.id, p.title)}>삭제</Btn>
          </div>
        </Card>
      ))}
    </Layout>
  )
}
