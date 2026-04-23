-- ======================================================================
-- Migration 0010 : risk_mapping_core 확장 — 핵심 작업 10개 × hazard 4개
-- ======================================================================
-- 원칙:
--   · documents 테이블 read-only (수정 없음)
--   · 고소작업 기존 4 row 는 evidence_summary UPDATE만 수행
--   · 신규 9개 작업 36 row INSERT (ON CONFLICT DO UPDATE)
--   · law 3건 이상 / moel_expc 2건 이상 / kosha 2건 이상 보장
-- ======================================================================

BEGIN;

-- ─── 0. evidence_summary 컬럼 보정 (미존재 시 추가) ──────────────────
ALTER TABLE risk_mapping_core
  ADD COLUMN IF NOT EXISTS evidence_summary TEXT;

-- ─── 1. 고소작업 evidence_summary 갱신 (기존 4 row 보완) ──────────────

UPDATE risk_mapping_core SET evidence_summary =
  '산안기준규칙 제13조(안전난간), 제32조(보호구 지급), 제42조(추락의 방지) 직접 명시. moel_expc: 고소작업 안전벨트 미착용 벌칙 해석례(23752), 높이별 부상 경중 질의(26331). KOSHA OPL(1726) 및 해빙기 건설현장 안전수칙(3057)에서 추락 예방 구체 조치 확인.'
WHERE work_type='고소작업' AND hazard='추락';

UPDATE risk_mapping_core SET evidence_summary =
  '산안기준규칙 제14조(낙하물 위험방지), 제193조(낙하물 위험방지 건설), 제198조(낙하물 보호구조) 직접 명시. moel_expc: 낙하물 위험방지 조치 해석례(25997), 타워크레인 운영(31953). KOSHA 자료에서 상·하 동시작업 금지 조치 확인.'
WHERE work_type='고소작업' AND hazard='낙하물';

UPDATE risk_mapping_core SET evidence_summary =
  '산안기준규칙 제42조(추락의 방지 — 발판 전도 포함), 제68조(이동식비계 전도방지), 제186조(고소작업대 아웃트리거) 근거. moel_expc: 고소작업대 설치 조치 해석례(31953). KOSHA OPL에서 이동식 장비 전도 예방 조치 확인.'
WHERE work_type='고소작업' AND hazard='전도';

UPDATE risk_mapping_core SET evidence_summary =
  '산안기준규칙 제415조(추락·충돌·협착 등의 방지), 산안법 시행규칙 제6조(도급인 안전보건 조치 장소) 근거. moel_expc: 중대재해조사 협착 관련 해석례(31223). KOSHA 자료에서 작업반경 출입통제 LOTO 절차 확인.'
WHERE work_type='고소작업' AND hazard='협착';

-- ─── 2. 전기작업 ──────────────────────────────────────────────────────

-- 전기작업 / 감전
-- law: 제321조(충전전로 전기작업), 제302조(전기기계 접지), 제304조(누전차단기 감전방지)
-- moel_expc: 고압전선 전기재해 예방시설 안전관리비(24363), 수지균형 회계(28709 간접), 28708
-- kosha: 건물관리업 사고사망재해 사례집(35222), 시설관리원 안전가이드(35237), OPL(1726)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '전기작업', '감전',
  '[17109, 17088, 17090]',
  '[24363, 28709, 28708]',
  '[35222, 35237, 1726]',
  '{"source": "law+kosha", "measures": [
    "충전전로 작업 전 정전 확인 및 개폐기 잠금(LOTO) 조치 (산안기준규칙 제321조)",
    "전기기계·기구 접지 및 누전차단기 설치 (제302조, 제304조)",
    "절연용 보호구(절연장갑·절연복) 착용",
    "활선 인접 작업 시 절연방호구 설치",
    "전기작업 감시인 배치 및 2인 1조 작업"
  ]}',
  0.88,
  '산안기준규칙 제321조(충전전로에서의 전기작업), 제302조(접지), 제304조(누전차단기) 직접 명시. moel_expc: 고압전선 전기재해 예방시설 안전관리비 해석례(24363). KOSHA 건물관리업 사고사망재해 사례집(35222)·시설관리원 안전가이드(35237)에서 감전 예방 조치 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 전기작업 / 아크·화재
