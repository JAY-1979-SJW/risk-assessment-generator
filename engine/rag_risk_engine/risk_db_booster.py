"""
Risk DB Booster v1.1 — supplements RAG engine output with structured risk_db data.

All operations are ADDITIVE ONLY — never replace or reduce KOSHA retrieval results.
JSON data is loaded lazily and cached at module level (files are small, < 500 KB total).

Connected DBs (this upgrade):
  - scenario/condition_scenarios.json      (30 scenarios)
  - hazard_action/hazard_controls.json     (90 controls)
  - hazard_action/hazard_ppe.json          (54 PPE entries)
  - work_taxonomy/work_types.json          (132 types)
  - work_taxonomy/work_hazards_map.json    (48 mappings)
  - law_standard/safety_laws.json          (51 laws)    ← 2단계 추가
  - law_standard/law_hazard_map.json       (49 mappings)← 2단계 추가
  - law_standard/law_worktype_map.json     (50 mappings)← 2단계 추가
  - law_standard/law_control_map.json      (10 mappings)← 2단계 추가
"""

import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_DB_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'risk_db')
)

# ── Hazard label mapping: Korean classifier labels → risk_db hazard codes ────

HAZARD_KO_TO_CODE: Dict[str, str] = {
    '추락': 'FALL',
    '감전': 'ELEC',
    '질식': 'ASPHYX',
    '화재': 'FIRE',
    '폭발': 'EXPLO',
    '낙하': 'DROP',
    '충돌': 'COLLIDE',
    '붕괴': 'COLLAPSE',
    '협착': 'ENTRAP',
    '절단': 'CUT',
    '중독': 'POISON',
    '분진': 'DUST',
    '소음': 'NOISE',
}

# Hazard code → BM25 query expansion tokens (Korean keyword clusters)
_CODE_TO_QUERY_TERMS: Dict[str, str] = {
    'FALL':     '추락 안전대 안전난간',
    'ASPHYX':   '질식 산소결핍 환기',
    'ELEC':     '감전 전원차단 절연',
    'FIRE':     '화재 소화기 화기통제',
    'EXPLO':    '폭발 가스농도 점화원',
    'DROP':     '낙하물 방지망 안전모',
    'COLLIDE':  '충돌 신호수 작업반경',
    'COLLAPSE': '붕괴 동바리 흙막이',
    'ENTRAP':   '협착 방호장치 잠금',
    'CUT':      '절단 방호덮개 보안경',
    'POISON':   '중독 MSDS 방독마스크',
    'DUST':     '분진 방진마스크 환기',
    'NOISE':    '소음 귀마개 귀덮개',
}

# ── Lazy-loaded data cache ───────────────────────────────────────────────────

_cache: Dict[str, object] = {}


def _load(rel_path: str) -> dict:
    full = os.path.join(_DB_ROOT, rel_path)
    if not os.path.exists(full):
        logger.warning('risk_db 파일 없음: %s', full)
        return {}
    with open(full, 'r', encoding='utf-8') as f:
        return json.load(f)


def _scenarios() -> List[dict]:
    if 'scenarios' not in _cache:
        _cache['scenarios'] = _load('scenario/condition_scenarios.json').get('scenarios', [])
    return _cache['scenarios']  # type: ignore


def _controls_by_code() -> Dict[str, List[dict]]:
    if 'controls' not in _cache:
        idx: Dict[str, List[dict]] = {}
        for item in _load('hazard_action/hazard_controls.json').get('hazard_controls', []):
            idx.setdefault(item['hazard_code'], []).append(item)
        _cache['controls'] = idx
    return _cache['controls']  # type: ignore


def _ppe_by_code() -> Dict[str, List[dict]]:
    if 'ppe' not in _cache:
        idx: Dict[str, List[dict]] = {}
        for item in _load('hazard_action/hazard_ppe.json').get('hazard_ppe', []):
            idx.setdefault(item['hazard_code'], []).append(item)
        _cache['ppe'] = idx
    return _cache['ppe']  # type: ignore


