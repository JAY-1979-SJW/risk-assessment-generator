import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Card, Btn, Input, Textarea } from '../../components/Layout'

const SECTIONS = [
  { type: 'meeting',        title: '위험성평가 회의',    dateLabel: '회의일자' },
  { type: 'education',      title: '안전보건 교육',       dateLabel: '교육일자' },
  { type: 'safety-meeting', title: '안전보건 협의체 회의', dateLabel: '회의일자' },
]

const EMPTY_FORM = { held_date: '', location: '', agenda: '', result: '', next_action: '', attendees: [] }
const EMPTY_ATTENDEE = { department: '', position: '', name: '' }

function AttendeeTable({ attendees, onChange }) {
  function update(i, k, v) {
    const next = attendees.map((a, idx) => idx === i ? { ...a, [k]: v } : a)
    onChange(next)
  }
  function add() { onChange([...attendees, { ...EMPTY_ATTENDEE }]) }
  function remove(i) { onChange(attendees.filter((_, idx) => idx !== i)) }

  return (
    <div>
      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569', marginBottom: 4 }}>참석자</div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', marginBottom: 6 }}>
        <thead>
          <tr style={{ background: '#f1f5f9' }}>
            {['부서','직위','성명',''].map(h => (
              <th key={h} style={{ padding: '0.3rem 0.5rem', border: '1px solid #e2e8f0', textAlign: 'center', fontWeight: 600, fontSize: '0.75rem' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {attendees.map((a, i) => (
            <tr key={i}>
              <td style={{ padding: 3, border: '1px solid #e2e8f0' }}>
                <input value={a.department} onChange={e => update(i, 'department', e.target.value)}
                  style={{ width: '100%', border: 'none', outline: 'none', fontSize: '0.8rem', padding: '0.15rem' }} />
              </td>
              <td style={{ padding: 3, border: '1px solid #e2e8f0' }}>
                <input value={a.position} onChange={e => update(i, 'position', e.target.value)}
                  style={{ width: '100%', border: 'none', outline: 'none', fontSize: '0.8rem', padding: '0.15rem' }} />
              </td>
              <td style={{ padding: 3, border: '1px solid #e2e8f0' }}>
                <input value={a.name} onChange={e => update(i, 'name', e.target.value)}
                  style={{ width: '100%', border: 'none', outline: 'none', fontSize: '0.8rem', padding: '0.15rem' }} />
              </td>
              <td style={{ padding: 3, border: '1px solid #e2e8f0', width: 36, textAlign: 'center' }}>
                <button onClick={() => remove(i)} style={{ border: 'none', background: 'none', cursor: 'pointer', color: '#dc2626', fontSize: '0.85rem' }}>✕</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Btn small color="gray" onClick={add}>+ 참석자 추가</Btn>
    </div>
  )
}

function FormSection({ pid, type, title, dateLabel }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg]   = useState('')

  useEffect(() => {
    api.getForm(pid, type)
      .then(d => setForm({ ...EMPTY_FORM, ...d, attendees: d.attendees || [] }))
      .catch(() => setForm(EMPTY_FORM))
  }, [pid, type])

  function set(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function save() {
    setSaving(true); setMsg('')
    try {
      await api.saveForm(pid, type, form)
      setMsg('저장되었습니다.')
      setTimeout(() => setMsg(''), 2000)
    } catch (e) { setMsg('오류: ' + e.message) }
    finally { setSaving(false) }
  }

  return (
    <Card title={title}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <Input label={dateLabel} type="date" value={form.held_date} onChange={v => set('held_date', v)} />
        <Input label="장소"       value={form.location}  onChange={v => set('location', v)} />
      </div>
      <div style={{ display: 'grid', gap: 12, marginBottom: 12 }}>
        <Textarea label="안건/주요내용" value={form.agenda}      onChange={v => set('agenda', v)}      rows={3} />
        <Textarea label="결과/결정사항" value={form.result}      onChange={v => set('result', v)}      rows={3} />
        <Textarea label="후속조치"      value={form.next_action} onChange={v => set('next_action', v)} rows={2} />
      </div>
      <AttendeeTable attendees={form.attendees} onChange={v => set('attendees', v)} />
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8, marginTop: 12 }}>
        {msg && <span style={{ fontSize: '0.82rem', color: msg.startsWith('오류') ? '#dc2626' : '#16a34a' }}>{msg}</span>}
        <Btn color="blue" onClick={save} disabled={saving}>{saving ? '저장 중...' : '저장'}</Btn>
      </div>
    </Card>
  )
}

export default function MeetingTab({ pid }) {
  return (
    <div>
      {SECTIONS.map(s => (
        <FormSection key={s.type} pid={pid} type={s.type} title={s.title} dateLabel={s.dateLabel} />
      ))}
    </div>
  )
}