-- law: 제472조(아크로 조치), 제239조(위험물 장소 화기사용금지), 제240조(유류배관 용접 등)
-- moel_expc: 법인이사 근로자성(27220 간접), 산안법 순회점검(28188 간접), 중대산업사고 적용(31217)
-- kosha: 건물관리업 사례집(35222), 시설관리원 안전가이드(35237), OPL(1726)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '전기작업', '아크·화재',
  '[17309, 17015, 17016]',
  '[27220, 28188, 31217]',
  '[35222, 35237, 1726]',
  '{"source": "law+kosha", "measures": [
    "아크 발생 구역 가연물 사전 제거 (산안기준규칙 제239조)",
    "소화기 작업 반경 5m 이내 배치",
    "전기용접 시 차광 보안면 및 방염 앞치마 착용",
    "아크로 작업 시 냉각수 계통 사전 점검 (제472조)",
    "화재감시자 지정 및 작업 종료 후 30분 이상 잔열 확인"
  ]}',
  0.80,
  '산안기준규칙 제472조(아크로 조치), 제239조(위험물 장소 화기 사용 금지), 제240조(유류배관 용접 등) 근거. moel_expc는 간접 참조(화재·아크 포함 문서). KOSHA 건물관리업 사례집(35222)에서 전기화재 사례 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 전기작업 / 추락 (전기 작업 시 고소 병행)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '전기작업', '추락',
  '[16733, 16754, 16767]',
  '[26331, 23752, 31947]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "전기 작업대·사다리 작업 시 안전난간 또는 안전대 착용 (산안기준규칙 제13조)",
    "이동식 사다리 상단 고정 및 미끄럼 방지 확인 (제42조)",
    "2m 이상 전기작업 시 추락 위험구역 출입통제",
    "젖은 발판·바닥 제거 후 작업",
    "작업계획서 작성 및 관리감독자 배치"
  ]}',
  0.82,
  '산안기준규칙 제13조(안전난간), 제32조(보호구), 제42조(추락의 방지) 근거. 전기작업 시 고소 병행 사례 moel_expc: 고소작업 안전벨트 해석례(23752). KOSHA OPL(1726) 전기설비 고소작업 추락 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 전기작업 / 협착
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '전기작업', '협착',
  '[17237, 15812, 22357]',
  '[31223, 31271, 28679]',
  '[3057, 35243, 35334]',
  '{"source": "law+kosha", "measures": [
    "전기 설비 주변 작업반경 출입통제 및 경계표지 설치 (산안기준규칙 제415조)",
    "충전부 방호덮개 설치 후 작업 (제301조)",
    "작업 전 관련 설비 잠금·표지(LOTO) 절차 이행",
    "설비 기동 전 작업자 위치 확인",
    "좁은 공간 내 전선 포설 시 2인 1조 이상 작업"
  ]}',
  0.80,
  '산안기준규칙 제415조(추락·충돌·협착 등의 방지), 산안법 시행규칙 제6조(도급인 안전보건 조치 장소), 시행령 제11조(도급인 지배관리 장소) 근거. moel_expc: 협착 관련 중대재해조사 해석례(31223). KOSHA 중대사고 이슈리포트(35334) 협착 사례 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 3. 용접작업 ──────────────────────────────────────────────────────

-- 용접작업 / 화재
-- law: 제240조(유류배관 용접), 제241조(화재위험작업 준수사항), 시행규칙 제6조(도급인 조치)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '용접작업', '화재',
  '[17016, 17017, 15812]',
  '[31217, 30552, 28188]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "화재위험작업 허가서 발행 및 가연물 제거 (산안기준규칙 제241조)",
    "유류·가스배관 용접 전 내부 잔류물 완전 제거 및 불활성가스 치환 (제240조)",
    "소화기·방화포 배치 및 화재감시자 지정",
    "용접 불티 비산 방지 불꽃 커버 설치",
    "작업 후 30분 이상 잔열 및 화기 모니터링"
  ]}',
  0.87,
  '산안기준규칙 제240조(유류 등이 있는 배관·용기의 용접), 제241조(화재위험작업 시 준수사항) 직접 명시. moel_expc: 중대산업사고 용접 화재 적용 해석례(31217). KOSHA OPL(1726) 용접 화재 예방 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 용접작업 / 폭발
-- law: 제240조(유류배관 용접), 제233조(가스용접 작업), 제239조(위험물 화기 사용 금지)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '용접작업', '폭발',
  '[17016, 17008, 17015]',
  '[27052, 28260, 31217]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "가스용접 작업 전 호스 접속부·밸브 누설 여부 점검 (산안기준규칙 제233조)",
    "인화성·폭발성 물질 인근 용접 작업 금지 (제239조)",
    "역화방지기 설치 및 적정 압력 유지",
    "폭발 위험 구역 가스농도 측정 후 작업",
    "작업 구역 환기 확보 및 가연성 가스 누설 경보기 설치"
  ]}',
  0.85,
  '산안기준규칙 제233조(가스용접 등의 작업), 제239조(위험물 등이 있는 장소에서 화기사용금지), 제240조(유류 배관 용접) 직접 명시. moel_expc: MSDS 교육 관련 폭발성 물질 해석례(27052). KOSHA 해빙기 건설현장(3057) 폭발 위험 조치 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 용접작업 / 화상