def _work_types() -> List[dict]:
    if 'work_types' not in _cache:
        _cache['work_types'] = _load('work_taxonomy/work_types.json').get('work_types', [])
    return _cache['work_types']  # type: ignore


def _hazard_map() -> Dict[str, List[dict]]:
    if 'hazard_map' not in _cache:
        idx: Dict[str, List[dict]] = {}
        for item in _load('work_taxonomy/work_hazards_map.json').get('mappings', []):
            idx.setdefault(item['work_type_code'], []).append(item)
        _cache['hazard_map'] = idx
    return _cache['hazard_map']  # type: ignore


# ── Law standard DB loaders (2단계) ─────────────────────────────────────────

def _safety_laws() -> Dict[str, dict]:
    """law_code → law entry dict"""
    if 'safety_laws' not in _cache:
        idx: Dict[str, dict] = {}
        for law in _load('law_standard/safety_laws.json').get('laws', []):
            idx[law['law_code']] = law
        _cache['safety_laws'] = idx
    return _cache['safety_laws']  # type: ignore


def _law_hazard_idx() -> Dict[str, List[dict]]:
    """hazard_code → list of law mappings"""
    if 'law_hazard_idx' not in _cache:
        idx: Dict[str, List[dict]] = {}
        for m in _load('law_standard/law_hazard_map.json').get('mappings', []):
            idx.setdefault(m['hazard_code'], []).append(m)
        _cache['law_hazard_idx'] = idx
    return _cache['law_hazard_idx']  # type: ignore


def _law_worktype_idx() -> Dict[str, List[dict]]:
    """work_type_code → list of law mappings"""
    if 'law_worktype_idx' not in _cache:
        idx: Dict[str, List[dict]] = {}
        for m in _load('law_standard/law_worktype_map.json').get('mappings', []):
            for wt_code in m.get('work_type_codes', []):
                idx.setdefault(wt_code, []).append(m)
        _cache['law_worktype_idx'] = idx
    return _cache['law_worktype_idx']  # type: ignore


def _law_control_list() -> List[dict]:
    """Flat list of law_control_map entries"""
    if 'law_control_list' not in _cache:
        _cache['law_control_list'] = _load('law_standard/law_control_map.json').get('mappings', [])
    return _cache['law_control_list']  # type: ignore


# ── Condition flag extraction ─────────────────────────────────────────────────

def _extract_flags(inp: dict) -> Dict[str, object]:
    """Map v2 RagInput fields to scenario trigger_conditions keys."""
    weather = inp.get('weather') or ''
    surface = inp.get('surface_condition') or ''
    height_m = inp.get('height_m') or 0

    weather_cond: Optional[str] = None
    if weather in ('wind', 'extreme'):
        weather_cond = 'wind_strong'
    elif weather in ('rain', 'snow'):
        weather_cond = 'rain'

    return {
        'work_at_height':    bool(inp.get('work_at_height') or height_m > 2),
        'night_work':        bool(inp.get('night_work')),
        'confined_space':    bool(inp.get('confined_space')),
        'hot_work':          bool(inp.get('hot_work')),
        'electrical_work':   bool(inp.get('electrical_work')),
        'heavy_equipment':   bool(inp.get('heavy_equipment')),
        'simultaneous_work': bool(inp.get('simultaneous_work')),
        'wet_surface':       surface in ('wet', 'slippery'),
        'weather_condition': weather_cond,
    }


def _scenario_matches(trigger: dict, flags: dict) -> bool:
    """Return True only when ALL trigger conditions are satisfied by flags."""
    for key, expected in trigger.items():
        if key == 'weather_condition':
            if flags.get('weather_condition') != expected:
                return False
        elif isinstance(expected, bool):
            if not flags.get(key):
                return False
        else:
            # Unknown condition (e.g. flammable_nearby, excavation) — cannot derive from v2
            return False
    return bool(trigger)  # empty trigger never matches


# ── Input-based condition warnings (v2 fields not covered by scenarios) ──────

