import React, { useEffect, useState, useCallback, useRef } from 'react'

const BASE = ''
const LOG_SOURCES = ['run_history', 'parser', 'pipeline']
const MAX_LINES = 2000

const LEVEL_COLOR = {
  ERROR:   '#ef4444',
  WARNING: '#f59e0b',
  INFO:    '#6b7280',
  DEBUG:   '#9ca3af',
}

function levelOf(line) {
  if (/\[ERROR\]/.test(line))   return 'ERROR'
  if (/\[WARNING\]/.test(line)) return 'WARNING'
  if (/완료|성공|PASS/.test(line))    return 'SUCCESS'
  return 'INFO'
}

function colorOf(level) {
  if (level === 'ERROR')   return '#ef4444'
  if (level === 'WARNING') return '#f59e0b'
  if (level === 'SUCCESS') return '#22c55e'
  return '#d1d5db'
}

function StatCard({ label, value, color = '#2563eb', sub }) {
  return (
    <div style={{
      background: '#1e293b', borderRadius: 8, padding: '14px 20px',
      borderLeft: `3px solid ${color}`, minWidth: 140,
    }}>
      <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color }}>{value ?? '-'}</div>
      {sub && <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function ProgressBar({ value, total, color = '#3b82f6' }) {
  const pct = total > 0 ? Math.round(value / total * 100) : 0
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
        <span>완료율</span>
        <span>{value?.toLocaleString()} / {total?.toLocaleString()} ({pct}%)</span>
      </div>
      <div style={{ height: 8, background: '#334155', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 4, transition: 'width .5s' }} />
      </div>
    </div>
  )
}