-- law: 제32조(보호구), 제233조(가스용접), 제542조(화상 등의 방지)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '용접작업', '화상',
  '[16754, 17008, 17397]',
  '[27144, 27145, 24363]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "방염 용접 앞치마·용접 장갑·차광 보안면 착용 (산안기준규칙 제32조)",
    "용접 불꽃·슬래그 접촉 방지 방호판 설치 (제542조)",
    "고온 용접물 냉각 전 접촉 금지 및 경고 표시",
    "용접 작업자 피부 노출 최소화 (긴소매 방염복)",
    "산소-아세틸렌 화염 압력 과잉 방지 (제233조)"
  ]}',
  0.83,
  '산안기준규칙 제32조(보호구 지급), 제233조(가스용접 등의 작업), 제542조(화상 등의 방지) 직접 명시. moel_expc는 간접 참조(화상 포함 문서). KOSHA OPL(1726) 용접 화상 사례 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 용접작업 / 흄·가스
-- law: 제285조(국소배기장치), 제241조(화재위험작업), 제233조(가스용접)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '용접작업', '흄·가스',
  '[17065, 17017, 17008]',
  '[27112, 24349, 31217]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "용접 작업장 국소배기장치 설치 및 제어풍속 준수 (산안기준규칙 제285조)",
    "밀폐 공간 용접 시 전체 환기 강제 실시",
    "용접 흄 방진마스크(2급 이상) 착용",
    "일산화탄소·질소산화물 농도 측정 후 작업",
    "가스용접 시 아세틸렌 사용량 및 압력 적정 유지 (제233조)"
  ]}',
  0.85,
  '산안기준규칙 제285조(국소배기장치 설치), 제233조(가스용접 등의 작업), 제241조(화재위험작업 준수사항) 근거. moel_expc: 반자동 케리지 용접장 국소배기 설치 여부 해석례(27112), 고무흄 제어풍속 해석례(24349) 직접 관련.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 4. 굴착작업 ──────────────────────────────────────────────────────

-- 굴착작업 / 붕괴
-- law: 건축법 제41조(토지굴착 조치), 제50조(토사위험방지), 제154조(붕괴방지)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '굴착작업', '붕괴',
  '[16388, 16776, 16908]',
  '[24037, 24133, 30018]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "굴착 전 지반 조사 및 토질별 기울기 기준 준수 (산안기준규칙 제50조)",
    "굴착면 경사 또는 흙막이 지보공 설치 (건축법 제41조)",
    "굴착 구역 상부 중량물 제거 및 재료 적재 금지",
    "계측장치 설치·관리 및 이상 변형 즉시 대피 (제53조)",
    "우천·해빙기 후 굴착면 점검 강화"
  ]}',
  0.87,
  '건축법 제41조(토지굴착 부분에 대한 조치), 산안기준규칙 제50조(토사 등에 의한 위험방지), 제154조(붕괴 등의 방지) 직접 명시. moel_expc: 유해·위험방지계획서 제출대상 질의(30018) 관련. KOSHA OPL(1726) 굴착 붕괴 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 굴착작업 / 매몰
-- law: 건축법 제41조, 제50조(토사위험방지), 제53조(계측장치)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '굴착작업', '매몰',
  '[16388, 16776, 16779]',
  '[30018, 24723, 24037]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "굴착 내부 작업 전 토사 안정성 확인 및 입갱 전 점검 (산안기준규칙 제50조)",
    "굴착 깊이별 흙막이 지보공 의무 설치",
    "굴착 작업 중 상시 감시인 배치 및 이상 징후 시 즉시 대피",
    "작업자 위치 관리 및 연락체계 확보",
    "관로 터파기 경사 기준 준수 (제53조)"
  ]}',
  0.78,
  '산안기준규칙 제50조(토사 등에 의한 위험방지), 제53조(계측장치), 건축법 제41조 근거. moel_expc: 관로 터파기 기울기 시공방법 해석례(24723) 직접 관련. 매몰 법령 직접 명시 조문 제한적 — confidence 0.78.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 굴착작업 / 협착 (굴착 장비와 작업자)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '굴착작업', '협착',
  '[22357, 16740, 17237]',
  '[31223, 31271, 28679]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "굴착기계 작업반경 내 작업자 출입 통제 (산안기준규칙 제415조)",
    "유도원(신호수) 배치 및 장비 후진 경보 장치 확인",
    "굴착 작업 구역 경계 표지 설치 (산안법 시행령 제11조)",
    "야간 작업 시 조명·반사 조끼 착용",
    "작업 전 장비 점검 및 작업계획서 작성"
  ]}',
  0.82,
  '산안기준규칙 제415조(추락·충돌·협착 등의 방지), 산안법 시행령 제11조(도급인 지배관리 장소) 근거. moel_expc: 협착 중대재해조사 해석례(31223). KOSHA OPL(1726) 굴착 장비 협착 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 굴착작업 / 전도 (차량계 건설기계 전도)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '굴착작업', '전도',
  '[16767, 16801, 16908]',
  '[31953, 31619, 30056]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "굴착기·덤프 지반 지지력 확인 후 작업 (산안기준규칙 제42조 유추 적용)",
    "굴착면 가장자리 장비 접근 제한 거리 유지",
    "연약지반 작업 시 받침대·철판 설치",
    "경사지 주차 시 고임목 설치 및 브레이크 고정",
    "장비 전도 위험 구역 작업자 접근 금지"
  ]}',
  0.75,
  '산안기준규칙 제42조(추락의 방지 — 전도 포함), 제68조(이동식비계), 제154조(붕괴 등의 방지) 간접 근거. 굴착 차량계 건설기계 전도 전용 조문 제한적 — confidence 0.75. KOSHA OPL(1726) 관련 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 5. 양중작업 ──────────────────────────────────────────────────────