def build_input_condition_warnings(inp: dict) -> List[str]:
    """Generate warnings for v2 conditions not already captured by scenario matching."""
    warnings: List[str] = []
    surface = inp.get('surface_condition') or ''
    weather = inp.get('weather') or ''
    height_m = inp.get('height_m') or 0
    worker_count = inp.get('worker_count') or 0

    if surface == 'uneven':
        warnings.append('[입력 경고] 고르지 않은 바닥: 이동 경로 정비 및 안전화 착용 확인 필요')
    if weather == 'snow':
        warnings.append('[입력 경고] 적설 환경: 작업 전 제설·결빙 방지 조치 필요')
    if weather == 'extreme':
        warnings.append('[입력 경고] 극한 기상: 폭염·한파 환경 작업자 건강 모니터링 필요')
    if height_m and height_m > 10:
        warnings.append(
            f'[입력 경고] 고소작업 {height_m:.0f}m: '
            '강풍 발생 시 즉시 작업 중지 기준 사전 수립 필요'
        )
    if worker_count >= 10:
        warnings.append(
            f'[입력 경고] 다수 작업자 {worker_count}명: '
            '작업 구역별 안전 담당자 지정 및 TBM 실시 필요'
        )

    return warnings


# ── Public API ───────────────────────────────────────────────────────────────

def match_condition_scenarios(inp: dict) -> List[dict]:
    """Return matched condition scenario dicts for the given input."""
    flags = _extract_flags(inp)
    return [sc for sc in _scenarios() if _scenario_matches(sc.get('trigger_conditions', {}), flags)]


def expand_query_by_taxonomy(inp: dict) -> str:
    """
    Return extra BM25 query tokens derived from work taxonomy hazard mapping.

    Matches sub_work text against work_types names → looks up associated hazard codes
    → returns Korean keyword clusters for those hazards.
    Max 3 hazard type expansions to avoid query dilution.
    """
    sub_work = (inp.get('sub_work') or '').strip()
    if not sub_work:
        return ''

    tokens: List[str] = []
    seen_codes: set = set()

    for wt in _work_types():
        name = wt.get('name_ko', '')
        if name and name in sub_work:
            wt_code = wt['code']
            for mapping in _hazard_map().get(wt_code, []):
                hcode = mapping['hazard_code']
                if hcode not in seen_codes:
                    term = _CODE_TO_QUERY_TERMS.get(hcode, '')
                    if term:
                        tokens.append(term)
                    seen_codes.add(hcode)

    return ' '.join(tokens[:3])


