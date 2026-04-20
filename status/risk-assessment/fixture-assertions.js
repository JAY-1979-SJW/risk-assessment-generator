// fixture-assertions.js — Node.js assertion runner for Action Recommendation logic
// Run: node status/risk-assessment/fixture-assertions.js

const SOURCES = ['git_guard', 'self_check', 'backup_check', 'restore_rehearsal'];

function normalizeEvent(e) {
  if (e.source === 'git_guard' && e.verdict === 'FAIL' &&
      e.summary && e.summary.includes('dirty_type=mode_only')) {
    return { ...e, normalized: 'WARN', noiseType: 'mode_only' };
  }
  return { ...e, normalized: e.verdict, noiseType: null };
}

function calcOverall(allData) {
  const now = Date.now(), h24 = now - 24 * 60 * 60 * 1000, reasons = [];
  const recent24 = {};
  for (const src of SOURCES)
    recent24[src] = (allData[src] || []).filter(e => new Date(e.ts).getTime() >= h24).map(normalizeEvent);
  const nFails = {}, nWarns = {};
  for (const src of SOURCES) {
    nFails[src] = recent24[src].filter(e => e.normalized === 'FAIL').length;
    nWarns[src] = recent24[src].filter(e => e.normalized === 'WARN').length;
  }
  const totalFails = Object.values(nFails).reduce((a, b) => a + b, 0);
  const totalWarns = Object.values(nWarns).reduce((a, b) => a + b, 0);
  function lastNFail(src, n) {
    const items = (allData[src] || []).slice(-n).map(normalizeEvent);
    return items.length >= n && items.every(e => e.normalized === 'FAIL');
  }
  if (lastNFail('self_check', 2)) reasons.push('self_check 연속 FAIL 2회');
  if (lastNFail('backup_check', 2)) reasons.push('backup_check 연속 FAIL 2회');
  if (lastNFail('restore_rehearsal', 2)) reasons.push('restore_rehearsal 연속 FAIL 2회');
  const failingSrcs = SOURCES.filter(s => nFails[s] >= 2);
  if (failingSrcs.length >= 2) reasons.push('복수 source 동시 FAIL');
  if (reasons.length > 0) return { overall: 'INCIDENT', reasons, totalFails, totalWarns };
  const degReasons = [];
  for (const src of ['self_check', 'backup_check', 'restore_rehearsal'])
    if (lastNFail(src, 2)) degReasons.push(src + ' 연속 FAIL');
  if (nFails['git_guard'] > 0) degReasons.push('git_guard FAIL');
  if (totalWarns >= 5) degReasons.push('WARN 누적');
  if (totalFails > 0 && degReasons.length === 0) degReasons.push('FAIL ' + totalFails + '회');
  if (degReasons.length > 0) return { overall: 'DEGRADED', reasons: degReasons, totalFails, totalWarns };
  return { overall: 'HEALTHY', reasons: [], totalFails: 0, totalWarns };
}

function calcAction(allData, overallResult) {
  const { overall } = overallResult;
  const allNorm = {};
  for (const src of SOURCES) allNorm[src] = (allData[src] || []).map(normalizeEvent);
  const restoreFail = allNorm['restore_rehearsal'].slice(-2).some(e => e.normalized === 'FAIL');
  const gitContentDirty = allNorm['git_guard'].slice(-3).some(e => e.normalized === 'FAIL' && e.noiseType !== 'mode_only');
  const backupFail = allNorm['backup_check'].slice(-2).every(e => e.normalized === 'FAIL') && allNorm['backup_check'].length >= 2;
  const now = Date.now(), h24 = now - 24 * 60 * 60 * 1000;
  const failSrcs = SOURCES.filter(src =>
    allNorm[src].filter(e => new Date(e.ts).getTime() >= h24 && e.normalized === 'FAIL').length >= 2
  );
  const aprReasons = [], aprIdSet = new Set();
  if (restoreFail)          { aprReasons.push('restore_rehearsal FAIL'); aprIdSet.add('APR-003'); aprIdSet.add('APR-004'); }
  if (gitContentDirty)      { aprReasons.push('git content dirty'); aprIdSet.add('APR-001'); aprIdSet.add('APR-004'); }
  if (backupFail)           { aprReasons.push('backup_check 연속 FAIL'); aprIdSet.add('APR-003'); aprIdSet.add('APR-004'); }
  if (failSrcs.length >= 2) { aprReasons.push('복수 source 동시 FAIL'); aprIdSet.add('APR-002'); aprIdSet.add('APR-003'); aprIdSet.add('APR-004'); }
  if (aprReasons.length > 0) {
    const templates = [];
    if (gitContentDirty)           templates.push('git 이상 대응 템플릿 (§ A)');
    if (restoreFail || backupFail) templates.push('데이터 복구 대응 템플릿 (§ C)');
    if (!templates.length)         templates.push('git 이상 대응 템플릿 (§ A) / 데이터 복구 대응 템플릿 (§ C)');
    return { action: 'APPROVAL-REQUIRED', approval: true, step: '대표님 승인 후 복구/정렬 절차 진행', reasons: aprReasons, actionIds: [...aprIdSet].slice(0, 4), priority: 'high', nextTemplate: templates.join(' / ') };
  }
  const svcRepeatFail = allNorm['self_check'].slice(-2).every(e => e.normalized === 'FAIL') && allNorm['self_check'].length >= 2;
  if (svcRepeatFail) return { action: 'AUTO-RECOVERY-CANDIDATE', approval: false, step: '원인 확인 후 최소 범위 재기동 후보', reasons: ['self_check 2회 연속 FAIL'], actionIds: ['ARC-001', 'ARC-002', 'ARC-003'], priority: 'medium', nextTemplate: '서비스 이상 대응 템플릿 (§ B)' };
  return { action: 'OBSERVE', approval: false, step: '상태 추적 유지, 즉시 조치 없음', reasons: overall === 'HEALTHY' ? ['서비스 정상'] : overallResult.reasons.slice(0, 2), actionIds: ['OBS-001', 'OBS-002', 'OBS-003'], priority: 'low', nextTemplate: null };
}

