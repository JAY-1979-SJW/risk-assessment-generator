import React, { useEffect, useState } from 'react'
import { Card, Btn, Input, Textarea } from '../../components/Layout'
import { api } from '../../api/client'

const EMPTY_MATERIAL = {
  machine_type: '',
  machine_max_load: '',
  work_location: '',
  work_method: '',
  safety_measures: '',
  speed_limit: '',
  travel_route_text: '',
  emergency_measure: '',
  emergency_contact: '',
  guide_worker_required: false,
  pedestrian_separation: '',
  pre_check_items_text: '',
}

function buildMaterialFormData(form) {
  const pre_check_items = form.pre_check_items_text
    .split('\n')
    .map(l => l.trim())
    .filter(l => l.length > 0)
    .map(l => ({ check_item: l, result: '', note: '' }))

  const data = {
    machine_type: form.machine_type,
    machine_max_load: form.machine_max_load,
    work_location: form.work_location,
    work_method: form.work_method,
    safety_measures: form.safety_measures,
    speed_limit: form.speed_limit,
    travel_route_text: form.travel_route_text,
    emergency_measure: form.emergency_measure,
    emergency_contact: form.emergency_contact,
    guide_worker_required: String(form.guide_worker_required),
    pedestrian_separation: form.pedestrian_separation,
  }
  if (pre_check_items.length > 0) {
    data.pre_check_items = pre_check_items
  }
  return data
}

export default function FormsTab() {
  const [forms, setForms] = useState([])
  const [selected, setSelected] = useState(null)
  const [materialForm, setMaterialForm] = useState(EMPTY_MATERIAL)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getFormTypes()
      .then(d => setForms(d.forms || []))
      .catch(() => setError('서식 목록을 불러오지 못했습니다.'))
  }, [])

  function setField(key, value) {
    setMaterialForm(prev => ({ ...prev, [key]: value }))
  }

  async function handleExport() {
    if (!selected) return
    setExporting(true)
    setError('')
    try {
      const spec = forms.find(f => f.form_type === selected)
      let form_data
      if (selected === 'material_handling_workplan') {
        form_data = buildMaterialFormData(materialForm)
      } else {
        form_data = {}
        for (const field of (spec?.required_fields || [])) {
          form_data[field] = ''
        }
      }
      const blob = await api.exportForm(selected, form_data)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selected}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setError(e.message)
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <Card title="서식 선택">
        {forms.length === 0 && !error && (
          <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>목록을 불러오는 중...</div>
        )}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {forms.map(f => (
            <button key={f.form_type} onClick={() => setSelected(f.form_type)}
              style={{
                padding: '0.5rem 1rem',
                border: `2px solid ${selected === f.form_type ? '#2563eb' : '#e2e8f0'}`,
                borderRadius: 8,
                background: selected === f.form_type ? '#eff6ff' : '#fff',
                color: selected === f.form_type ? '#2563eb' : '#475569',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: selected === f.form_type ? 700 : 400,
              }}
            >
              {f.display_name}
            </button>
          ))}
        </div>
      </Card>

      {selected === 'material_handling_workplan' && (
        <>
          <Card title="법정 필수 항목">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <Input label="장비 종류" required value={materialForm.machine_type}
                onChange={v => setField('machine_type', v)} />
              <Input label="최대하중" required value={materialForm.machine_max_load}
                onChange={v => setField('machine_max_load', v)} />
              <Input label="작업 위치" value={materialForm.work_location}
                onChange={v => setField('work_location', v)} />
              <Input label="속도 제한" value={materialForm.speed_limit}
                onChange={v => setField('speed_limit', v)} />
            </div>
            <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <Textarea label="작업 방법 *" required rows={3} value={materialForm.work_method}
                onChange={v => setField('work_method', v)} />
              <Textarea label="안전조치" rows={3} value={materialForm.safety_measures}
                onChange={v => setField('safety_measures', v)} />
              <Textarea label="운행경로 설명 *" rows={3} value={materialForm.travel_route_text}
                onChange={v => setField('travel_route_text', v)} />
              <Textarea label="비상조치 방법 *" rows={2} value={materialForm.emergency_measure}
                onChange={v => setField('emergency_measure', v)} />
            </div>
          </Card>

          <Card title="보강 항목">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <Input label="비상연락처" value={materialForm.emergency_contact}
                onChange={v => setField('emergency_contact', v)} />
              <Input label="보행자 분리 방법" value={materialForm.pedestrian_separation}
                onChange={v => setField('pedestrian_separation', v)} />
            </div>
            <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input type="checkbox"
                  checked={materialForm.guide_worker_required}
                  onChange={e => setField('guide_worker_required', e.target.checked)}
                />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>유도자 필요</span>
              </label>
              <Textarea
                label="작업 전 점검항목 (줄 단위 입력, 미입력 시 법정 기본값 8개 자동 적용)"
                rows={6}
                value={materialForm.pre_check_items_text}
                onChange={v => setField('pre_check_items_text', v)}
                placeholder={'제동장치 및 조종장치 기능 이상 유무\n하역장치 및 유압장치 기능 이상 유무\n바퀴의 이상 유무'}
              />
              <div style={{
                background: '#fef9c3', border: '1px solid #fde047',
                borderRadius: 6, padding: '0.5rem 0.75rem',
                fontSize: '0.78rem', color: '#713f12',
              }}>
                ※ 운행경로 개략도는 출력 후 수기로 작성하세요 (서식 내 스케치 공간 제공됨).
              </div>
            </div>
          </Card>
        </>
      )}

      {selected && selected !== 'material_handling_workplan' && (
        <Card>
          <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
            선택한 서식의 세부 입력폼은 추후 제공될 예정입니다. 지금 다운로드하면 빈 서식이 생성됩니다.
          </div>
        </Card>
      )}

      {selected && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: '0.5rem' }}>
          <Btn color="green" onClick={handleExport} disabled={exporting}>
            {exporting ? '생성 중...' : '서식 다운로드'}
          </Btn>
          {error && <span style={{ fontSize: '0.82rem', color: '#dc2626' }}>{error}</span>}
        </div>
      )}
    </div>
  )
}