def boost_results(
    inp: dict,
    hazards: List[str],
    existing_actions: List[str],
    existing_ppe: List[str],
    existing_legal: List[str],
) -> dict:
    """
    Compute additive boosts from risk_db.

    Priority order inside each category:
      actions  → scenario_controls (condition-matched) > db_controls (hazard-matched)
      ppe      → mandatory PPE first, then optional
      legal    → scenario law_refs first, then hazard_controls law_refs

    Returns dict with keys:
      scenario_controls      — controls from matched condition_scenarios (up to 4)
      db_controls            — controls from hazard_controls (up to 4)
      db_ppe                 — PPE from hazard_ppe (up to 4)
      db_law_refs            — law refs from scenarios + hazard_controls (up to 4)
      condition_warnings     — critical-priority scenario warnings
      input_warnings         — v2 field-based warnings
      boosted_by_conditions  — matched scenario IDs
      boosted_by_taxonomy    — work type codes used for query expansion
      source_db_refs         — all risk_db record IDs referenced
    """
    # ── 1. Condition scenario matching ────────────────────────────────────────
    matched_scenarios = match_condition_scenarios(inp)
    boosted_by_conditions = [sc['id'] for sc in matched_scenarios]

    existing_actions_set = {a.strip() for a in existing_actions}
    existing_legal_set = {l.strip() for l in existing_legal}

    scenario_controls: List[str] = []
    scenario_law_refs: List[str] = []
    scenario_hazard_codes: List[str] = []
    condition_warnings: List[str] = []

    for sc in matched_scenarios:
        for ctrl in sc.get('recommended_controls', []):
            c = ctrl.strip()
            if c and c not in existing_actions_set and c not in scenario_controls:
                scenario_controls.append(c)
        for ref in sc.get('law_refs', []):
            r = ref.strip()
            if r and r not in existing_legal_set and r not in scenario_law_refs:
                scenario_law_refs.append(r)
        for hcode in sc.get('boosted_hazards', []):
            if hcode not in scenario_hazard_codes:
                scenario_hazard_codes.append(hcode)
        if sc.get('priority') == 'critical':
            condition_warnings.append(f"[조건 경고] {sc['label']}: {sc['description']}")

    # ── 2. Map Korean hazard labels → codes (+ scenario-boosted codes) ────────
    hazard_codes: List[str] = []
    for h in hazards:
        code = HAZARD_KO_TO_CODE.get(h)
        if code and code not in hazard_codes:
            hazard_codes.append(code)
    for code in scenario_hazard_codes:
        if code not in hazard_codes:
            hazard_codes.append(code)

    # ── 3. hazard_controls → supplemental actions + legal refs ───────────────
    controls_idx = _controls_by_code()
    db_controls: List[str] = []
    db_law_refs: List[str] = []

    for code in hazard_codes[:5]:
        for ctrl in sorted(controls_idx.get(code, []), key=lambda x: x.get('priority', 9)):
            text = ctrl['control_text'].strip()
            if text and text not in existing_actions_set and text not in db_controls:
                db_controls.append(text)
            law = ctrl.get('law_ref', '').strip()
            if law and law not in existing_legal_set and law not in scenario_law_refs and law not in db_law_refs:
                db_law_refs.append(law)

    # ── 4. hazard_ppe → supplemental PPE (mandatory first) ───────────────────
    ppe_idx = _ppe_by_code()
    existing_ppe_set = {p.strip() for p in existing_ppe}
    db_ppe: List[str] = []

    for code in hazard_codes[:5]:
        entries = ppe_idx.get(code, [])
        # mandatory first
        for ppe_item in sorted(entries, key=lambda x: not x.get('mandatory', False)):
            name = ppe_item['ppe_name'].strip()
            if name and name not in existing_ppe_set and name not in db_ppe:
                db_ppe.append(name)

    # ── 5. Input-level condition warnings ─────────────────────────────────────
    input_warnings = build_input_condition_warnings(inp)

    # ── 6. Taxonomy expansion (for notes only — actual token added in engine) ──
    boosted_by_taxonomy: List[str] = []
    sub_work = (inp.get('sub_work') or '').strip()
    for wt in _work_types():
        name = wt.get('name_ko', '')
        if name and name in sub_work:
            boosted_by_taxonomy.append(wt['code'])

    return {
        'scenario_controls':     scenario_controls[:4],
        'db_controls':           db_controls[:4],
        'db_ppe':                db_ppe[:4],
        'db_law_refs':           (scenario_law_refs + db_law_refs)[:4],
        'condition_warnings':    condition_warnings,
        'input_warnings':        input_warnings,
        'boosted_by_conditions': boosted_by_conditions,
        'boosted_by_taxonomy':   boosted_by_taxonomy[:3],
        'source_db_refs':        boosted_by_conditions[:],
        'hazard_codes':          hazard_codes,   # 2단계: 법령 연결용 노출
    }


# ── Legal enrichment (2단계) ─────────────────────────────────────────────────

_RELATION_PRIORITY: Dict[str, int] = {'required': 0, 'recommended': 1, 'reference': 2}
_HIGH_RISK_CODES = frozenset({'FALL', 'ELEC', 'FIRE', 'COLLAPSE', 'ASPHYX'})


