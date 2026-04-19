import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Card } from '../../components/Layout'

export default function CriteriaTab() {
  const [criteria, setCriteria] = useState(null)

  useEffect(() => {
    api.getRiskCriteria().then(d => setCriteria(d)).catch(() => {})
  }, [])

  const TH = { padding: '0.45rem 0.6rem', border: '1px solid #e2e8f0', background: '#f1f5f9', fontWeight: 600, fontSize: '0.78rem', textAlign: 'center' }
  const TD = { padding: '0.4rem 0.6rem', border: '1px solid #e2e8f0', fontSize: '0.82rem', textAlign: 'center' }

  const levelColor = { 높음: '#dc2626', 보통: '#d97706', 낮음: '#16a34a' }
  const levelBg    = { 높음: '#fef2f2', 보통: '#fffbeb', 낮음: '#f0fdf4' }

  return (
    <div>
      <Card title="위험성 결정 기준">
        <p style={{ fontSize: '0.82rem', color: '#64748b', marginTop: 0, marginBottom: 12 }}>
          위험성 = 가능성(빈도) × 중대성(강도). 점수에 따라 위험도 수준을 결정합니다.
        </p>
        <table style={{ borderCollapse: 'collapse', fontSize: '0.82rem', marginBottom: '1rem' }}>
          <thead>
            <tr>
              <th style={TH}>점수</th>
              <th style={TH}>위험도</th>
              <th style={TH}>조치 기준</th>
            </tr>
          </thead>
          <tbody>
            {criteria?.levels?.map((row, i) => (
              <tr key={i}>
                <td style={TD}>{row.score_range}</td>
                <td style={{ ...TD, fontWeight: 700, color: levelColor[row.level] || '#334155', background: levelBg[row.level] || '#fff' }}>{row.level}</td>
                <td style={{ ...TD, textAlign: 'left' }}>{row.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="가능성(빈도) 기준">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr>
              <th style={TH}>점수</th>
              <th style={TH}>수준</th>
              <th style={TH}>기준</th>
            </tr>
          </thead>
          <tbody>
            {criteria?.possibility?.map((row, i) => (
              <tr key={i}>
                <td style={TD}>{row.score}</td>
                <td style={{ ...TD, fontWeight: 600 }}>{row.label}</td>
                <td style={{ ...TD, textAlign: 'left' }}>{row.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="중대성(강도) 기준">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
          <thead>
            <tr>
              <th style={TH}>점수</th>
              <th style={TH}>수준</th>
              <th style={TH}>기준</th>
            </tr>
          </thead>
          <tbody>
            {criteria?.severity?.map((row, i) => (
              <tr key={i}>
                <td style={TD}>{row.score}</td>
                <td style={{ ...TD, fontWeight: 600 }}>{row.label}</td>
                <td style={{ ...TD, textAlign: 'left' }}>{row.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      <Card title="위험성 결정 매트릭스">
        <table style={{ borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr>
              <th style={TH}>가능성 \ 중대성</th>
              {[1, 2, 3].map(s => <th key={s} style={TH}>중대성 {s}</th>)}
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3].map(p => (
              <tr key={p}>
                <th style={TH}>가능성 {p}</th>
                {[1, 2, 3].map(s => {
                  const score = p * s
                  const lv = score >= 6 ? '높음' : score >= 3 ? '보통' : '낮음'
                  return (
                    <td key={s} style={{ ...TD, fontWeight: 700, color: levelColor[lv], background: levelBg[lv] }}>
                      {score} ({lv})
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
