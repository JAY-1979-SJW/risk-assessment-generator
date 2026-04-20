#!/usr/bin/env python3
"""
실 DB 연결 품질 검증 스크립트
Usage:
    python engine/rag_risk_engine/validate_realdb.py
"""

import json
import os
import sys
import time

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)

import psycopg2
import psycopg2.extras

from engine.rag_risk_engine.engine import run_engine
from engine.rag_risk_engine.schema import validate_input

# ── DB 연결 설정 ──────────────────────────────────────────────────────────
KOSHA_DB = dict(
    host='127.0.0.1', port=5435, dbname='common_data',
    user='common_admin', password='XenZ5xmKw5jEf1bWQuU2LxWRZMlJ',
    connect_timeout=5,
)

# ── 20건 테스트 케이스 ────────────────────────────────────────────────────
# 1건: 실 KRAS 데이터, 나머지 19건: KOSHA 커버리지 기반 대표 시나리오
TEST_CASES = [
    # ── 실 데이터 (kras id=1) ─────────────────────────────────────────────
    {
        'id': 'REAL-01',
        'source': 'kras_actual',
        'process': '고소작업',
        'sub_work': '천장 배관 설치',
        'risk_category': '추락',
        'risk_detail': '이동식비계',
        'risk_situation': '이동식 비계에서 천장 배관 설치 작업 중 추락 위험',
        'expected_hazard': '추락',
        'expected_actions_kw': ['안전난간', '안전대', '비계'],
        'expected_ppe_kw': ['안전모', '안전대'],
    },
    # ── 대표 시나리오 (synthetic) ─────────────────────────────────────────
    {
        'id': 'SYN-01',
        'source': 'synthetic',
        'process': '건축 골조',
        'sub_work': '시스템 비계 설치',
        'risk_situation': '시스템 비계 상부에서 작업 중 추락 위험 안전난간 미설치 상태',
        'expected_hazard': '추락',
        'expected_actions_kw': ['안전난간', '안전대', '작업발판'],
        'expected_ppe_kw': ['안전모', '안전대'],
    },
    {
        'id': 'SYN-02',
        'source': 'synthetic',
        'process': '건축 골조',
        'sub_work': '슬래브 거푸집 설치',
        'risk_situation': '거푸집 동바리 불안정으로 인한 붕괴 위험, 동바리 간격 초과',
        'expected_hazard': '붕괴',
        'expected_actions_kw': ['동바리', '거푸집'],
        'expected_ppe_kw': ['안전모'],
    },
    {
        'id': 'SYN-03',
        'source': 'synthetic',
        'process': '건축 철골',
        'sub_work': '기둥 보 접합 작업',
        'risk_situation': '고소 철골 작업 중 볼트 체결 불량으로 부재 낙하 위험',
        'expected_hazard': '추락',
        'expected_actions_kw': ['안전망', '안전대'],
        'expected_ppe_kw': ['안전모', '안전대'],
    },
    {
        'id': 'SYN-04',
        'source': 'synthetic',
        'process': '전기 설비',
        'sub_work': '분전반 배선 교체',
        'risk_situation': '분전반 내부 활선 상태 배선 작업 중 감전 위험, 전원 차단 미실시',
        'expected_hazard': '감전',
        'expected_actions_kw': ['전원 차단', 'LOTO', '절연'],
        'expected_ppe_kw': ['절연장갑'],
    },
    {
        'id': 'SYN-05',
        'source': 'synthetic',
        'process': '토목 하수도',
        'sub_work': '맨홀 내부 점검',
        'risk_situation': '밀폐공간 맨홀 내부 작업 중 산소 결핍 및 황화수소 질식 위험',
        'expected_hazard': '질식',
        'expected_actions_kw': ['공기호흡기', '환기', '감시인'],
        'expected_ppe_kw': ['공기호흡기'],
    },
    {
        'id': 'SYN-06',
        'source': 'synthetic',
        'process': '배관 설치',
        'sub_work': '파이프 용접 작업',
        'risk_situation': '용접 작업 중 불꽃 비산으로 인근 가연성 자재 화재 발생 위험',
        'expected_hazard': '화재',
        'expected_actions_kw': ['소화기', '가연', '방화'],
        'expected_ppe_kw': ['방염복', '안전모'],
    },
    {
        'id': 'SYN-07',
        'source': 'synthetic',
        'process': '토공 굴착',
        'sub_work': '지반 굴착 작업',
        'risk_situation': '흙막이 미설치 구간 굴착 작업 중 지반 붕괴 위험',
        'expected_hazard': '붕괴',
        'expected_actions_kw': ['흙막이', '굴착'],
        'expected_ppe_kw': ['안전모', '안전화'],
    },
    {
        'id': 'SYN-08',
        'source': 'synthetic',
        'process': '양중 작업',
        'sub_work': '타워크레인 중량물 인양',
        'risk_situation': '크레인 인양 중 와이어 파단 또는 슬링 탈락으로 중량물 낙하 충돌 위험',
        'expected_hazard': '낙하',
        'expected_actions_kw': ['신호수', '반경'],
        'expected_ppe_kw': ['안전모'],
    },
    {
        'id': 'SYN-09',
        'source': 'synthetic',
        'process': '건축 해체',
        'sub_work': '구조물 해체 작업',
        'risk_situation': '콘크리트 구조물 해체 중 구조물 붕괴 전도 위험',
        'expected_hazard': '붕괴',
        'expected_actions_kw': ['해체', '순서'],
        'expected_ppe_kw': ['안전모'],
    },
    {
        'id': 'SYN-10',
        'source': 'synthetic',
        'process': '건축 외장',
        'sub_work': '지붕 방수 시공',
        'risk_situation': '경사 지붕면 방수 작업 중 미끄럼 추락 위험',
        'expected_hazard': '추락',
        'expected_actions_kw': ['추락방지망', '안전대', '안전난간'],
        'expected_ppe_kw': ['안전모', '안전대'],
    },
    {
        'id': 'SYN-11',
        'source': 'synthetic',
        'process': '건축 마감',
        'sub_work': '외벽 도장 작업',
        'risk_situation': '인화성 유기 용제 사용 도장 작업 중 화재 폭발 위험 환기 불량',
        'expected_hazard': '화재',
        'expected_actions_kw': ['환기', '점화원', '소화기'],
        'expected_ppe_kw': ['방독마스크'],
    },
    {
        'id': 'SYN-12',
        'source': 'synthetic',
        'process': '화학설비',
        'sub_work': '유해화학물질 취급',
        'risk_situation': '유해화학물질 취급 작업 MSDS 미숙지 보호구 미착용 피부 호흡기 노출 중독',
        'expected_hazard': '중독',
        'expected_actions_kw': ['MSDS', '보호구', '환기'],
        'expected_ppe_kw': ['방독마스크', '장갑'],
    },
    {
        'id': 'SYN-13',
        'source': 'synthetic',
        'process': '철근 콘크리트',
        'sub_work': '철근 절단 작업',
        'risk_situation': '회전 절단날을 이용한 철근 절단 중 날 접촉 절단 위험',
        'expected_hazard': '절단',
        'expected_actions_kw': ['덮개', '보호', '방호'],
        'expected_ppe_kw': ['안전모', '보안경'],
    },
    {
        'id': 'SYN-14',
        'source': 'synthetic',
        'process': '설비 배관',
        'sub_work': '배관 압력 시험',
        'risk_situation': '배관 수압 시험 중 배관 이음부 파열 충격 파편 위험',
        'expected_hazard': '폭발',
        'expected_actions_kw': ['압력', '점검'],
        'expected_ppe_kw': ['안전모', '보안경'],
    },
    {
        'id': 'SYN-15',
        'source': 'synthetic',
        'process': '전기 공사',
        'sub_work': '전동공구 사용 작업',
        'risk_situation': '습윤 환경에서 전동공구 사용 중 누전 감전 위험 이중 절연 미확인',
        'expected_hazard': '감전',
        'expected_actions_kw': ['이중 절연', '누전 차단기', '절연'],
        'expected_ppe_kw': ['절연장갑'],
    },
    {
        'id': 'SYN-16',
        'source': 'synthetic',
        'process': '비계 공사',
        'sub_work': '외부 비계 해체',
        'risk_situation': '외부 비계 해체 작업 중 비계 부재 낙하 하부 작업자 충돌 위험',
        'expected_hazard': '낙하',
        'expected_actions_kw': ['낙하물 방지망', '통제', '신호'],
        'expected_ppe_kw': ['안전모', '안전대'],
    },
    {
        'id': 'SYN-17',
        'source': 'synthetic',
        'process': '지하 굴착',
        'sub_work': '도시가스관 인근 굴착',
        'risk_situation': '지하 매설 가스관 인근 굴착 작업 중 가스관 파손 가스 누출 폭발 위험',
        'expected_hazard': '폭발',
        'expected_actions_kw': ['가스', '탐지', '환기'],
        'expected_ppe_kw': ['안전모'],
    },
    {
        'id': 'SYN-18',
        'source': 'synthetic',
        'process': '고소 작업차',
        'sub_work': 'MEWP 고소작업대 작업',
        'risk_situation': '고소작업대 탑승 작업 중 과부하 또는 경사지 전도로 인한 추락 위험',
        'expected_hazard': '추락',
        'expected_actions_kw': ['고소작업대', '안전대', '과부하'],
        'expected_ppe_kw': ['안전모', '안전대'],
    },
    {
        'id': 'SYN-19',
        'source': 'synthetic',
        'process': '콘크리트 타설',
        'sub_work': '콘크리트 펌프카 운용',
        'risk_situation': '콘크리트 펌프카 붐대 작동 중 붕대 전도 낙하 충돌 위험',
        'expected_hazard': '충돌',
        'expected_actions_kw': ['반경', '통제', '신호수'],
        'expected_ppe_kw': ['안전모'],
    },
]