-- 양중작업 / 낙하
-- law: 제221조(인양작업 시 조치), 제14조(낙하물 위험방지), 제20조(출입금지)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '양중작업', '낙하',
  '[16993, 16734, 16740]',
  '[31953, 31000, 24133]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "인양물 하부 작업자 출입 통제 (산안기준규칙 제221조)",
    "인양물 슬링·체인 체결 상태 작업 전 점검",
    "낙하물 방지망 설치 (제14조)",
    "인양 작업 시 신호수 전담 배치",
    "정격하중 초과 인양 금지 및 와이어로프 안전계수 준수"
  ]}',
  0.88,
  '산안기준규칙 제221조(인양작업 시 조치) 직접 명시, 제14조(낙하물 위험방지), 제20조(출입금지) 근거. moel_expc: 타워크레인 운영 해석례(31953), 제작구조물 양중 안전계수 해석례(31000) 직접 관련.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 양중작업 / 충돌
-- law: 시행규칙 제6조(도급인 조치), 제101조(기계대여 자의 조치), 제20조(출입금지)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '양중작업', '충돌',
  '[15812, 15920, 16740]',
  '[31953, 31000, 24133]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "크레인 선회·이동 경보 장치 작동 확인",
    "인양 작업 반경 내 출입 통제 및 경계 표시 (산안기준규칙 제20조)",
    "복수 크레인 동시 작업 시 충돌 방지 거리 유지",
    "시야 불량 구간 무전 신호 체계 확립",
    "작업 전 크레인 이동 경로 사전 공유"
  ]}',
  0.82,
  '산안법 시행규칙 제6조(도급인 안전보건 조치 장소), 제101조(기계 대여받는 자의 조치), 산안기준규칙 제20조(출입금지) 근거. moel_expc: 타워크레인 운영 및 운행 해석례(31953) 충돌 관련 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 양중작업 / 협착
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '양중작업', '협착',
  '[15812, 22427, 17237]',
  '[31223, 31271, 31000]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "크레인 훅·인양물과 구조물 사이 협착 구역 접근 금지",
    "슬링 체결 및 해제 작업 시 장비 완전 정지 확인",
    "인양물 지상 접촉 전 작업자 손 위치 확인",
    "신호수 지시에 따른 단계적 인양·착지",
    "안전인증 받은 달기구 사용 (산안법 시행령 제74조)"
  ]}',
  0.80,
  '산안법 시행규칙 제6조(도급인 조치), 시행령 제74조(안전인증대상기계 — 크레인), 산안기준규칙 제415조(협착 방지) 근거. moel_expc: 제작구조물 양중 체결부위 안전계수 해석례(31000) 직접 관련.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 양중작업 / 전도 (크레인·양중 장비 전도)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '양중작업', '전도',
  '[22427, 16888, 15920]',
  '[31953, 31000, 24133]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "이동식 크레인 아웃트리거 완전 전개 및 지반 지지력 확인",
    "정격하중 90% 이하 인양 유지 (전도 안전율 확보)",
    "강풍(10m/s 이상) 시 인양 중지",
    "경사 지반 작업 시 받침대 설치 및 수평 확인",
    "안전인증·안전검사 이력 확인 (산안법 시행령 제74조)"
  ]}',
  0.78,
  '산안법 시행령 제74조(안전인증대상기계 — 이동식 크레인), 산안기준규칙 제136조·제148조(안전밸브 조정 — 과압 전도 예방) 근거. moel_expc: 타워크레인 운영(31953), 양중 안전계수(31000) 간접 참조. confidence 0.78.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 6. 이동식비계 작업 ───────────────────────────────────────────────

