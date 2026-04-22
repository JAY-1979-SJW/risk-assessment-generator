import React, { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Card, Btn, Input, Select, RiskBadge } from '../../components/Layout'

const EMPTY = {
  process_name: '', work_name: '', hazard_type: '', hazard_detail: '',
  current_measure: '', possibility: 2, severity: 2,
  improvement: '', after_possibility: 1, after_severity: 1, manager: ''
}

const SCORE_OPTS = [
  { value: 1, label: '1' }, { value: 2, label: '2' }, { value: 3, label: '3' }
]

function riskLevel(p, s) {
  const score = p * s
  if (score >= 6) return '높음'
  if (score >= 3) return '보통'
  return '낮음'
}

function RowForm({ item, onChange, onSave, onCancel }) {
  return (
    <tr style={{ background: '#f8fafc' }}>
      <td style={TD}><input value={item.process_name}   onChange={e => onChange('process_name', e.target.value)}   style={INP} /></td>
      <td style={TD}><input value={item.work_name}      onChange={e => onChange('work_name', e.target.value)}      style={INP} /></td>
      <td style={TD}><input value={item.hazard_type}    onChange={e => onChange('hazard_type', e.target.value)}    style={INP} /></td>
      <td style={TD}><input value={item.hazard_detail}  onChange={e => onChange('hazard_detail', e.target.value)}  style={{ ...INP, minWidth: 140 }} /></td>
      <td style={TD}><input value={item.current_measure}onChange={e => onChange('current_measure', e.target.value)}style={{ ...INP, minWidth: 140 }} /></td>
      <td style={TD}>
        <select value={item.possibility} onChange={e => onChange('possibility', Number(e.target.value))} style={SEL}>
          {SCORE_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </td>
      <td style={TD}>
        <select value={item.severity} onChange={e => onChange('severity', Number(e.target.value))} style={SEL}>
          {SCORE_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </td>
      <td style={{ ...TD, textAlign: 'center' }}><RiskBadge level={riskLevel(item.possibility, item.severity)} /></td>
      <td style={TD}><input value={item.improvement}       onChange={e => onChange('improvement', e.target.value)}       style={{ ...INP, minWidth: 140 }} /></td>
      <td style={TD}>
        <select value={item.after_possibility} onChange={e => onChange('after_possibility', Number(e.target.value))} style={SEL}>
          {SCORE_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </td>
      <td style={TD}>
        <select value={item.after_severity} onChange={e => onChange('after_severity', Number(e.target.value))} style={SEL}>
          {SCORE_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </td>
      <td style={{ ...TD, textAlign: 'center' }}><RiskBadge level={riskLevel(item.after_possibility, item.after_severity)} /></td>
      <td style={TD}><input value={item.manager} onChange={e => onChange('manager', e.target.value)} style={INP} /></td>
      <td style={{ ...TD, whiteSpace: 'nowrap' }}>
        <Btn small color="blue" onClick={onSave}>저장</Btn>{' '}
        <Btn small color="gray" onClick={onCancel}>취소</Btn>
      </td>
    </tr>
  )
}

// ─── Draft sub-components ─────────────────────────────────────────────────────

const CONDITION_FLAG_OPTIONS = [
  { value: 'high_place',     label: '고소작업' },
  { value: 'confined_space', label: '밀폐공간' },
  { value: 'live_electric',  label: '활선작업' },
  { value: 'night_work',     label: '야간작업' },
  { value: 'chemical_use',   label: '화학물질' },
]

function DraftRowList({ rows, recalcLoading, onRecalculate }) {
  return (
    <div style={{ marginTop: 8 }}>
      {rows.map(row => (
        <div key={row.row_id} style={{
          border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.75rem',
          marginBottom: 8, background: '#f8fafc',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
            <div>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'monospace' }}>{row.row_id}</span>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#1e293b', marginTop: 2 }}>
                {row.editable.hazard_text}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: 2 }}>
                위험도 점수: {row.hazard.hazard_score}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexShrink: 0, marginLeft: 8 }}>
              {row.row_flags.map(flag => (
                <span key={flag} style={{
                  fontSize: '0.68rem', background: '#fef2f2', color: '#dc2626',
                  border: '1px solid #fecaca', borderRadius: 4, padding: '0.1rem 0.35rem',
                }}>{flag}</span>
              ))}
              <Btn small color="gray" onClick={() => onRecalculate(row)} disabled={!!recalcLoading[row.row_id]}>
                {recalcLoading[row.row_id] ? '재계산 중...' : '재계산'}
              </Btn>
            </div>
          </div>

          {/* 안전대책: editable.control_texts (사용자 수정용) — controls[] 원본과 분리 */}
          <div style={{ marginBottom: 6 }}>
            <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569', marginBottom: 3 }}>안전대책</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {row.editable.control_texts.map((txt, i) => (
                <span key={i} style={{
                  fontSize: '0.75rem', background: '#eff6ff', color: '#1d4ed8',
                  border: '1px solid #bfdbfe', borderRadius: 4, padding: '0.15rem 0.5rem',
                }}>{txt}</span>
              ))}
            </div>
          </div>

          {/* 법적 근거 */}
          {row.laws.length > 0 && (
            <div>
              <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569', marginBottom: 3 }}>법적 근거</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {row.laws.map(law => (
                  <span key={law.law_id} style={{
                    fontSize: '0.72rem', background: '#f0fdf4', color: '#15803d',
                    border: '1px solid #bbf7d0', borderRadius: 4, padding: '0.1rem 0.4rem',
                  }}>{law.law_title}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function DraftPanel() {
  const [form, setForm]                   = useState({ work_type_code: '', condition_flags: [] })
  const [loading, setLoading]             = useState(false)
  const [msg, setMsg]                     = useState('')
  const [draftRows, setDraftRows]         = useState(null)
  const [summary, setSummary]             = useState(null)
  const [reviewFlags, setReviewFlags]     = useState([])
  const [recalcLoading, setRecalcLoading] = useState({})

  function toggleFlag(flag) {
    setForm(f => ({
      ...f,
      condition_flags: f.condition_flags.includes(flag)
        ? f.condition_flags.filter(x => x !== flag)
        : [...f.condition_flags, flag],
    }))
  }

  async function handleRecommend() {
    if (!form.work_type_code.trim()) { setMsg('작업유형 코드를 입력하세요.'); return }
    setLoading(true); setMsg(''); setDraftRows(null); setReviewFlags([]); setSummary(null)
    try {
      const result = await api.draftRecommend({
        work: { work_type_code: form.work_type_code.trim() },
        site_context: { condition_flags: form.condition_flags },
      })
      setDraftRows(result.rows)
      setSummary(result.summary)
      setReviewFlags(result.review_flags)
    } catch (e) { setMsg('오류: ' + e.message) }
    finally { setLoading(false) }
  }

  async function handleRecalculate(row) {
    setRecalcLoading(prev => ({ ...prev, [row.row_id]: true }))
    setMsg('')
    try {
      const result = await api.draftRecalculate({
        draft_context: {
          work_type_code: form.work_type_code.trim(),
          condition_flags: form.condition_flags,
        },
        rows: [{
          row_id: row.row_id,
          hazard_code: row.hazard.hazard_code,
          selected_control_codes: row.controls.map(c => c.control_code),
          custom_control_texts: [],
          excluded_law_ids: [],
        }],
      })
      const updated = result.rows[0]
      setDraftRows(prev => prev.map(r => r.row_id === updated.row_id ? updated : r))
    } catch (e) { setMsg('재계산 오류: ' + e.message) }
    finally { setRecalcLoading(prev => ({ ...prev, [row.row_id]: false })) }
  }

  return (
    <Card title="AI 추천 초안 생성 (구조화 엔진)">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8, alignItems: 'flex-end', marginBottom: 8 }}>
        <Input
          label="작업유형 코드 *"
          value={form.work_type_code}
          onChange={v => setForm(f => ({ ...f, work_type_code: v }))}
          placeholder="예: ELEC_LIVE · TEMP_SCAFF · WATER_MANHOLE · LIFT_RIGGING"
        />
        <Btn color="blue" onClick={handleRecommend} disabled={loading}>
          {loading ? '생성 중...' : 'AI 추천 초안'}
        </Btn>
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 8 }}>
        {CONDITION_FLAG_OPTIONS.map(opt => (
          <label key={opt.value} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.8rem', cursor: 'pointer', userSelect: 'none' }}>
            <input type="checkbox" checked={form.condition_flags.includes(opt.value)} onChange={() => toggleFlag(opt.value)} />
            {opt.label}
          </label>
        ))}
      </div>
      {msg && (
        <div style={{ fontSize: '0.82rem', color: msg.startsWith('오류') ? '#dc2626' : '#16a34a', marginBottom: 6 }}>{msg}</div>
      )}
      {reviewFlags.length > 0 && (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
          {reviewFlags.map(flag => (
            <span key={flag} style={{
              fontSize: '0.72rem', background: '#fffbeb', color: '#d97706',
              border: '1px solid #fde68a', borderRadius: 4, padding: '0.1rem 0.4rem',
            }}>{flag}</span>
          ))}
        </div>
      )}
      {summary && (
        <div style={{ fontSize: '0.78rem', color: '#475569', marginBottom: 6 }}>
          위험요소 {summary.hazard_count}건 · 대책 {summary.control_count}건 · 법적 근거 {summary.law_count}건
        </div>
      )}
      {draftRows && draftRows.length > 0 && (
        <DraftRowList rows={draftRows} recalcLoading={recalcLoading} onRecalculate={handleRecalculate} />
      )}
      {draftRows && draftRows.length === 0 && (
        <div style={{ fontSize: '0.82rem', color: '#64748b' }}>해당 작업유형의 위험요소 데이터가 없습니다.</div>
      )}
    </Card>
  )
}

