import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Card, Btn, Input, Textarea, Select } from '../../components/Layout'

const ROLES = ['총괄관리', '실무총괄', '현장실시', '기술지원', '참여/협의']
const EMPTY_MEMBER = { position:'', name:'', role:'현장실시', responsibility:'' }

export default function OrgTab({ pid }) {
  const [members, setMembers] = useState([])
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.getOrg(pid)
      .then(d => setMembers(d.members?.length ? d.members : [{ ...EMPTY_MEMBER }]))
      .catch(() => setMembers([{ ...EMPTY_MEMBER }]))
  }, [pid])

  function update(i, k, v) {
    setMembers(ms => ms.map((m, idx) => idx === i ? { ...m, [k]: v } : m))
  }
  function add() { setMembers(ms => [...ms, { ...EMPTY_MEMBER }]) }
  function remove(i) { setMembers(ms => ms.filter((_, idx) => idx !== i)) }

  async function save() {
    setSaving(true); setMsg('')
    try {
      await api.saveOrgBulk(pid, members.map((m, i) => ({ ...m, sort_order: i })))
      setMsg('저장되었습니다.')
      setTimeout(() => setMsg(''), 2000)
    } catch (e) { setMsg('오류: ' + e.message) }
    finally { setSaving(false) }
  }

  return (
    <div>
      <Card title="위험성평가 실시 조직 구성">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: '#f1f5f9' }}>
              {['직위/직책','성명','역할','책임 및 권한',''].map(h => (
                <th key={h} style={{ padding: '0.5rem', border: '1px solid #e2e8f0', textAlign: 'center', fontWeight: 600, fontSize: '0.8rem' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {members.map((m, i) => (
              <tr key={i}>
                <td style={{ padding: 4, border: '1px solid #e2e8f0', width: 140 }}>
                  <input value={m.position} onChange={e => update(i,'position',e.target.value)}
                    style={{ width:'100%', border:'none', outline:'none', fontSize:'0.82rem', padding:'0.25rem' }} />
                </td>
                <td style={{ padding: 4, border: '1px solid #e2e8f0', width: 100 }}>
                  <input value={m.name} onChange={e => update(i,'name',e.target.value)}
                    style={{ width:'100%', border:'none', outline:'none', fontSize:'0.82rem', padding:'0.25rem' }} />
                </td>
                <td style={{ padding: 4, border: '1px solid #e2e8f0', width: 110 }}>
                  <select value={m.role} onChange={e => update(i,'role',e.target.value)}
                    style={{ border:'none', outline:'none', fontSize:'0.82rem', width:'100%' }}>
                    {ROLES.map(r => <option key={r}>{r}</option>)}
                  </select>
                </td>
                <td style={{ padding: 4, border: '1px solid #e2e8f0' }}>
                  <input value={m.responsibility} onChange={e => update(i,'responsibility',e.target.value)}
                    style={{ width:'100%', border:'none', outline:'none', fontSize:'0.82rem', padding:'0.25rem' }} />
                </td>
                <td style={{ padding: 4, border: '1px solid #e2e8f0', width: 40, textAlign:'center' }}>
                  <button onClick={() => remove(i)} style={{ border:'none', background:'none', cursor:'pointer', color:'#dc2626', fontSize:'0.9rem' }}>✕</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: 8 }}>
          <Btn small color="gray" onClick={add}>+ 행 추가</Btn>
        </div>
      </Card>

      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8 }}>
        {msg && <span style={{ fontSize: '0.82rem', color: msg.startsWith('오류') ? '#dc2626' : '#16a34a' }}>{msg}</span>}
        <Btn color="blue" onClick={save} disabled={saving}>{saving ? '저장 중...' : '저장'}</Btn>
      </div>
    </div>
  )
}
