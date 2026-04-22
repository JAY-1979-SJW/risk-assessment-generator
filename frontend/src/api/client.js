const BASE = '/api'

async function req(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '요청 실패')
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Projects
  getProjects: ()            => req('GET', '/projects'),
  createProject: (title)     => req('POST', '/projects', { title }),
  getProject: (id)           => req('GET', `/projects/${id}`),
  updateProject: (id, data)  => req('PUT', `/projects/${id}`, data),
  deleteProject: (id)        => req('DELETE', `/projects/${id}`),

  // Company Info
  getCompany: (pid)          => req('GET', `/projects/${pid}/company-info`),
  saveCompany: (pid, data)   => req('PUT', `/projects/${pid}/company-info`, data),

  // Organization
  getOrg: (pid)              => req('GET', `/projects/${pid}/organization`),
  saveOrgBulk: (pid, members)=> req('PUT', `/projects/${pid}/organization/bulk`, members),

  // Assessments
  getAssessments: (pid)      => req('GET', `/projects/${pid}/assessments`),
  addAssessment: (pid, data) => req('POST', `/projects/${pid}/assessments`, data),
  bulkAddAssessments: (pid, items) => req('POST', `/projects/${pid}/assessments/bulk`, items),
  updateAssessment: (pid, id, data) => req('PUT', `/projects/${pid}/assessments/${id}`, data),
  deleteAssessment: (pid, id)=> req('DELETE', `/projects/${pid}/assessments/${id}`),
  clearAssessments: (pid)    => req('DELETE', `/projects/${pid}/assessments`),

  // Forms
  getForm: (pid, type)       => req('GET', `/projects/${pid}/${type}`),
  saveForm: (pid, type, data)=> req('PUT', `/projects/${pid}/${type}`, data),

  // Templates
  getCategories: ()          => req('GET', '/templates/categories'),
  getPolicy: (cat)           => req('GET', `/templates/policy/${cat}`),
  getGoal: (cat)             => req('GET', `/templates/goal/${cat}`),
  getRiskCriteria: ()        => req('GET', '/templates/risk-criteria'),

  // AI Generate
  generateAI: (data)         => req('POST', '/generate', data),

  // Draft Recommend / Recalculate
  draftRecommend:    (data)  => req('POST', '/risk-assessment/draft/recommend', data),
  draftRecalculate:  (data)  => req('POST', '/risk-assessment/draft/recalculate', data),

  // Export
  exportExcel: async (pid) => {
    const r = await fetch(`${BASE}/projects/${pid}/export/excel`)
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: '엑셀 생성 실패' }))
      throw new Error(err.detail || '엑셀 생성 실패')
    }
    return r.blob()
  },
}