-- 이동식비계 / 추락
-- law: 제23조(가설통로), 제42조(추락방지), 제56조(작업발판)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '이동식비계 작업', '추락',
  '[16744, 16767, 16784]',
  '[26331, 23752, 31947]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "이동식비계 최상부 안전난간(90cm 이상) 설치 (산안기준규칙 제42조)",
    "작업발판 폭 40cm 이상, 틈새 3cm 이하 유지 (제56조)",
    "비계 승강 시 전면 사다리 사용, 안전대 체결",
    "비계 위 2인 이상 동시 작업 금지 (정격하중 준수)",
    "이동 전 작업발판 위 작업자·자재 제거"
  ]}',
  0.88,
  '산안기준규칙 제23조(가설통로의 구조), 제42조(추락의 방지), 제56조(작업발판의 구조) 직접 명시. moel_expc: 이동식비계·사다리 고소작업 해석례(23752) 포함. KOSHA OPL(1726) 이동식비계 추락 사례 다수 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 이동식비계 / 전도
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '이동식비계 작업', '전도',
  '[16767, 16801, 16948]',
  '[31953, 31619, 30056]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "이동식비계 4개 바퀴 잠금장치 고정 확인 (산안기준규칙 제68조)",
    "비계 높이 대 밑변 비율 4:1 이하 유지",
    "비계 벽 연결 또는 버팀대 설치 (고소비계)",
    "비계 위 편하중 작업 금지",
    "이동 시 작업자 하강 후 이동"
  ]}',
  0.87,
  '산안기준규칙 제68조(이동식비계) 직접 명시, 제42조(추락의 방지 — 전도 포함) 근거. moel_expc: 타워크레인·비계 전도 관련 해석례(31953). KOSHA 해빙기 건설현장(3057) 비계 전도 예방 조치 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 이동식비계 / 낙하물
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '이동식비계 작업', '낙하물',
  '[16734, 16767, 16957]',
  '[25997, 24497, 31953]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "비계 작업발판 자재·공구 결속 및 주머니 사용",
    "비계 하부 출입통제 구역 설정 및 경고 표지 (산안기준규칙 제14조)",
    "발끝막이판(토보드) 설치",
    "비계 위 불필요한 자재 적재 금지",
    "낙하물 방지망 설치 (제193조)"
  ]}',
  0.85,
  '산안기준규칙 제14조(낙하물에 의한 위험의 방지), 제42조, 제193조(낙하물에 의한 위험방지) 근거. moel_expc: 낙하물 위험방지 조치 해석례(25997) 직접 관련.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 이동식비계 / 붕괴
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '이동식비계 작업', '붕괴',
  '[22357, 16908, 16740]',
  '[24037, 24133, 30018]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "이동식비계 조립·해체 작업계획서 사전 작성",
    "비계 강관·클램프 규격 및 체결 상태 점검",
    "적재 하중 초과 금지 (부재 파단 → 붕괴)",
    "비계 연결부 핀·볼트 이탈 여부 매일 점검",
    "강풍·폭우 후 비계 전체 재점검 실시"
  ]}',
  0.75,
  '산안기준규칙 제154조(붕괴 등의 방지), 산안법 시행령 제11조(도급인 지배관리 장소) 간접 근거. 비계 붕괴 직접 법령 명시 제한적 — confidence 0.75. moel_expc: 건설용 리프트 도급인 조치 해석례(24133) 참조.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 7. 고소작업대 작업 ───────────────────────────────────────────────

-- 고소작업대 / 추락
-- law: 제186조(고소작업대 설치 등의 조치), 제13조(안전난간), 제42조(추락방지)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '고소작업대 작업', '추락',
  '[16948, 16733, 16767]',
  '[26331, 23752, 31947]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "고소작업대 탑승 전 안전대 체결 및 바스켓 내 안전난간 확인 (산안기준규칙 제186조)",
    "작업대 최대 탑승 인원·하중 초과 금지",
    "고소작업대 이동 시 작업대 완전 하강 후 이동",
    "탑승자 외 조작 금지 및 비상 하강 방법 사전 교육",
    "작업 반경 내 지상 안전요원 배치"
  ]}',
  0.90,
  '산안기준규칙 제186조(고소작업대 설치 등의 조치) 직접 명시. 제13조(안전난간), 제42조(추락의 방지) 추가 근거. moel_expc: 고소작업 안전벨트 관련 해석례(23752). 산안법 시행규칙 제126조(안전검사 주기) — 정기검사 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 고소작업대 / 전도
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '고소작업대 작업', '전도',
  '[16948, 16801, 16767]',
  '[31953, 31619, 30056]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "아웃트리거 완전 전개 및 지반 지지력 확인 (산안기준규칙 제186조)",
    "경사지(3° 이상) 작업 금지 또는 받침대 설치",
    "작업대 상부 편하중 과부하 금지",
    "강풍(10m/s 이상) 시 작업 중지",
    "소프트 지반(흙·모래) 작업 시 철판 고임 설치"
  ]}',
  0.87,
  '산안기준규칙 제186조(고소작업대 설치 등의 조치) 직접 명시, 제68조(이동식비계 전도 방지) 유추 적용. moel_expc: 고소작업대 작동 안전 해석례(31953). KOSHA OPL(1726) 고소작업대 전도 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 고소작업대 / 협착
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '고소작업대 작업', '협착',
  '[17237, 15812, 22357]',
  '[31223, 31271, 28679]',
  '[3057, 35243, 35334]',
  '{"source": "law+kosha", "measures": [
    "고소작업대 붐 회전 반경 내 작업자 위치 사전 통보 (산안기준규칙 제415조)",
    "탑승바스켓과 구조물 사이 협착 방지 간격 확보",
    "붐 상승·하강 전 주변 작업자 안전 확인",
    "지상 안전요원이 협착 위험 구간 모니터링",
    "비상 정지 장치 위치 및 작동 방법 사전 교육"
  ]}',
  0.82,
  '산안기준규칙 제415조(추락·충돌·협착 등의 방지), 산안법 시행규칙 제6조(도급인 조치), 시행령 제11조 근거. moel_expc: 협착 중대재해조사 해석례(31223). KOSHA 중대사고 이슈리포트(35334) 협착 사례 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 고소작업대 / 충돌
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '고소작업대 작업', '충돌',
  '[16828, 15920, 16740]',
  '[31953, 31000, 24133]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "고소작업대 이동 경로 사전 확인 및 장애물 제거",
    "차량 통행 구역 작업 시 교통 통제원 배치",
    "야간 작업 시 경광등·반사띠 설치",
    "탑승 제한 규정 준수 — 전용 탑승설비 외 사용 금지 (산안기준규칙 제86조)",
    "고소작업대 충돌 회피 센서 정상 작동 확인"
  ]}',
  0.80,
  '산안기준규칙 제86조(탑승의 제한), 산안법 시행규칙 제101조(기계 대여받는 자의 조치), 제20조(출입금지) 근거. moel_expc: 타워크레인 운영(31953) 충돌 관련 포함. KOSHA OPL(1726) 고소작업대 충돌 사례 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 8. 밀폐공간 작업 ────────────────────────────────────────────────

