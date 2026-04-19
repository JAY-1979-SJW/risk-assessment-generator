import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Card, Btn, Input, Textarea, Select } from '../../components/Layout'

const EVAL_TYPES = ['최초평가', '정기평가', '수시평가']

const EMPTY = {
  company_name:'', ceo_name:'', business_type:'', address:'',
  site_name:'', work_type:'', eval_date:'', eval_type:'정기평가',
  safety_policy:'', safety_goal:''
}

export default function CompanyTab({ pid }) {
  const [form, setForm] = useState(EMPTY)
  const [categories, setCategories] = useState([])
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.getCompany(pid).then(d => setForm({ ...EMPTY, ...d })).catch(() => {})
    api.getCategories().then(d => setCategories(d.categories || [])).catch(() => {})
  }, [pid])

  function set(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function applyTemplate(cat) {
    try {
      const [p, g] = await Promise.all([api.getPolicy(cat), api.getGoal(cat)])
      setForm(f => ({ ...f, safety_policy: p.policy, safety_goal: g.goal, work_type: cat }))
    } catch {}
  }

  async function save() {
    setSaving(true); setMsg('')
    try {
      await api.saveCompany(pid, form)
      setMsg('저장되었습니다.')
      setTimeout(() => setMsg(''), 2000)
    } catch (e) { setMsg('오류: ' + e.message) }
    finally { setSaving(false) }
  }

  return (
    <div>
      <Card title="기본정보">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Input label="회사명" value={form.company_name} onChange={v => set('company_name', v)} required />
          <Input label="대표자" value={form.ceo_name}     onChange={v => set('ceo_name', v)}     required />
          <Input label="업종"   value={form.business_type} onChange={v => set('business_type', v)} />
          <Input label="현장명" value={form.site_name}    onChange={v => set('site_name', v)}    required />
          <Input label="평가일자" type="date" value={form.eval_date} onChange={v => set('eval_date', v)} required />
          <Select label="평가유형" value={form.eval_type} onChange={v => set('eval_type', v)} options={EVAL_TYPES} />
        </div>
        <div style={{ marginTop: 12 }}>
          <Input label="주소" value={form.address} onChange={v => set('address', v)} />
        </div>
      </Card>

      <Card title="안전보건방침 & 추진목표">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.78rem', color: '#64748b' }}>업종 템플릿:</span>
          {categories.map(cat => (
            <Btn key={cat} small color="gray" onClick={() => applyTemplate(cat)}>{cat}</Btn>
          ))}
        </div>
        <div style={{ display: 'grid', gap: 12 }}>
          <Textarea label="안전보건방침" value={form.safety_policy} onChange={v => set('safety_policy', v)} rows={4} />
          <Textarea label="추진목표"     value={form.safety_goal}   onChange={v => set('safety_goal', v)}   rows={4} />
        </div>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8 }}>
        {msg && <span style={{ fontSize: '0.82rem', color: msg.startsWith('오류') ? '#dc2626' : '#16a34a' }}>{msg}</span>}
        <Btn color="blue" onClick={save} disabled={saving}>{saving ? '저장 중...' : '저장'}</Btn>
      </div>
    </div>
  )
}