# ── 품질 평가 로직 ─────────────────────────────────────────────────────────

def evaluate_result(case: dict, result: dict) -> dict:
    """각 결과에 대한 품질 판정 (GOOD / ACCEPTABLE / FAIL)"""
    issues = []
    grade = 'GOOD'

    # 1) 검색 결과 존재 여부
    chunk_ids = result.get('source_chunk_ids', [])
    if not chunk_ids:
        issues.append('NO_RESULTS: 검색 결과 없음')
        grade = 'FAIL'

    # 2) hazard 일치 여부
    expected_hazard = case.get('expected_hazard', '')
    primary_hazards = result.get('primary_hazards', [])
    hazard_matched = any(
        expected_hazard in h or h in expected_hazard
        for h in primary_hazards
    ) if expected_hazard else True
    if not hazard_matched:
        issues.append(f'HAZARD_MISMATCH: 기대={expected_hazard}, 실제={primary_hazards}')
        if grade == 'GOOD':
            grade = 'ACCEPTABLE'

    # 3) recommended_actions 존재 및 관련성
    actions = result.get('recommended_actions', [])
    if not actions:
        issues.append('NO_ACTIONS: 대책 없음')
        if grade == 'GOOD':
            grade = 'ACCEPTABLE'
    else:
        expected_kw = case.get('expected_actions_kw', [])
        actions_text = ' '.join(actions)
        matched_kw = [kw for kw in expected_kw if kw in actions_text]
        if expected_kw and not matched_kw:
            issues.append(f'ACTIONS_MISMATCH: 기대키워드={expected_kw} 미포함, 실제={actions[:3]}')
            if grade == 'GOOD':
                grade = 'ACCEPTABLE'

    # 4) PPE 존재 여부
    ppe = result.get('required_ppe', [])
    if not ppe:
        issues.append('NO_PPE: 보호구 없음')
        if grade == 'GOOD':
            grade = 'ACCEPTABLE'

    # 5) confidence
    confidence = result.get('confidence', 'low')
    if confidence == 'low' and grade != 'FAIL':
        issues.append(f'LOW_CONFIDENCE')
        if grade == 'GOOD':
            grade = 'ACCEPTABLE'

    # 6) warnings 확인
    warnings = result.get('warnings', [])
    for w in warnings:
        if '없음' in w or '편향' in w or '낮음' in w:
            issues.append(f'WARNING: {w[:60]}')

    # 최종 판정: FAIL 조건 재검토
    if not chunk_ids:
        grade = 'FAIL'
    elif grade == 'ACCEPTABLE' and len([i for i in issues if 'FAIL' not in i]) >= 3:
        grade = 'FAIL'

    return {
        'id': case['id'],
        'source': case['source'],
        'grade': grade,
        'confidence': confidence,
        'chunk_count': len(chunk_ids),
        'hazard_matched': hazard_matched,
        'actions_count': len(actions),
        'ppe_count': len(ppe),
        'legal_count': len(result.get('legal_basis_candidates', [])),
        'issues': issues,
        'primary_hazards': primary_hazards,
        'top_actions': actions[:3],
        'top_ppe': ppe[:3],
    }