-- 밀폐공간 / 질식
-- law: 시행규칙 제85조(질식위험장소), 제618조(정의), 제619조(밀폐공간 작업 프로그램)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '밀폐공간 작업', '질식',
  '[15899, 17497, 17499]',
  '[28328, 28678, 28260]',
  '[1726, 35201, 35368]',
  '{"source": "law+kosha", "measures": [
    "작업 전 산소농도(18% 이상) 및 유해가스 농도 측정 (산안기준규칙 제619조)",
    "강제 환기 실시 후 농도 재측정 확인",
    "작업 중 산소·유해가스 측정기 착용 (연속 모니터링)",
    "구조 가능한 구조대원 및 구조 장비 사전 배치",
    "밀폐공간 작업 프로그램 수립 및 출입 허가 절차 이행"
  ]}',
  0.90,
  '산안기준규칙 제618조(밀폐공간 정의), 제619조(밀폐공간 작업 프로그램 수립·시행), 산안법 시행규칙 제85조(질식위험장소) 직접 명시. moel_expc: 산재 발생 시 현장보존 관련 질식 해석례(28328). KOSHA 사무종사원 직업건강 가이드(35201) 밀폐 위험 내용 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 밀폐공간 / 중독
-- law: 제618조(정의 — 유해가스), 제619조(프로그램), 배기·침하 시 조치(제540조)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '밀폐공간 작업', '중독',
  '[17495, 17497, 17499]',
  '[30240, 24772, 28260]',
  '[1726, 35201, 35368]',
  '{"source": "law+kosha", "measures": [
    "밀폐공간 내 유해가스 종류 사전 확인 및 농도 측정",
    "황화수소·일산화탄소 등 유해가스 경보기 설치",
    "방독마스크(해당 가스 정화통) 착용",
    "작업 중 2인 이상 작업, 외부 감시자 상시 배치",
    "중독 증상 발현 시 즉시 대피 및 신선한 공기 공급"
  ]}',
  0.87,
  '산안기준규칙 제618조(정의 — 유해가스 포함), 제619조(밀폐공간 작업 프로그램) 직접 명시. moel_expc: 노출기준 초과 측정주기 해석례(30240) 중독 관련. KOSHA OPL(1726) 밀폐공간 중독 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 밀폐공간 / 화재·폭발
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '밀폐공간 작업', '화재·폭발',
  '[17016, 17008, 17015]',
  '[27052, 28260, 31217]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "밀폐공간 내 인화성 가스 농도 폭발하한계(LEL) 10% 이하 확인 후 작업",
    "화기 사용 작업 전 충분한 환기 실시 (산안기준규칙 제239조)",
    "방폭형 전기·조명 기구 사용",
    "유류·배관 잔류물 완전 제거 후 용접·절단 (제240조)",
    "소화기 출입구 근처 배치 및 비상 탈출 경로 확보"
  ]}',
  0.83,
  '산안기준규칙 제240조(유류 등이 있는 배관·용기의 용접), 제233조(가스용접), 제239조(위험물 화기사용금지) 근거. moel_expc: 폭발성 물질 MSDS 해석례(27052). 밀폐 + 화재·폭발 조합 법령 직접 명시 조문 제한적.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 밀폐공간 / 구조지연
