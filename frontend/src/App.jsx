import React, { useEffect, useState } from 'react'

const STATUS_COLOR = { ok: '#16a34a', degraded: '#d97706', error: '#dc2626' }
const CONN_COLOR = { connected: '#16a34a', error: '#dc2626', not_configured: '#6b7280' }

export default function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [fetchedAt, setFetchedAt] = useState(null)

  const fetchHealth = () => {
    setLoading(true)
    fetch('/api/health')
      .then(r => r.json())
      .then(d => { setData(d); setFetchedAt(new Date()) })
      .catch(() => setData({ status: 'error', api: 'unreachable' }))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchHealth()
    const id = setInterval(fetchHealth, 30000)
    return () => clearInterval(id)
  }, [])

  const statusColor = data ? (STATUS_COLOR[data.status] ?? '#6b7280') : '#6b7280'

  return (
    <div style={{ fontFamily: 'Pretendard, -apple-system, sans-serif', background: '#f8fafc', minHeight: '100vh', padding: '2rem' }}>
      <div style={{ maxWidth: 640, margin: '0 auto' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1e293b', marginBottom: '0.25rem' }}>
          KRAS 시스템 상태
        </h1>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '1.5rem' }}>
          {fetchedAt ? `${fetchedAt.toLocaleTimeString('ko-KR')} 기준` : '조회 중...'}
          <button onClick={fetchHealth} style={{ marginLeft: '0.75rem', fontSize: '0.75rem', color: '#3b82f6', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
            새로고침
          </button>
        </p>

        {loading && !data && <p style={{ color: '#94a3b8' }}>불러오는 중...</p>}

        {data && (
          <>
            {/* 전체 상태 */}
            <Card>
              <Row label="전체 상태">
                <Badge color={statusColor}>{data.status === 'ok' ? '정상' : data.status === 'degraded' ? '일부 이상' : '오류'}</Badge>
              </Row>
              <Row label="API 서버">
                <Badge color={data.api === 'up' ? STATUS_COLOR.ok : STATUS_COLOR.error}>
                  {data.api === 'up' ? '구동 중' : '응답 없음'}
                </Badge>
              </Row>
              <Row label="데이터베이스" last>
                <Badge color={CONN_COLOR[data.db] ?? '#6b7280'}>
                  {data.db === 'connected' ? '연결됨' : data.db === 'error' ? '오류' : '미설정'}
                </Badge>
              </Row>
              {data.db_error && (
                <p style={{ fontSize: '0.75rem', color: '#dc2626', marginTop: '0.5rem', wordBreak: 'break-all' }}>{data.db_error}</p>
              )}
            </Card>

            {/* KOSHA 데이터 현황 */}
            {data.kosha && (
              <Card title="KOSHA 지식DB 수집 현황">
                <Row label="총 자료 수">
                  <Val>{data.kosha.materials?.toLocaleString()}건</Val>
                </Row>
                <Row label="파일 — 파싱 완료">
                  <Val color="#16a34a">{(data.kosha.files?.success ?? 0).toLocaleString()}건</Val>
                </Row>
                <Row label="파일 — 대기 중">
                  <Val color="#d97706">{(data.kosha.files?.pending ?? 0).toLocaleString()}건</Val>
                </Row>
                {data.kosha.files?.failed > 0 && (
                  <Row label="파일 — 실패">
                    <Val color="#dc2626">{data.kosha.files.failed.toLocaleString()}건</Val>
                  </Row>
                )}
                <Row label="텍스트 청크">
                  <Val>{data.kosha.chunks?.toLocaleString()}개</Val>
                </Row>
                <Row label="공종 분류 태그" last>
                  <Val>{data.kosha.tags?.toLocaleString()}개</Val>
                </Row>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function Card({ title, children }) {
  return (
    <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '1rem 1.25rem', marginBottom: '1rem' }}>
      {title && <p style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>{title}</p>}
      {children}
    </div>
  )
}

function Row({ label, children, last }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.4rem 0', borderBottom: last ? 'none' : '1px solid #f1f5f9' }}>
      <span style={{ fontSize: '0.875rem', color: '#475569' }}>{label}</span>
      {children}
    </div>
  )
}

function Badge({ color, children }) {
  return (
    <span style={{ fontSize: '0.8rem', fontWeight: 600, color, background: color + '18', padding: '0.2rem 0.6rem', borderRadius: 999 }}>
      {children}
    </span>
  )
}

function Val({ color, children }) {
  return <span style={{ fontSize: '0.875rem', fontWeight: 600, color: color ?? '#1e293b' }}>{children}</span>
}