# ── KOSHA 청크 로드 ────────────────────────────────────────────────────────

def load_kosha_chunks() -> list:
    print('[STEP 1] KOSHA DB에서 청크 로드 중...')
    conn = psycopg2.connect(**KOSHA_DB)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    kmc.id,
                    kmc.normalized_text,
                    kmc.raw_text,
                    kmc.work_type,
                    kmc.hazard_type,
                    kmc.control_measure,
                    kmc.ppe,
                    kmc.law_ref,
                    kmc.keywords,
                    kct.trade_type,
                    kct.confidence AS tag_confidence
                FROM kosha_material_chunks kmc
                LEFT JOIN kosha_chunk_tags kct ON kct.chunk_id = kmc.id
                WHERE (kmc.normalized_text IS NOT NULL OR kmc.raw_text IS NOT NULL)
                LIMIT 5000
            """)
            rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    # 통계
    total = len(rows)
    tagged = sum(1 for r in rows if r.get('work_type') or r.get('hazard_type'))
    has_law = sum(1 for r in rows if r.get('law_ref'))
    has_control = sum(1 for r in rows if r.get('control_measure'))
    has_ppe = sum(1 for r in rows if r.get('ppe'))

    # work_type distribution
    from collections import Counter
    wt_counter = Counter(r.get('work_type') for r in rows if r.get('work_type'))
    ht_counter = Counter(r.get('hazard_type') for r in rows if r.get('hazard_type'))

    print(f'  총 청크: {total}')
    print(f'  태그 보유(work/hazard): {tagged} ({tagged/total*100:.1f}%)')
    print(f'  law_ref 있음: {has_law} ({has_law/total*100:.1f}%)')
    print(f'  control_measure 있음: {has_control} ({has_control/total*100:.1f}%)')
    print(f'  ppe 있음: {has_ppe} ({has_ppe/total*100:.1f}%)')
    print(f'  work_type top5: {wt_counter.most_common(5)}')
    print(f'  hazard_type top5: {ht_counter.most_common(5)}')
    print()

    return rows, {
        'total': total,
        'tagged': tagged,
        'has_law': has_law,
        'has_control': has_control,
        'has_ppe': has_ppe,
        'work_type_top5': wt_counter.most_common(5),
        'hazard_type_top5': ht_counter.most_common(5),
    }


# ── 메인 실행 ─────────────────────────────────────────────────────────────

def main():
    print('=' * 70)
    print('RAG Risk Engine v1 - Real DB Quality Validation')
    print('=' * 70)

    # Step 1: 청크 로드
    chunks, db_stats = load_kosha_chunks()

    # Step 2 & 3: 20건 실행
    print('[STEP 2/3] 20건 테스트 실행 중...')
    results_raw = []
    evals = []

    for i, case in enumerate(TEST_CASES, 1):
        inp = {
            'process': case['process'],
            'sub_work': case['sub_work'],
            'risk_situation': case['risk_situation'],
            'risk_category': case.get('risk_category'),
            'risk_detail': case.get('risk_detail'),
            'top_k': 10,
        }
        try:
            result = run_engine(inp, chunks)
            ev = evaluate_result(case, result)
            evals.append(ev)
            results_raw.append({'case_id': case['id'], 'input': inp, 'output': result})
            status = f"[{ev['grade']:10s}] {ev['confidence']:6s} chunks={ev['chunk_count']:2d} hz={ev['hazard_matched']}"
            case_id = case['id']
            print(f'  [{i:2d}/20] {case_id:9s} {status}')
            if ev['issues']:
                for iss in ev['issues'][:2]:
                    print(f'          => {iss}')
        except Exception as e:
            case_id = case['id']
            print(f'  [{i:2d}/20] {case_id:9s} ERROR: {e}')
            evals.append({'id': case['id'], 'source': case['source'], 'grade': 'FAIL',
                         'issues': [f'EXCEPTION: {e}'], 'confidence': 'low',
                         'chunk_count': 0, 'hazard_matched': False})

    print()

    # Step 4 & 5: 품질 분석
    print('[STEP 4/5] 품질 분석...')
    grade_counts = {'GOOD': 0, 'ACCEPTABLE': 0, 'FAIL': 0}
    fail_patterns = {
        'NO_RESULTS': 0, 'HAZARD_MISMATCH': 0, 'NO_ACTIONS': 0,
        'NO_PPE': 0, 'LOW_CONFIDENCE': 0, 'ACTIONS_MISMATCH': 0,
    }
    for ev in evals:
        grade_counts[ev['grade']] += 1
        for iss in ev.get('issues', []):
            for pat in fail_patterns:
                if pat in iss:
                    fail_patterns[pat] += 1

    total_cases = len(evals)
    good_pct = grade_counts['GOOD'] / total_cases * 100
    acc_pct = grade_counts['ACCEPTABLE'] / total_cases * 100
    fail_pct = grade_counts['FAIL'] / total_cases * 100

    print(f'  GOOD:       {grade_counts["GOOD"]:2d}/{total_cases} ({good_pct:.0f}%)')
    print(f'  ACCEPTABLE: {grade_counts["ACCEPTABLE"]:2d}/{total_cases} ({acc_pct:.0f}%)')
    print(f'  FAIL:       {grade_counts["FAIL"]:2d}/{total_cases} ({fail_pct:.0f}%)')
    print()
    print('  실패 패턴별 집계:')
    for pat, cnt in sorted(fail_patterns.items(), key=lambda x: -x[1]):
        if cnt > 0:
            print(f'    {pat:22s}: {cnt}건')
    print()

    # Step 6: 품질 판정
    if fail_pct <= 15 and good_pct + acc_pct >= 85:
        overall = 'GOOD'
    elif fail_pct <= 35:
        overall = 'ACCEPTABLE'
    else:
        overall = 'FAIL'

    print(f'[STEP 6] 최종 품질 판정: {overall}')
    print()

    # Step 7: 개선 항목
    print('[STEP 7] 개선 필요 항목:')
    issues_summary = []

    # work_type 분포 분석
    wt_top = db_stats['work_type_top5']
    if wt_top and wt_top[0][1] > db_stats['total'] * 0.5:
        top_wt = wt_top[0][0]
        top_cnt = wt_top[0][1]
        pct = top_cnt / db_stats['total'] * 100
        issues_summary.append(
            f'[데이터] work_type "{top_wt}" {top_cnt}건 ({pct:.1f}%) 과편향 - '
            '청크 재분류 필요'
        )

    ht_top = db_stats['hazard_type_top5']
    if ht_top and ht_top[0][0] in ('위험', '위험요인', '유해'):
        issues_summary.append(
            f'[데이터] hazard_type "{ht_top[0][0]}" {ht_top[0][1]}건 무의미 태그 - '
            '분류 기준 재정의 필요'
        )

    if fail_patterns['HAZARD_MISMATCH'] > 2:
        issues_summary.append(
            f'[검색] hazard_type 필드 불일치 {fail_patterns["HAZARD_MISMATCH"]}건 - '
            '쿼리 확장 또는 타입 매핑 보완'
        )
    if fail_patterns['NO_RESULTS'] > 0:
        issues_summary.append(
            f'[검색] 검색 결과 없음 {fail_patterns["NO_RESULTS"]}건 - '
            '토크나이저 개선 또는 코퍼스 확충 필요'
        )
    if fail_patterns['LOW_CONFIDENCE'] > 5:
        issues_summary.append(
            f'[엔진] confidence low {fail_patterns["LOW_CONFIDENCE"]}건 - '
            'tag_ratio 기준 완화 검토 (현재 데이터 태그율 낮음)'
        )
    if fail_patterns['ACTIONS_MISMATCH'] > 3:
        issues_summary.append(
            '[엔진] control_measure 텍스트 부정확 - '
            'chunking 품질 개선 또는 조합 로직 보강'
        )

    for iss in issues_summary:
        print(f'  {iss}')

    if not issues_summary:
        print('  (특이 이슈 없음)')
    print()

    # 결과 파일 저장
    out_path = os.path.join(os.path.dirname(__file__), 'validation_results.json')
    report = {
        'db_stats': db_stats,
        'grade_summary': grade_counts,
        'overall_verdict': overall,
        'fail_patterns': fail_patterns,
        'issues_summary': issues_summary,
        'case_evaluations': evals,
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f'결과 저장: {out_path}')
    print('=' * 70)


if __name__ == '__main__':
    main()