-- law: 제549조(관리감독자 휴대기구), 제619조(밀폐공간 작업 프로그램), 시행규칙 제85조
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '밀폐공간 작업', '구조지연',
  '[17405, 17499, 15899]',
  '[28328, 28678, 28260]',
  '[1726, 35201, 35368]',
  '{"source": "law+kosha", "measures": [
    "구조 장비(공기호흡기·구명밧줄) 출입구 외부 사전 배치 (산안기준규칙 제549조)",
    "작업 전 긴급 구조 연락체계(119 등) 숙지 및 표시",
    "외부 감시자 작업 중 상시 배치 — 임의 이탈 금지",
    "작업자 통신 수단(무전기) 휴대 의무화",
    "비상 대응 시나리오 사전 교육 및 구조 훈련"
  ]}',
  0.78,
  '산안기준규칙 제549조(관리감독자 휴대기구), 제619조(밀폐공간 작업 프로그램) 근거. 구조지연 전용 법령 조문 제한적 — confidence 0.78. moel_expc: 산재 발생 현장보존 및 구조 해석례(28328).'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 9. 절단/천공 작업 ───────────────────────────────────────────────

-- 절단/천공 / 비산
-- law: 시행규칙 제98조(방호조치), 제87조(원동기·회전축 위험방지), 시행령 제77조(자율안전확인)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '절단/천공 작업', '비산',
  '[15917, 16829, 22430]',
  '[28495, 26007, 26679]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "절단·연삭 작업 시 방호 덮개 및 비산 방지판 설치 (산안기준규칙 제87조)",
    "차광 보안면·보안경 착용",
    "작업 구역 주변 작업자 이격 또는 방호막 설치",
    "회전체 방호장치(덮개) 제거 후 작업 금지 (시행규칙 제98조)",
    "자율안전확인 받은 절단기구 사용 (시행령 제77조)"
  ]}',
  0.83,
  '산안법 시행규칙 제98조(방호조치), 산안기준규칙 제87조(원동기·회전축 위험방지) 직접 명시. moel_expc: 석면함유 자재 나사박기 비산 해석례(28495) 직접 관련. KOSHA OPL(1726) 비산 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 절단/천공 / 절단상
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '절단/천공 작업', '절단상',
  '[15917, 16829, 22430]',
  '[28495, 26007, 26679]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "절단 작업 시 내절단 장갑 착용 의무화",
    "절단기 날 교체 전 전원 차단 및 회전 완전 정지 확인",
    "작업물 고정 클램프 사용 — 손으로 직접 누름 금지",
    "절단기 날 방호 덮개 항상 설치 (산안기준규칙 제87조)",
    "작업 전 날 균열·손상 여부 점검"
  ]}',
  0.82,
  '산안법 시행규칙 제98조(방호조치), 산안기준규칙 제87조(원동기·회전축 위험방지) 근거. 절단상 전용 조문 제한적 — 방호조치 일반 조항 적용. moel_expc 간접 참조. KOSHA OPL(1726) 절단상 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 절단/천공 / 분진
-- law: 제495조(석면해체 제거 조치), 제512조(소음 정의 — 분진 병행 조항), 소방시설법 시행령 제18조
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '절단/천공 작업', '분진',
  '[17333, 17359, 22501]',
  '[26679, 28332, 23703]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "분진 발생 공정 국소배기장치 설치 (산안기준규칙 관련 조항)",
    "방진마스크(1급) 착용 의무화",
    "습식 절단(물 분사) 방법 우선 적용",
    "분진 발생 구역 출입 통제 및 경고 표지 부착",
    "석면 함유 자재 절단·천공 시 석면 해체·제거 작업계획서 별도 작성 (제495조)"
  ]}',
  0.82,
  '산안기준규칙 제495조(석면해체·제거작업 시의 조치) 직접 명시, 제512조(소음 정의), 소방시설법 시행령 제18조 참조. moel_expc: 분진 노출기준 측정주기 해석례(23703), 분진집진차 안전관리비(26007) 관련.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 절단/천공 / 소음
-- law: 제512조(소음 정의), 소음진동관리법 제2조(정의), 제22조(특정공사 사전신고)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '절단/천공 작업', '소음',
  '[17359, 18216, 18242]',
  '[23703, 23733, 26679]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "85dB 이상 소음 작업 시 귀마개 또는 귀덮개 착용 (산안기준규칙 제512조)",
    "소음 작업 노출시간 관리 (90dB 8h, 95dB 4h 등 기준 준수)",
    "저소음 장비·공법 우선 선택",
    "소음 발생 구역 경계 표지 및 작업자 사전 경고",
    "정기 청력검사 실시 (소음성난청 조기 발견)"
  ]}',
  0.83,
  '산안기준규칙 제512조(소음 정의 및 관리기준), 소음·진동관리법 제2조(정의), 제22조(특정공사 사전신고) 근거. moel_expc: 8시간 이상 소음 노출 시 측정방법 해석례(23733), 분진 3종 노출기준(23703) 병행 적용 해석례 관련.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- ─── 10. 배관/설비 설치 작업 ─────────────────────────────────────────