export default function KoshaMonitor({ onBack, onStats }) {
  const [stats, setStats]           = useState(null)
  const [lines, setLines]           = useState([])
  const [paused, setPaused]         = useState(false)
  const [errorOnly, setErrorOnly]   = useState(false)
  const [connected, setConnected]   = useState(false)
  const [lastTs, setLastTs]         = useState(null)
  const [srcFilter, setSrcFilter]   = useState('all')
  const [tailStarted, setTailStarted] = useState(false)

  const logRef      = useRef(null)
  const pausedRef   = useRef(false)
  const esRef       = useRef(null)
  const pendingRef  = useRef([])

  pausedRef.current = paused

  // ── 통계 조회 (30초 갱신) ───────────────────────────────────────────────────
  const loadStats = useCallback(async () => {
    try {
      const r = await fetch(BASE + '/admin/kosha/stats')
      if (r.ok) setStats(await r.json())
    } catch (_) {}
  }, [])

  useEffect(() => {
    loadStats()
    const t = setInterval(loadStats, 30000)
    return () => clearInterval(t)
  }, [loadStats])

  // ── SSE 연결 ────────────────────────────────────────────────────────────────
  const appendLines = useCallback((newLines) => {
    setLines(prev => {
      const merged = [...prev, ...newLines]
      return merged.length > MAX_LINES ? merged.slice(-MAX_LINES) : merged
    })
    const last = newLines.findLast(l => l.ts)
    if (last) setLastTs(last.ts)
  }, [])

  useEffect(() => {
    const url = `${BASE}/admin/kosha/stream?logs=${LOG_SOURCES.join(',')}&tail=150`
    const es = new EventSource(url)
    esRef.current = es

    es.onopen = () => setConnected(true)

    es.addEventListener('connected', () => setConnected(true))
    es.addEventListener('tail_start', () => setTailStarted(true))
    es.addEventListener('warn', (e) => {
      try {
        const d = JSON.parse(e.data)
        appendLines([{ src: 'system', line: '⚠ ' + d.msg, level: 'WARNING', ts: new Date().toLocaleTimeString() }])
      } catch (_) {}
    })

    es.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data)
        const level = levelOf(d.line)
        const ts = d.line.match(/\d{2}:\d{2}:\d{2}/)?.[0] ?? null
        const item = { src: d.src, line: d.line, level, ts }
        if (pausedRef.current) {
          pendingRef.current.push(item)
        } else {
          appendLines([item])
        }
      } catch (_) {}
    }

    es.onerror = () => setConnected(false)

    return () => es.close()
  }, [appendLines])

  // pause 해제 시 쌓인 라인 반영
  useEffect(() => {
    if (!paused && pendingRef.current.length > 0) {
      appendLines(pendingRef.current)
      pendingRef.current = []
    }
  }, [paused, appendLines])

  // ── auto scroll ─────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!paused && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [lines, paused])

  // ── 필터링 ──────────────────────────────────────────────────────────────────
  const filtered = lines.filter(l => {
    if (errorOnly && l.level !== 'ERROR' && l.level !== 'WARNING') return false
    if (srcFilter !== 'all' && l.src !== srcFilter) return false
    return true
  })

  // ── 통계 파싱 ───────────────────────────────────────────────────────────────
  const fileStats  = stats?.summary ?? {}
  const totalFiles = (fileStats.total_files ?? 0)
  const success    = stats?.by_file_status?.find(r => r.parse_status === 'success')?.count ?? 0
  const pending    = stats?.by_file_status?.find(r => r.parse_status === 'pending')?.count ?? 0
  const failed     = stats?.by_file_status?.filter(r => r.parse_status?.startsWith('fail'))
                           .reduce((a, r) => a + (r.count ?? 0), 0) ?? 0
  const unsupported = stats?.by_file_status?.find(r => r.parse_status === 'unsupported')?.count ?? 0

  // ── UI ──────────────────────────────────────────────────────────────────────
  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#e2e8f0', fontFamily: 'monospace' }}>

      {/* 헤더 */}
      <div style={{ background: '#1e293b', borderBottom: '1px solid #334155', padding: '12px 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: '1px solid #475569', color: '#94a3b8', borderRadius: 6, padding: '4px 12px', cursor: 'pointer', fontSize: 13 }}>← 뒤로</button>
        <span style={{ fontWeight: 700, fontSize: 16, color: '#e2e8f0' }}>KOSHA 파서 모니터</span>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 12, color: connected ? '#22c55e' : '#ef4444' }}>
            {connected ? '● 연결됨' : '○ 연결 끊김'}
          </span>
          {tailStarted && <span style={{ fontSize: 11, color: '#64748b' }}>실시간 수신 중</span>}
          <button onClick={loadStats} style={{ background: '#334155', border: 'none', color: '#94a3b8', borderRadius: 6, padding: '4px 10px', cursor: 'pointer', fontSize: 12 }}>↻ 통계 갱신</button>
          {onStats && <button onClick={onStats} style={{ background: '#1d4ed8', border: 'none', color: '#fff', borderRadius: 6, padding: '4px 12px', cursor: 'pointer', fontSize: 12 }}>📊 통계 대시보드</button>}
        </div>
      </div>

      <div style={{ padding: '20px 24px' }}>

        {/* 통계 카드 */}
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
          <StatCard label="파싱 성공" value={success.toLocaleString()} color="#22c55e" />
          <StatCard label="대기 중" value={pending.toLocaleString()} color="#3b82f6" />
          <StatCard label="실패" value={failed.toLocaleString()} color="#ef4444" />
          <StatCard label="미지원" value={unsupported.toLocaleString()} color="#f59e0b" />
          <StatCard label="청크 생성" value={(fileStats.total_chunks ?? 0).toLocaleString()} color="#a78bfa" />
          <StatCard label="마지막 로그" value={lastTs ?? '—'} color="#64748b" sub="HH:MM:SS" />
        </div>

        {/* 완료율 바 */}
        {totalFiles > 0 && (
          <div style={{ background: '#1e293b', borderRadius: 8, padding: '14px 20px', marginBottom: 16 }}>
            <ProgressBar value={success} total={success + pending + failed + unsupported} color="#22c55e" />
          </div>
        )}

        {/* 로그 컨트롤 */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, color: '#64748b' }}>소스:</span>
          {['all', ...LOG_SOURCES].map(s => (
            <button key={s} onClick={() => setSrcFilter(s)} style={{
              background: srcFilter === s ? '#334155' : 'none',
              border: '1px solid #334155', color: srcFilter === s ? '#e2e8f0' : '#64748b',
              borderRadius: 5, padding: '3px 10px', cursor: 'pointer', fontSize: 12,
            }}>{s}</button>
          ))}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button onClick={() => setErrorOnly(v => !v)} style={{
              background: errorOnly ? '#7f1d1d' : '#1e293b',
              border: `1px solid ${errorOnly ? '#ef4444' : '#334155'}`,
              color: errorOnly ? '#fca5a5' : '#94a3b8',
              borderRadius: 5, padding: '3px 10px', cursor: 'pointer', fontSize: 12,
            }}>ERROR 필터</button>
            <button onClick={() => setPaused(v => !v)} style={{
              background: paused ? '#1e3a5f' : '#1e293b',
              border: `1px solid ${paused ? '#3b82f6' : '#334155'}`,
              color: paused ? '#93c5fd' : '#94a3b8',
              borderRadius: 5, padding: '3px 10px', cursor: 'pointer', fontSize: 12,
            }}>{paused ? `▶ 재개 (${pendingRef.current.length})` : '⏸ 일시정지'}</button>
            <button onClick={() => { setLines([]); pendingRef.current = [] }} style={{
              background: '#1e293b', border: '1px solid #334155', color: '#94a3b8',
              borderRadius: 5, padding: '3px 10px', cursor: 'pointer', fontSize: 12,
            }}>🗑 지우기</button>
          </div>
        </div>

        {/* 로그 뷰어 */}
        <div ref={logRef} style={{
          background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8,
          height: 'calc(100vh - 380px)', overflowY: 'auto', padding: '12px 16px',
          fontSize: 12, lineHeight: 1.6,
        }}>
          {filtered.length === 0 && (
            <div style={{ color: '#334155', textAlign: 'center', marginTop: 40 }}>
              {connected ? '로그 수신 대기 중...' : '연결 중...'}
            </div>
          )}
          {filtered.map((item, i) => (
            <div key={i} style={{
              color: colorOf(item.level),
              borderBottom: item.level === 'ERROR' ? '1px solid #1f0a0a' : 'none',
              padding: item.level === 'ERROR' ? '2px 0' : '1px 0',
              background: item.level === 'ERROR' ? 'rgba(239,68,68,.05)' : 'transparent',
            }}>
              <span style={{ color: '#475569', marginRight: 8 }}>[{item.src}]</span>
              {item.line}
            </div>
          ))}
        </div>
        <div style={{ fontSize: 11, color: '#334155', marginTop: 6 }}>
          표시: {filtered.length} / 전체: {lines.length} 줄 (최대 {MAX_LINES})
          {paused && <span style={{ color: '#3b82f6', marginLeft: 12 }}>⏸ 일시정지 — {pendingRef.current.length}줄 대기 중</span>}
        </div>
      </div>
    </div>
  )
}