function ev(source, verdict, minsAgo, summary) {
  return { source, verdict, summary: summary || '', ts: new Date(Date.now() - minsAgo * 60000).toISOString() };
}

const fixtures = {
  observe: {
    git_guard:         [ev('git_guard','PASS',120), ev('git_guard','PASS',60), ev('git_guard','PASS',5)],
    self_check:        [ev('self_check','PASS',120), ev('self_check','PASS',60), ev('self_check','PASS',5)],
    backup_check:      [ev('backup_check','PASS',120), ev('backup_check','PASS',60)],
    restore_rehearsal: [ev('restore_rehearsal','PASS',240), ev('restore_rehearsal','PASS',120)],
  },
  arc: {
    git_guard:         [ev('git_guard','PASS',120), ev('git_guard','PASS',5)],
    self_check:        [ev('self_check','PASS',240), ev('self_check','FAIL',120), ev('self_check','FAIL',60)],
    backup_check:      [ev('backup_check','PASS',120), ev('backup_check','PASS',60)],
    restore_rehearsal: [ev('restore_rehearsal','PASS',240), ev('restore_rehearsal','PASS',120)],
  },
  apr: {
    git_guard:         [ev('git_guard','PASS',120), ev('git_guard','PASS',5)],
    self_check:        [ev('self_check','PASS',120), ev('self_check','PASS',60)],
    backup_check:      [ev('backup_check','PASS',120), ev('backup_check','PASS',60)],
    restore_rehearsal: [ev('restore_rehearsal','FAIL',120), ev('restore_rehearsal','FAIL',60)],
  },
};

const results = {};
for (const [key, data] of Object.entries(fixtures)) {
  const overall = calcOverall(data);
  const action  = calcAction(data, overall);
  results[key]  = { overall, action };
}

const obs = results.observe.action;
const arc = results.arc.action;
const apr = results.apr.action;

const checks = [];
function check(label, cond) { checks.push({ label, pass: !!cond }); }

check('OBSERVE: action=OBSERVE',              obs.action === 'OBSERVE');
check('ARC: action=AUTO-RECOVERY-CANDIDATE',  arc.action === 'AUTO-RECOVERY-CANDIDATE');
check('APR: action=APPROVAL-REQUIRED',        apr.action === 'APPROVAL-REQUIRED');
check('OBSERVE: ids=[OBS-001,002,003]',        JSON.stringify(obs.actionIds) === JSON.stringify(['OBS-001','OBS-002','OBS-003']));
check('ARC: ids=[ARC-001,002,003]',            JSON.stringify(arc.actionIds) === JSON.stringify(['ARC-001','ARC-002','ARC-003']));
check('APR: ids include APR-003',              apr.actionIds.includes('APR-003'));
check('APR: ids include APR-004',              apr.actionIds.includes('APR-004'));
check('OBSERVE: priority=low',                 obs.priority === 'low');
check('ARC: priority=medium',                  arc.priority === 'medium');
check('APR: priority=high',                    apr.priority === 'high');
check('APR: nextTemplate has § C',             apr.nextTemplate && apr.nextTemplate.includes('§ C'));
check('OBSERVE: nextTemplate=null',            obs.nextTemplate === null);
check('ARC: nextTemplate has § B',             arc.nextTemplate && arc.nextTemplate.includes('§ B'));
check('ARC: no § A in nextTemplate',           arc.nextTemplate && !arc.nextTemplate.includes('§ A'));
check('ARC: no § C in nextTemplate',           arc.nextTemplate && !arc.nextTemplate.includes('§ C'));
check('APR: no § B in nextTemplate',           apr.nextTemplate && !apr.nextTemplate.includes('§ B'));
check('APR: approval=true',                    apr.approval === true);
check('OBSERVE: approval=false',               obs.approval === false);
check('ARC: approval=false',                   arc.approval === false);

const passed = checks.filter(c => c.pass).length;
const failed  = checks.filter(c => !c.pass).length;
console.log('\n' + (failed === 0 ? 'PASS' : 'FAIL') + ' -- ' + passed + '/' + checks.length + ' checks passed\n');
checks.forEach(c => console.log('  ' + (c.pass ? 'PASS' : 'FAIL') + '  ' + c.label));
console.log('');
process.exit(failed > 0 ? 1 : 0);