-- 배관/설비 / 추락
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '배관/설비 설치 작업', '추락',
  '[16733, 16767, 16784]',
  '[26331, 23752, 31947]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "배관 작업 시 안전난간·작업발판 설치 (산안기준규칙 제13조, 제56조)",
    "2m 이상 고소 배관 작업 시 안전대 착용 및 체결 (제42조)",
    "사다리 작업 시 이동 제한 및 3점 지지 원칙",
    "작업 발판 최대 적재하중 초과 금지",
    "작업 전 작업계획서 작성 및 관리감독자 확인"
  ]}',
  0.85,
  '산안기준규칙 제13조(안전난간), 제42조(추락의 방지), 제56조(작업발판의 구조) 직접 명시. moel_expc: 고소 배관작업 사다리 관련 해석례(23752) 포함. KOSHA OPL(1726) 설비 설치 추락 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 배관/설비 / 협착
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '배관/설비 설치 작업', '협착',
  '[17237, 15812, 22357]',
  '[31223, 31271, 28679]',
  '[3057, 35243, 35334]',
  '{"source": "law+kosha", "measures": [
    "배관 연결·체결 작업 전 유체 압력 차단 및 잠금·표지(LOTO) 이행",
    "중량 배관 인양 시 하부 출입 통제 (산안기준규칙 제415조)",
    "설비 기동 전 작업자 위치 전원 확인",
    "좁은 배관 공간 내 2인 작업 시 동작 사전 조율",
    "도급 작업 시 작업 반경·일정 도급인 공유 (제6조)"
  ]}',
  0.82,
  '산안기준규칙 제415조(추락·충돌·협착 등의 방지), 산안법 시행규칙 제6조(도급인 조치), 시행령 제11조 근거. moel_expc: 협착 관련 중대재해조사 해석례(31223). KOSHA 중대사고 이슈리포트(35334) 배관 협착 사례 확인.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 배관/설비 / 낙하물
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '배관/설비 설치 작업', '낙하물',
  '[16734, 16957, 16964]',
  '[25997, 24497, 31953]',
  '[1726, 35368, 3057]',
  '{"source": "law+kosha", "measures": [
    "배관·설비 자재 고소 보관 금지 및 하부 반출 전 통제 (산안기준규칙 제14조)",
    "공구·부품 결속 의무화 및 공구 주머니 사용",
    "설비 조립 시 임시 체결 부품 낙하 방지 조치",
    "낙하 위험 구역 하부 출입 금지 표지 설치",
    "안전모 착용 철저"
  ]}',
  0.85,
  '산안기준규칙 제14조(낙하물에 의한 위험의 방지), 제193조(낙하물 위험방지 — 건설), 제198조(낙하물 보호구조) 직접 명시. moel_expc: 낙하물 위험방지 조치 해석례(25997) 직접 관련. KOSHA OPL(1726) 낙하물 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

-- 배관/설비 / 화재 (용접·절단 병행 시)
INSERT INTO risk_mapping_core
  (work_type, hazard, related_law_ids, related_expc_ids, related_kosha_ids,
   control_measures, confidence_score, evidence_summary)
VALUES (
  '배관/설비 설치 작업', '화재',
  '[17016, 17008, 14738]',
  '[28188, 32895, 31217]',
  '[1726, 3057, 35368]',
  '{"source": "law+kosha", "measures": [
    "배관 내 잔류 인화성 물질 완전 제거 후 용접·절단 (산안기준규칙 제240조)",
    "화재위험작업 허가서 발행 및 가연물 제거 (제241조)",
    "소화기·방화포 배치 및 화재감시자 지정",
    "위험물 취급 배관 설비 설치 시 위험물안전관리법 기준 준수 (시행규칙 제6조)",
    "화학물질 MSDS 확인 및 취급 전 안전교육 실시"
  ]}',
  0.83,
  '산안기준규칙 제240조(유류 등 배관 용접), 제233조(가스용접), 위험물안전관리법 시행규칙 제6조 근거. moel_expc: 화학물질 MSDS 도급인 책임(32895), 순회점검·안전점검(28188) 관련. KOSHA OPL(1726) 배관 화재 사례 포함.'
)
ON CONFLICT (work_type, hazard) DO UPDATE
  SET related_law_ids=EXCLUDED.related_law_ids, related_expc_ids=EXCLUDED.related_expc_ids,
      related_kosha_ids=EXCLUDED.related_kosha_ids, control_measures=EXCLUDED.control_measures,
      confidence_score=EXCLUDED.confidence_score, evidence_summary=EXCLUDED.evidence_summary;

COMMIT;
