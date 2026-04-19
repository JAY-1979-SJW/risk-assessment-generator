import React, { useEffect, useState } from 'react'

const API = '/api/internal'

// INTERNAL_API_KEY를 URL 쿼리로 전달하거나, 로컬스토리지에 저장해 헤더로 전송
// 키가 없으면 빈 문자열 → 서버에서 INTERNAL_API_KEY 미설정 시 통과
function getStoredKey() {
  try { return localStorage.getItem('kras_internal_key') || '' } catch { return '' }
}
function setStoredKey(k) {
  try { localStorage.setItem('kras_internal_key', k) } catch {}
}
function apiFetch(url, key) {
  const headers = key ? { 'X-Internal-Key': key } : {}
  return fetch(url, { headers })
}

const S = {
  page: { display: 'flex', minHeight: '100vh', fontFamily: 'Pretendard, -apple-system, sans-serif', background: '#f8fafc', color: '#1e293b' },
  sidebar: { width: 260, minWidth: 220, background: '#fff', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', padding: '1.25rem 0' },
  sideTitle: { fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#94a3b8', padding: '0 1rem 0.5rem' },
  fileItem: (active) => ({
    padding: '0.45rem 1rem', cursor: 'pointer', fontSize: '0.8rem',
    background: active ? '#eff6ff' : 'transparent',
    color: active ? '#2563eb' : '#475569',
    borderLeft: active ? '3px solid #2563eb' : '3px solid transparent',
    wordBreak: 'break-all', lineHeight: 1.4,
  }),
  main: { flex: 1, padding: '2rem 2.5rem', overflowY: 'auto' },
  header: { marginBottom: '1.5rem', paddingBottom: '1rem', borderBottom: '1px solid #e2e8f0' },
  h1: { fontSize: '1.1rem', fontWeight: 700, margin: 0 },
  sub: { fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' },
  mdWrap: { maxWidth: 720, lineHeight: 1.75, fontSize: '0.9rem' },
  empty: { color: '#94a3b8', marginTop: '3rem', textAlign: 'center' },
  badge: { display: 'inline-block', fontSize: '0.7rem', background: '#f1f5f9', color: '#64748b', borderRadius: 4, padding: '0.1rem 0.4rem', marginLeft: '0.4rem' },
  changeItem: { background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.75rem 1rem', marginBottom: '0.6rem' },
  changeTs: { fontSize: '0.72rem', color: '#94a3b8' },
  changeSummary: { fontSize: '0.85rem', marginTop: '0.2rem' },
  changeFiles: { fontSize: '0.72rem', color: '#64748b', marginTop: '0.25rem' },
  tabBar: { display: 'flex', gap: 8, marginBottom: '1.25rem' },
  tab: (active) => ({
    padding: '0.35rem 0.85rem', borderRadius: 6, fontSize: '0.8rem', cursor: 'pointer', border: 'none',
    background: active ? '#2563eb' : '#f1f5f9', color: active ? '#fff' : '#475569', fontWeight: active ? 600 : 400,
  }),
}

function renderMd(md) {
  if (!md) return ''
  return md
    .replace(/^### (.+)$/gm, '<h3 style="margin:1.2em 0 0.4em;font-size:0.95rem;color:#1e293b">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="margin:1.5em 0 0.5em;font-size:1.05rem;border-bottom:1px solid #e2e8f0;padding-bottom:0.3em">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="margin:0 0 1em;font-size:1.2rem;font-weight:700">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code style="background:#f1f5f9;padding:0.1em 0.35em;border-radius:3px;font-size:0.85em">$1</code>')
    .replace(/^- (.+)$/gm, '<li style="margin:0.2em 0">$1</li>')
    .replace(/(<li.*<\/li>\n?)+/g, s => `<ul style="padding-left:1.4em;margin:0.4em 0">${s}</ul>`)
    .replace(/\n\n/g, '<br/><br/>')
}

export default function DevlogPage() {
  const [tab, setTab] = useState('devlog')
  const [files, setFiles] = useState([])
  const [selected, setSelected] = useState(null)
  const [content, setContent] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiKey, setApiKey] = useState(getStoredKey)
  const [keyInput, setKeyInput] = useState('')
  const [authError, setAuthError] = useState(false)

  function loadDevlogList(key) {
    apiFetch(`${API}/devlog`, key)
      .then(r => { if (r.status === 401) { setAuthError(true); return null } setAuthError(false); return r.json() })
      .then(d => { if (!d) return; setFiles(d.files || []); if (d.files?.length) selectFile(d.files[0].filename, key) })
      .catch(() => setError('devlog 목록을 불러오지 못했습니다.'))
  }

  useEffect(() => { loadDevlogList(apiKey) }, [])

  useEffect(() => {
    if (tab !== 'history') return
    apiFetch(`${API}/change-history?n=50`, apiKey)
      .then(r => { if (r.status === 401) { setAuthError(true); return null } return r.json() })
      .then(d => { if (!d) return; setHistory(d.items || []) })
      .catch(() => setError('변경 이력을 불러오지 못했습니다.'))
  }, [tab])

  function handleKeySubmit(e) {
    e.preventDefault()
    const k = keyInput.trim()
    setApiKey(k)
    setStoredKey(k)
    setAuthError(false)
    setError('')
    loadDevlogList(k)
    setKeyInput('')
  }

  function selectFile(filename, key) {
    const k = key !== undefined ? key : apiKey
    setSelected(filename)
    setLoading(true)
    setContent('')
    apiFetch(`${API}/devlog/${filename}`, k)
      .then(r => { if (r.status === 401) { setAuthError(true); return null } return r.json() })
      .then(d => { if (!d) return; setContent(d.content || '') })
      .catch(() => setContent('파일을 불러오지 못했습니다.'))
      .finally(() => setLoading(false))
  }

  return (
    <div style={S.page}>
      {/* 사이드바 */}
      <aside style={S.sidebar}>
        <div style={S.sideTitle}>개발 로그</div>
        {files.length === 0 && <div style={{ padding: '0.5rem 1rem', fontSize: '0.78rem', color: '#94a3b8' }}>파일 없음</div>}
        {files.map(f => (
          <div key={f.filename} style={S.fileItem(selected === f.filename)} onClick={() => { setTab('devlog'); selectFile(f.filename) }}>
            {f.filename.replace('.md', '')}
          </div>
        ))}
      </aside>

      {/* 본문 */}
      <main style={S.main}>
        <div style={S.header}>
          <div style={S.h1}>개발 로그 <span style={S.badge}>내부 전용</span></div>
          <div style={S.sub}>앱 메뉴와 연결되지 않은 독립 페이지 · URL 직접 접근 전용</div>
        </div>

        <div style={S.tabBar}>
          <button style={S.tab(tab === 'devlog')} onClick={() => setTab('devlog')}>작업 로그</button>
          <button style={S.tab(tab === 'history')} onClick={() => setTab('history')}>변경 이력</button>
        </div>

        {authError && (
          <form onSubmit={handleKeySubmit} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: '1rem', background: '#fef9c3', border: '1px solid #fde047', borderRadius: 8, padding: '0.75rem 1rem' }}>
            <span style={{ fontSize: '0.82rem', color: '#92400e' }}>🔒 인증 키가 필요합니다.</span>
            <input
              type="password" value={keyInput} onChange={e => setKeyInput(e.target.value)}
              placeholder="X-Internal-Key 입력"
              style={{ flex: 1, padding: '0.35rem 0.6rem', border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.82rem' }}
              autoFocus
            />
            <button type="submit" style={{ padding: '0.35rem 0.8rem', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 5, fontSize: '0.82rem', cursor: 'pointer' }}>
              확인
            </button>
          </form>
        )}

        {error && <div style={{ color: '#dc2626', marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</div>}

        {tab === 'devlog' && (
          <div style={S.mdWrap}>
            {loading && <div style={{ color: '#94a3b8' }}>불러오는 중...</div>}
            {!loading && !content && <div style={S.empty}>왼쪽에서 파일을 선택하세요.</div>}
            {!loading && content && (
              <div dangerouslySetInnerHTML={{ __html: renderMd(content) }} />
            )}
          </div>
        )}

        {tab === 'history' && (
          <div style={{ maxWidth: 720 }}>
            {history.length === 0 && <div style={S.empty}>변경 이력이 없습니다.</div>}
            {history.map((item, i) => (
              <div key={i} style={S.changeItem}>
                <div style={S.changeTs}>{item.timestamp}</div>
                <div style={S.changeSummary}><strong>{item.task_name}</strong></div>
                <div style={{ fontSize: '0.8rem', color: '#475569', marginTop: '0.2rem' }}>{item.summary}</div>
                {item.changed_files?.length > 0 && (
                  <div style={S.changeFiles}>수정 파일: {item.changed_files.join(' · ')}</div>
                )}
                {item.result && <div style={{ ...S.changeFiles, marginTop: '0.15rem' }}>결과: {item.result}</div>}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
