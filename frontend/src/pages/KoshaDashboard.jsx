import React, { useEffect, useState, useCallback } from 'react'

const BASE = ''

async function fetchStats() {
  const res = await fetch(BASE + '/admin/kosha/stats')
  if (!res.ok) throw new Error('통계 조회 실패')
  return res.json()
}

function StatCard({ label, value, color = '#2563eb' }) {
  return (
    <div style={{
      background: '#fff', borderRadius: 10, padding: '18px 24px',
      boxShadow: '0 1px 4px rgba(0,0,0,.1)', minWidth: 160,
      borderLeft: `4px solid ${color}`,
    }}>
      <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value?.toLocaleString() ?? '-'}</div>
    </div>
  )
}

function Table({ title, rows, columns }) {
  return (
    <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,.1)' }}>
      <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 12, color: '#1f2937' }}>{title}</div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr>
            {columns.map(c => (
              <th key={c.key} style={{
                textAlign: c.align || 'left', padding: '6px 10px',
                background: '#f3f4f6', color: '#374151', fontWeight: 600,
              }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
              {columns.map(c => (
                <td key={c.key} style={{ padding: '6px 10px', textAlign: c.align || 'left', color: '#374151' }}>
                  {c.render ? c.render(row[c.key], row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SchemaViewer({ schema }) {
  const [open, setOpen] = useState(null)
  return (
    <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,.1)' }}>
      <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 12, color: '#1f2937' }}>DB 스키마</div>
      {Object.entries(schema).map(([table, cols]) => (
        <div key={table} style={{ marginBottom: 8 }}>
          <button
            onClick={() => setOpen(open === table ? null : table)}
            style={{
              background: '#f3f4f6', border: 'none', borderRadius: 6, padding: '6px 14px',
              cursor: 'pointer', fontWeight: 600, fontSize: 13, color: '#374151', width: '100%', textAlign: 'left',
            }}
          >
            {open === table ? '▼' : '▶'} {table} ({cols.length}개 컬럼)
          </button>
          {open === table && (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12, marginTop: 4 }}>
              <thead>
                <tr>
                  <th style={{ padding: '4px 10px', background: '#f9fafb', textAlign: 'left' }}>컬럼</th>
                  <th style={{ padding: '4px 10px', background: '#f9fafb', textAlign: 'left' }}>타입</th>
                </tr>
              </thead>
              <tbody>
                {cols.map((c, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '4px 10px', color: '#111827', fontFamily: 'monospace' }}>{c.column}</td>
                    <td style={{ padding: '4px 10px', color: '#6b7280' }}>{c.type}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ))}
    </div>
  )
}

function parseStatusBadge(status) {
  const colors = { success: '#16a34a', pending: '#d97706', failed: '#dc2626', unsupported: '#6b7280' }
  return (
    <span style={{
      background: colors[status] || '#e5e7eb', color: '#fff',
      borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 600,
    }}>{status}</span>
  )
}

export default function KoshaDashboard({ onBack }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const d = await fetchStats()
      setData(d)
      setLastUpdated(new Date().toLocaleTimeString('ko-KR'))
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const t = setInterval(load, 30000)
    return () => clearInterval(t)
  }, [load])

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', padding: '24px 32px', fontFamily: 'system-ui, sans-serif' }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
        <button onClick={onBack} style={{
          background: '#e5e7eb', border: 'none', borderRadius: 6, padding: '6px 14px',
          cursor: 'pointer', fontSize: 13, color: '#374151',
        }}>← 돌아가기</button>
        <div>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#111827' }}>KOSHA 수집 DB 모니터링</h1>
          {lastUpdated && <div style={{ fontSize: 12, color: '#9ca3af', marginTop: 2 }}>마지막 갱신: {lastUpdated} (30초 자동 갱신)</div>}
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <button onClick={load} disabled={loading} style={{
            background: '#2563eb', color: '#fff', border: 'none', borderRadius: 6,
            padding: '7px 16px', cursor: loading ? 'not-allowed' : 'pointer', fontSize: 13,
          }}>{loading ? '갱신 중...' : '새로고침'}</button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8, padding: '12px 16px', color: '#dc2626', marginBottom: 20 }}>
          오류: {error}
        </div>
      )}

      {loading && !data && (
        <div style={{ textAlign: 'center', padding: 60, color: '#6b7280' }}>데이터 로딩 중...</div>
      )}

      {data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 요약 카드 */}
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <StatCard label="전체 자료 수" value={data.summary.materials} color="#2563eb" />
            <StatCard label="파일 수" value={data.summary.files} color="#7c3aed" />
            <StatCard label="청크 수" value={data.summary.chunks} color="#059669" />
            <StatCard label="태그 수" value={data.summary.tags} color="#d97706" />
          </div>

          {/* 파싱 진행률 */}
          {(() => {
            const parsed = data.by_file_status.find(r => r.parse_status === 'success')?.cnt || 0
            const total = data.summary.files
            const pct = total > 0 ? Math.round(parsed / total * 100) : 0
            return (
              <div style={{ background: '#fff', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,.1)' }}>
                <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 10, color: '#1f2937' }}>
                  파싱 진행률 — {parsed.toLocaleString()} / {total.toLocaleString()} ({pct}%)
                </div>
                <div style={{ background: '#e5e7eb', borderRadius: 99, height: 12, overflow: 'hidden' }}>
                  <div style={{ background: '#16a34a', height: '100%', width: `${pct}%`, transition: 'width .4s' }} />
                </div>
              </div>
            )
          })()}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
            {/* list_type 분포 */}
            <Table
              title="자료 유형(list_type) 분포"
              rows={data.by_list_type}
              columns={[
                { key: 'list_type', label: '유형' },
                { key: 'cnt', label: '건수', align: 'right', render: v => v.toLocaleString() },
              ]}
            />

            {/* 파일 상태 */}
            <Table
              title="파일 다운로드/파싱 상태"
              rows={data.by_file_status}
              columns={[
                { key: 'download_status', label: '다운로드' },
                { key: 'parse_status', label: '파싱', render: v => parseStatusBadge(v) },
                { key: 'cnt', label: '건수', align: 'right', render: v => v.toLocaleString() },
              ]}
            />

            {/* 파일 타입 */}
            <Table
              title="파일 형식 분포"
              rows={data.by_file_type}
              columns={[
                { key: 'file_type', label: '확장자' },
                { key: 'cnt', label: '건수', align: 'right', render: v => v.toLocaleString() },
              ]}
            />

            {/* 공종 TOP 20 */}
            <Table
              title="공종(trade_type) TOP 20"
              rows={data.top_trades}
              columns={[
                { key: 'trade_type', label: '공종' },
                { key: 'cnt', label: '태그 수', align: 'right', render: v => v.toLocaleString() },
              ]}
            />
          </div>

          {/* 최근 수집 자료 */}
          <Table
            title="최근 수집 자료 10건"
            rows={data.recent_materials}
            columns={[
              { key: 'id', label: 'ID', align: 'right' },
              { key: 'title', label: '제목' },
              { key: 'list_type', label: '유형' },
              { key: 'created_at', label: '수집일시', render: v => v?.slice(0, 19) },
            ]}
          />

          {/* DB 스키마 */}
          <SchemaViewer schema={data.schema} />
        </div>
      )}
    </div>
  )
}
