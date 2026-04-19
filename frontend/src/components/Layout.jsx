import React from 'react'

const S = {
  wrap: { minHeight: '100vh', background: '#f8fafc', fontFamily: 'Pretendard,-apple-system,sans-serif', color: '#1e293b' },
  nav: { background: '#1e3a5f', color: '#fff', padding: '0 1.5rem', display: 'flex', alignItems: 'center', height: 52, gap: 16 },
  navTitle: { fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.01em' },
  navSub: { fontSize: '0.75rem', color: '#94a3b8' },
  body: { maxWidth: 1100, margin: '0 auto', padding: '1.5rem 1rem' },
}

export default function Layout({ children, title, subtitle, actions }) {
  return (
    <div style={S.wrap}>
      <nav style={S.nav}>
        <div>
          <div style={S.navTitle}>KRAS 위험성평가표 자동생성기</div>
          {subtitle && <div style={S.navSub}>{subtitle}</div>}
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>{actions}</div>
      </nav>
      <div style={S.body}>{children}</div>
    </div>
  )
}

export function Card({ children, title, style }) {
  return (
    <div style={{ background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0', padding: '1.25rem', marginBottom: '1rem', ...style }}>
      {title && <div style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.75rem', color: '#334155' }}>{title}</div>}
      {children}
    </div>
  )
}

export function Btn({ children, onClick, color = 'blue', small, disabled, type = 'button' }) {
  const colors = {
    blue:   { bg: '#2563eb', text: '#fff' },
    green:  { bg: '#16a34a', text: '#fff' },
    red:    { bg: '#dc2626', text: '#fff' },
    gray:   { bg: '#f1f5f9', text: '#334155' },
    purple: { bg: '#7c3aed', text: '#fff' },
  }
  const c = colors[color] || colors.blue
  return (
    <button type={type} onClick={onClick} disabled={disabled} style={{
      padding: small ? '0.3rem 0.7rem' : '0.45rem 1rem',
      background: disabled ? '#e2e8f0' : c.bg,
      color: disabled ? '#94a3b8' : c.text,
      border: 'none', borderRadius: 6, cursor: disabled ? 'not-allowed' : 'pointer',
      fontSize: small ? '0.78rem' : '0.85rem', fontWeight: 600,
    }}>{children}</button>
  )
}

export function Input({ label, value, onChange, placeholder, type = 'text', required }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {label && <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569' }}>
        {label}{required && <span style={{ color: '#dc2626' }}> *</span>}
      </span>}
      <input type={type} value={value} onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{ padding: '0.4rem 0.6rem', border: '1px solid #cbd5e1', borderRadius: 6,
          fontSize: '0.875rem', outline: 'none', width: '100%', boxSizing: 'border-box' }} />
    </label>
  )
}

export function Textarea({ label, value, onChange, rows = 3, placeholder }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {label && <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569' }}>{label}</span>}
      <textarea value={value} onChange={e => onChange(e.target.value)} rows={rows}
        placeholder={placeholder}
        style={{ padding: '0.4rem 0.6rem', border: '1px solid #cbd5e1', borderRadius: 6,
          fontSize: '0.875rem', outline: 'none', resize: 'vertical', fontFamily: 'inherit' }} />
    </label>
  )
}

export function Select({ label, value, onChange, options }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {label && <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#475569' }}>{label}</span>}
      <select value={value} onChange={e => onChange(e.target.value)}
        style={{ padding: '0.4rem 0.6rem', border: '1px solid #cbd5e1', borderRadius: 6, fontSize: '0.875rem' }}>
        {options.map(o => <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>)}
      </select>
    </label>
  )
}

export function RiskBadge({ level }) {
  const colors = { 높음: '#dc2626', 보통: '#d97706', 낮음: '#16a34a' }
  const bg     = { 높음: '#fef2f2', 보통: '#fffbeb', 낮음: '#f0fdf4' }
  return (
    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: colors[level] || '#64748b',
      background: bg[level] || '#f8fafc', padding: '0.15rem 0.5rem', borderRadius: 999 }}>
      {level}
    </span>
  )
}