// ─── Style constants ──────────────────────────────────────────────────────────

const TD  = { padding: 4, border: '1px solid #e2e8f0', verticalAlign: 'middle' }
const INP = { width: '100%', border: 'none', outline: 'none', fontSize: '0.8rem', padding: '0.2rem', minWidth: 80 }
const SEL = { border: 'none', outline: 'none', fontSize: '0.8rem', width: '100%' }
const TH  = { padding: '0.4rem 0.3rem', border: '1px solid #e2e8f0', textAlign: 'center', fontWeight: 600, fontSize: '0.75rem', background: '#f1f5f9', whiteSpace: 'nowrap' }

export default function AssessmentTab({ pid }) {
  const [items, setItems]       = useState([])
  const [editId, setEditId]     = useState(null)
  const [editBuf, setEditBuf]   = useState(null)
  const [adding, setAdding]     = useState(false)
  const [addBuf, setAddBuf]     = useState({ ...EMPTY })
  const [aiForm, setAiForm]     = useState({ process_name: '', trade_type: '', work_type: '' })
  const [generating, setGenerating] = useState(false)
  const [aiMsg, setAiMsg]       = useState('')
  const [msg, setMsg]           = useState('')

  useEffect(() => { load() }, [pid])

  function load() {
    api.getAssessments(pid).then(d => setItems(d.items || [])).catch(() => {})
  }

  function flash(m) { setMsg(m); setTimeout(() => setMsg(''), 2500) }

  async function saveNew() {
    try {
      await api.addAssessment(pid, addBuf)
      setAdding(false); setAddBuf({ ...EMPTY }); load(); flash('추가되었습니다.')
    } catch (e) { flash('오류: ' + e.message) }
  }

  function startEdit(item) {
    setEditId(item.id)
    setEditBuf({ ...item })
  }

  async function saveEdit() {
    try {
      await api.updateAssessment(pid, editId, editBuf)
      setEditId(null); setEditBuf(null); load(); flash('수정되었습니다.')
    } catch (e) { flash('오류: ' + e.message) }
  }

  async function del(id) {
    if (!confirm('삭제하시겠습니까?')) return
    try { await api.deleteAssessment(pid, id); load(); flash('삭제되었습니다.') }
    catch (e) { flash('오류: ' + e.message) }
  }

  async function handleGenerate() {
    if (!aiForm.process_name.trim()) { setAiMsg('공정명을 입력하세요.'); return }
    setGenerating(true); setAiMsg('')
    try {
      const result = await api.generateAI({
        project_id: pid,
        process_name: aiForm.process_name,
        trade_type: aiForm.trade_type,
        work_type: aiForm.work_type,
      })
      if (result.items?.length) {
        await api.bulkAddAssessments(pid, result.items)
        load()
        setAiMsg(`AI가 ${result.items.length}건을 생성했습니다.`)
      } else {
        setAiMsg('생성된 항목이 없습니다.')
      }
    } catch (e) { setAiMsg('오류: ' + e.message) }
    finally { setGenerating(false) }
  }

  return (
    <div>
      {/* AI 자동생성 (KOSHA DB + OpenAI) */}
      <Card title="AI 자동생성 (KOSHA DB + OpenAI)">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8, alignItems: 'flex-end' }}>
          <Input label="공정명 *" value={aiForm.process_name} onChange={v => setAiForm(f => ({ ...f, process_name: v }))} placeholder="예: 거푸집 설치" />
          <Input label="업종"     value={aiForm.trade_type}   onChange={v => setAiForm(f => ({ ...f, trade_type: v }))}   placeholder="예: 건설업" />
          <Input label="작업유형" value={aiForm.work_type}    onChange={v => setAiForm(f => ({ ...f, work_type: v }))}    placeholder="예: 고소작업" />
          <Btn color="purple" onClick={handleGenerate} disabled={generating}>
            {generating ? '생성 중...' : 'AI 생성'}
          </Btn>
        </div>
        {aiMsg && (
          <div style={{ marginTop: 8, fontSize: '0.82rem', color: aiMsg.startsWith('오류') ? '#dc2626' : '#16a34a' }}>{aiMsg}</div>
        )}
      </Card>

      {/* AI 추천 초안 생성 (구조화 엔진) — draftRows는 items와 분리된 별도 상태 */}
      <DraftPanel />

      {/* 평가 항목 테이블 */}
      <Card title="위험성평가 항목">
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr>
                {['공정명','작업명','유해위험요인 유형','유해위험요인 상세','현재 안전보건조치',
                  '가능성','중대성','현재위험도','개선 대책','개선후 가능성','개선후 중대성','개선후 위험도','담당자',''].map(h => (
                  <th key={h} style={TH}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                editId === item.id
                  ? <RowForm key={item.id}
                      item={editBuf}
                      onChange={(k, v) => setEditBuf(b => ({ ...b, [k]: v }))}
                      onSave={saveEdit}
                      onCancel={() => setEditId(null)} />
                  : <tr key={item.id}>
                      <td style={TD}>{item.process_name}</td>
                      <td style={TD}>{item.work_name}</td>
                      <td style={TD}>{item.hazard_type}</td>
                      <td style={TD}>{item.hazard_detail}</td>
                      <td style={TD}>{item.current_measure}</td>
                      <td style={{ ...TD, textAlign: 'center' }}>{item.possibility}</td>
                      <td style={{ ...TD, textAlign: 'center' }}>{item.severity}</td>
                      <td style={{ ...TD, textAlign: 'center' }}><RiskBadge level={item.current_risk_level} /></td>
                      <td style={TD}>{item.improvement}</td>
                      <td style={{ ...TD, textAlign: 'center' }}>{item.after_possibility}</td>
                      <td style={{ ...TD, textAlign: 'center' }}>{item.after_severity}</td>
                      <td style={{ ...TD, textAlign: 'center' }}><RiskBadge level={item.after_risk_level} /></td>
                      <td style={TD}>{item.manager}</td>
                      <td style={{ ...TD, whiteSpace: 'nowrap' }}>
                        <Btn small color="gray" onClick={() => startEdit(item)}>수정</Btn>{' '}
                        <Btn small color="red"  onClick={() => del(item.id)}>삭제</Btn>
                      </td>
                    </tr>
              ))}
              {adding && (
                <RowForm
                  item={addBuf}
                  onChange={(k, v) => setAddBuf(b => ({ ...b, [k]: v }))}
                  onSave={saveNew}
                  onCancel={() => setAdding(false)} />
              )}
            </tbody>
          </table>
        </div>
        <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
          {!adding && <Btn small color="gray" onClick={() => { setAdding(true); setAddBuf({ ...EMPTY }) }}>+ 행 추가</Btn>}
          {msg && <span style={{ fontSize: '0.82rem', color: msg.startsWith('오류') ? '#dc2626' : '#16a34a' }}>{msg}</span>}
        </div>
      </Card>
    </div>
  )
}
