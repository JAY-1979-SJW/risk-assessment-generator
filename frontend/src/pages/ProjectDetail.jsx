import React, { useState } from 'react'
import Layout, { Btn } from '../components/Layout'
import CompanyTab from './tabs/CompanyTab'
import OrgTab from './tabs/OrgTab'
import AssessmentTab from './tabs/AssessmentTab'
import MeetingTab from './tabs/MeetingTab'
import CriteriaTab from './tabs/CriteriaTab'
import { api } from '../api/client'

const TABS = [
  { id: 'company',    label: '① 기본정보' },
  { id: 'org',        label: '② 조직구성' },
  { id: 'assessment', label: '③ 위험성평가' },
  { id: 'meeting',    label: '④ 회의/교육' },
  { id: 'criteria',   label: '⑤ 평가기준' },
]

export default function ProjectDetail({ pid, onBack }) {
  const [tab, setTab] = useState('company')
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')

  async function handleExport() {
    setExporting(true)
    setExportError('')
    try {
      const blob = await api.exportExcel(pid)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `위험성평가표_${pid}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setExportError(e.message)
    } finally {
      setExporting(false)
    }
  }

  return (
    <Layout
      subtitle={`프로젝트 #${pid}`}
      actions={
        <>
          <Btn small color="gray" onClick={onBack}>← 목록</Btn>
          <Btn small color="green" onClick={handleExport} disabled={exporting}>
            {exporting ? '생성 중...' : '엑셀 내보내기'}
          </Btn>
        </>
      }
    >
      {exportError && (
        <div style={{ color: '#dc2626', fontSize: '0.82rem', marginBottom: 8 }}>{exportError}</div>
      )}

      {/* 탭 바 */}
      <div style={{ display: 'flex', gap: 4, marginBottom: '1rem', borderBottom: '2px solid #e2e8f0', paddingBottom: 0 }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{
              padding: '0.5rem 1rem', border: 'none', background: 'none', cursor: 'pointer',
              fontWeight: tab === t.id ? 700 : 400,
              color: tab === t.id ? '#2563eb' : '#64748b',
              borderBottom: tab === t.id ? '2px solid #2563eb' : '2px solid transparent',
              marginBottom: -2, fontSize: '0.875rem',
            }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* 탭 컨텐츠 */}
      {tab === 'company'    && <CompanyTab    pid={pid} />}
      {tab === 'org'        && <OrgTab        pid={pid} />}
      {tab === 'assessment' && <AssessmentTab pid={pid} />}
      {tab === 'meeting'    && <MeetingTab    pid={pid} />}
      {tab === 'criteria'   && <CriteriaTab             />}
    </Layout>
  )
}