def build_legal_enrichment(
    hazard_codes: List[str],
    work_type_codes: List[str],
    combined_actions: List[str],
    combined_ppe: List[str],
) -> dict:
    """
    Build legal_basis, law_refs, legal_warnings from law DB.
    Additive-only — does not modify existing results.

    relation_type 우선순위: required > recommended > reference
    동일 law_code가 여러 소스에서 매핑될 경우 높은 우선순위 유지, matched_by 누적.
    """
    laws = _safety_laws()
    hazard_idx = _law_hazard_idx()
    worktype_idx = _law_worktype_idx()
    control_list = _law_control_list()

    # law_code → {'relation_type': str, 'matched_by': set}
    accumulator: Dict[str, dict] = {}

    law_refs: Dict[str, List[str]] = {
        'hazard_refs':    [],
        'work_type_refs': [],
        'control_refs':   [],
    }

    def _upsert(lcode: str, rt: str, source: str, ref_list: List[str]) -> None:
        """Update accumulator with higher-priority relation_type; accumulate matched_by."""
        if lcode not in accumulator:
            accumulator[lcode] = {'relation_type': rt, 'matched_by': {source}}
        else:
            if _RELATION_PRIORITY.get(rt, 2) < _RELATION_PRIORITY.get(
                    accumulator[lcode]['relation_type'], 2):
                accumulator[lcode]['relation_type'] = rt
            accumulator[lcode]['matched_by'].add(source)
        if lcode not in ref_list:
            ref_list.append(lcode)

    # A. Hazard-based
    for hcode in hazard_codes:
        for m in hazard_idx.get(hcode, []):
            _upsert(m['law_code'], m.get('relation_type', 'reference'),
                    'hazard', law_refs['hazard_refs'])

    # B. Work-type-based
    for wt_code in work_type_codes:
        for m in worktype_idx.get(wt_code, []):
            _upsert(m['law_code'], m.get('relation_type', 'reference'),
                    'work_type', law_refs['work_type_refs'])

    # C. Control-text matching
    actions_set = {a.strip() for a in combined_actions}
    for m in control_list:
        if m.get('control_text', '').strip() in actions_set:
            _upsert(m['law_code'], m.get('relation_type', 'reference'),
                    'control', law_refs['control_refs'])

    # Build legal_basis sorted by relation_type priority
    legal_basis = []
    for lcode, info in sorted(
        accumulator.items(),
        key=lambda x: _RELATION_PRIORITY.get(x[1]['relation_type'], 2),
    ):
        entry = laws.get(lcode)
        if not entry:
            continue
        legal_basis.append({
            'law_code':      lcode,
            'law_name':      entry.get('law_name', ''),
            'article_no':    entry.get('article_no', ''),
            'title':         entry.get('title') or entry.get('clause_title', ''),
            'relation_type': info['relation_type'],
            'matched_by':    sorted(info['matched_by']),
        })

    # Legal warnings
    legal_warnings: List[str] = []

    # W1: high-risk hazard with no law mapping
    for hcode in hazard_codes:
        if hcode in _HIGH_RISK_CODES and not hazard_idx.get(hcode):
            legal_warnings.append(
                f'고위험 작업인데 법령 매핑이 없습니다 ({hcode}).'
            )

    # W2: required law mapped but no combined_actions
    required_laws = [lc for lc, v in accumulator.items() if v['relation_type'] == 'required']
    if required_laws and not combined_actions:
        legal_warnings.append('필수 법령 근거가 연결되었으나 대응 안전조치가 부족합니다.')

    # W3: PPE-related required law but no PPE result
    ppe_laws = [lc for lc in law_refs['hazard_refs']
                if '보호구' in (laws.get(lc, {}).get('title', '') +
                               laws.get(lc, {}).get('summary', ''))]
    if ppe_laws and not combined_ppe:
        legal_warnings.append('필수 보호구가 누락되었습니다.')

    # W4: high-risk hazards present but zero law mappings at all
    if hazard_codes and _HIGH_RISK_CODES.intersection(hazard_codes) and not accumulator:
        legal_warnings.append('고위험 작업인데 법령 매핑이 없습니다.')

    return {
        'legal_basis':    legal_basis,
        'law_refs':       law_refs,
        'legal_warnings': legal_warnings,
    }
