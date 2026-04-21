"""
위험성평가표 초안 생성 API 테스트
대상:
  POST /api/risk-assessment/draft/recommend
  POST /api/risk-assessment/draft/recalculate

실행: pytest tests/test_risk_assessment_draft_api.py -v
"""
import sys
import os
from pathlib import Path

# backend/ 경로를 sys.path에 추가 (라우터/서비스 임포트용)
_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND))

import pytest
from fastapi.testclient import TestClient

# main.py 임포트 (DB 의존성 없이 TestClient 사용)
os.environ.setdefault("DATABASE_URL", "")
os.environ.setdefault("COMMON_DATA_URL", "")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("INTERNAL_API_KEY", "")

from main import app

client = TestClient(app, raise_server_exceptions=True)

RECOMMEND_URL = "/api/risk-assessment/draft/recommend"
RECALCULATE_URL = "/api/risk-assessment/draft/recalculate"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 1: 정상 recommend — ELEC_LIVE
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_elec_live():
    resp = client.post(RECOMMEND_URL, json={
        "site_context": {
            "condition_flags": ["live_electric"]
        },
        "work": {
            "work_type_code": "ELEC_LIVE",
            "work_name": "활선 점검"
        }
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["work"]["work_type_code"] == "ELEC_LIVE"
    assert len(data["rows"]) >= 1

    row = data["rows"][0]
    assert row["hazard"]["hazard_code"] == "ELEC"
    assert len(row["controls"]) >= 1
    assert len(row["laws"]) >= 1
    assert row["row_id"].startswith("ELEC_LIVE_ELEC_")

    # editable과 원본 controls 분리 검증
    control_names = {c["control_name"] for c in row["controls"]}
    editable_texts = set(row["editable"]["control_texts"])
    # editable.control_texts는 control_names와 일치 가능하지만,
    # 구조상 별도 필드임 (controls[].control_name != editable.control_texts의 직접 참조)
    assert "control_texts" in row["editable"]
    assert "hazard_text" in row["editable"]


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 2: 정상 recommend — WATER_MANHOLE (confined_space)
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_water_manhole():
    resp = client.post(RECOMMEND_URL, json={
        "site_context": {
            "condition_flags": ["confined_space"]
        },
        "work": {
            "work_type_code": "WATER_MANHOLE"
        }
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["work"]["work_type_code"] == "WATER_MANHOLE"
    hazard_codes = {r["hazard"]["hazard_code"] for r in data["rows"]}
    assert "ASPHYX" in hazard_codes, f"ASPHYX not found in {hazard_codes}"

    # law evidence 포함 확인
    for row in data["rows"]:
        assert len(row["laws"]) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 3: 존재하지 않는 work_type_code → 404
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_invalid_work_type():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "NONEXISTENT_CODE_XYZ"}
    })
    assert resp.status_code == 404, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 4: work_type_code 누락 → 422
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_missing_work_type_code():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_name": "작업명만 있고 코드 없음"}
    })
    assert resp.status_code == 422, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 5: options 범위 초과 → 422
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_options_out_of_range():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "options": {"max_hazards": 99}
    })
    assert resp.status_code == 422, resp.text

    resp2 = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "options": {"max_hazards": 0}
    })
    assert resp2.status_code == 422, resp2.text


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 6: 정상 recalculate
# ─────────────────────────────────────────────────────────────────────────────
def test_recalculate_normal():
    resp = client.post(RECALCULATE_URL, json={
        "draft_context": {
            "work_type_code": "ELEC_LIVE",
            "condition_flags": ["live_electric"]
        },
        "rows": [
            {
                "row_id": "ELEC_LIVE_ELEC_001",
                "hazard_code": "ELEC",
                "selected_control_codes": ["ELEC_C02", "ELEC_C05"],
                "custom_control_texts": ["사용자 입력 대책 1"],
                "excluded_law_ids": [],
                "memo": "테스트 메모"
            }
        ],
        "options": {
            "rebuild_law_evidence": True,
            "rescore_controls": True
        }
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert len(data["rows"]) == 1
    row = data["rows"][0]
    assert row["row_id"] == "ELEC_LIVE_ELEC_001"

    # editable에 custom_control_texts 반영
    assert row["editable"]["memo"] == "테스트 메모"
    assert "사용자 입력 대책 1" in row["editable"]["control_texts"]

    # controls는 선택된 코드 기준
    ctrl_codes = {c["control_code"] for c in row["controls"]}
    assert "ELEC_C02" in ctrl_codes
    assert "ELEC_C05" in ctrl_codes

    # editable.control_texts와 controls[].control_name은 별도 필드
    for c in row["controls"]:
        assert "control_code" in c
        assert "control_name" in c


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 7: 빈 rows recalculate → 422
# ─────────────────────────────────────────────────────────────────────────────
def test_recalculate_empty_rows():
    resp = client.post(RECALCULATE_URL, json={
        "draft_context": {"work_type_code": "ELEC_LIVE"},
        "rows": []
    })
    assert resp.status_code == 422, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 8: 잘못된 row_id (hazard_code 불일치) → 422
# ─────────────────────────────────────────────────────────────────────────────
def test_recalculate_wrong_row_id():
    resp = client.post(RECALCULATE_URL, json={
        "draft_context": {"work_type_code": "ELEC_LIVE"},
        "rows": [
            {
                "row_id": "TEMP_SCAFF_FALL_001",  # worktype 불일치
                "hazard_code": "ELEC",
                "selected_control_codes": []
            }
        ]
    })
    assert resp.status_code == 422, resp.text


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 9: editable과 controls 분리 검증 (상세)
# ─────────────────────────────────────────────────────────────────────────────
def test_editable_controls_separation():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "TEMP_SCAFF"},
        "site_context": {"condition_flags": ["high_place"]}
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    for row in data["rows"]:
        # controls[]는 엔진 원본: control_code, control_name, control_score 포함
        for ctrl in row["controls"]:
            assert "control_code" in ctrl
            assert "control_name" in ctrl
            assert "control_score" in ctrl

        # editable은 별도 구조: control_texts는 str list
        assert isinstance(row["editable"]["control_texts"], list)
        for text in row["editable"]["control_texts"]:
            assert isinstance(text, str)

        # editable에 control_code/control_score 없음
        assert "control_code" not in row["editable"]
        assert "control_score" not in row["editable"]


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 10: condition_flags 없음 → CONDITION_FLAG_MISSING warning
# ─────────────────────────────────────────────────────────────────────────────
def test_condition_flag_missing_warning():
    # WATER_MANHOLE은 confined_space 권장
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "WATER_MANHOLE"},
        "site_context": {"condition_flags": []}  # 권장 flag 없음
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "CONDITION_FLAG_MISSING" in data["review_flags"], \
        f"Expected CONDITION_FLAG_MISSING, got: {data['review_flags']}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 11: TEMP_SCAFF — row_id 형식 검증
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_temp_scaff_row_ids():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "TEMP_SCAFF"},
        "site_context": {"condition_flags": ["high_place"]}
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    for i, row in enumerate(data["rows"], start=1):
        row_id = row["row_id"]
        # 형식: TEMP_SCAFF_{HAZARD_CODE}_{seq:03d}
        assert row_id.startswith("TEMP_SCAFF_"), f"bad row_id: {row_id}"
        parts = row_id.split("_")
        seq_part = parts[-1]
        assert seq_part.isdigit(), f"seq not numeric: {row_id}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 12: LIFT_RIGGING — row, control, law 포함 확인
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_lift_rigging():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "LIFT_RIGGING"},
        "site_context": {"condition_flags": ["high_place"]}
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["summary"]["hazard_count"] >= 1
    assert data["summary"]["control_count"] >= 1
    assert data["summary"]["law_count"] >= 1

    for row in data["rows"]:
        assert len(row["controls"]) >= 1
        assert len(row["laws"]) >= 1
        # law에 evidence_paths 포함
        for lw in row["laws"]:
            assert len(lw["evidence_paths"]) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 13: LOW_LAW_EVIDENCE flag — include_law_evidence=False → laws 비어있음
# ─────────────────────────────────────────────────────────────────────────────
def test_low_law_evidence_flag():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "options": {"include_law_evidence": False}
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    for row in data["rows"]:
        assert row["laws"] == [], "laws should be empty when include_law_evidence=False"
        # laws가 없으면 LOW_LAW_EVIDENCE가 row_flags에 포함되어야 함
        assert "LOW_LAW_EVIDENCE" in row["row_flags"], \
            f"Expected LOW_LAW_EVIDENCE in row_flags, got: {row['row_flags']}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 14: recalculate — unknown control_code → MANUAL_REVIEW_RECOMMENDED
# ─────────────────────────────────────────────────────────────────────────────
def test_recalculate_unknown_control_code_flag():
    resp = client.post(RECALCULATE_URL, json={
        "draft_context": {
            "work_type_code": "ELEC_LIVE",
            "condition_flags": ["live_electric"]
        },
        "rows": [
            {
                "row_id": "ELEC_LIVE_ELEC_001",
                "hazard_code": "ELEC",
                "selected_control_codes": ["ELEC_C02", "NONEXISTENT_CTRL_ZZZ"],
                "custom_control_texts": [],
                "excluded_law_ids": []
            }
        ]
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    row = data["rows"][0]
    # 알 수 없는 코드는 controls에서 제외
    ctrl_codes = {c["control_code"] for c in row["controls"]}
    assert "NONEXISTENT_CTRL_ZZZ" not in ctrl_codes
    assert "ELEC_C02" in ctrl_codes
    # 인식 불가 코드 존재 → MANUAL_REVIEW_RECOMMENDED
    assert "MANUAL_REVIEW_RECOMMENDED" in row["row_flags"], \
        f"Expected MANUAL_REVIEW_RECOMMENDED, got: {row['row_flags']}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 15: recommend 반복 호출 결정론적 일치 (3회)
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_deterministic_repeat():
    payload = {
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
    }
    results = []
    for _ in range(3):
        resp = client.post(RECOMMEND_URL, json=payload)
        assert resp.status_code == 200
        results.append(resp.json()["rows"])

    assert results[0] == results[1], "recommend rows must be identical on repeat call (1==2)"
    assert results[1] == results[2], "recommend rows must be identical on repeat call (2==3)"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 16: recalculate 반복 호출 결정론적 일치 (3회)
# ─────────────────────────────────────────────────────────────────────────────
def test_recalculate_deterministic_repeat():
    payload = {
        "draft_context": {
            "work_type_code": "ELEC_LIVE",
            "condition_flags": ["live_electric"],
        },
        "rows": [
            {
                "row_id": "ELEC_LIVE_ELEC_001",
                "hazard_code": "ELEC",
                "selected_control_codes": ["ELEC_C02"],
            }
        ],
    }
    results = []
    for _ in range(3):
        resp = client.post(RECALCULATE_URL, json=payload)
        assert resp.status_code == 200
        results.append(resp.json()["rows"])

    assert results[0] == results[1], "recalculate rows must be identical on repeat call (1==2)"
    assert results[1] == results[2], "recalculate rows must be identical on repeat call (2==3)"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 17: max_laws_per_row 상한 준수 (max=2)
# ─────────────────────────────────────────────────────────────────────────────
def test_max_laws_per_row_enforced():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
        "options": {"max_laws_per_row": 2},
    })
    assert resp.status_code == 200
    data = resp.json()
    for row in data["rows"]:
        assert len(row["laws"]) <= 2, \
            f"row {row['row_id']} has {len(row['laws'])} laws, expected ≤2"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 18: max_laws_per_row 최솟값 경계 (max=1)
# ─────────────────────────────────────────────────────────────────────────────
def test_max_laws_per_row_min_boundary():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "WATER_MANHOLE"},
        "site_context": {"condition_flags": ["confined_space"]},
        "options": {"max_laws_per_row": 1},
    })
    assert resp.status_code == 200
    data = resp.json()
    for row in data["rows"]:
        assert len(row["laws"]) <= 1, \
            f"row {row['row_id']} has {len(row['laws'])} laws, expected ≤1"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 19: generic-law top1 미발생 — specific law 존재 시 첫 번째 law는 비generic
# ─────────────────────────────────────────────────────────────────────────────
def test_generic_law_not_top1():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
    })
    assert resp.status_code == 200
    data = resp.json()

    for row in data["rows"]:
        laws = row["laws"]
        if not laws:
            continue
        has_specific = any(
            any(p != "worktype_law" for p in lw["evidence_paths"])
            for lw in laws
        )
        if has_specific:
            first_paths = laws[0]["evidence_paths"]
            assert any(p != "worktype_law" for p in first_paths), \
                f"row {row['row_id']}: top-1 law is generic (worktype_law only) but specific laws exist. " \
                f"laws={[l['evidence_paths'] for l in laws]}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 20: law evidence priority 순서 — control_law → hazard_law → worktype_law
# ─────────────────────────────────────────────────────────────────────────────
def test_law_ordering_priority():
    _PRIORITY = {"control_law": 0, "hazard_law": 1, "worktype_law": 2}

    def ev_priority(paths):
        for key in ("control_law", "hazard_law", "worktype_law"):
            if key in paths:
                return _PRIORITY[key]
        return 2

    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
        "options": {"max_laws_per_row": 5},
    })
    assert resp.status_code == 200
    data = resp.json()

    for row in data["rows"]:
        priorities = [ev_priority(lw["evidence_paths"]) for lw in row["laws"]]
        assert priorities == sorted(priorities), \
            f"row {row['row_id']}: law ordering not sorted by priority: {priorities}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 21: generic-law cap — specific law 존재 시 worktype-only law ≤1
# ─────────────────────────────────────────────────────────────────────────────
def test_generic_law_cap_with_specific():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "WATER_MANHOLE"},
        "site_context": {"condition_flags": ["confined_space"]},
        "options": {"max_laws_per_row": 10},
    })
    assert resp.status_code == 200
    data = resp.json()

    for row in data["rows"]:
        laws = row["laws"]
        specific = [l for l in laws if any(p != "worktype_law" for p in l["evidence_paths"])]
        generic = [l for l in laws if all(p == "worktype_law" for p in l["evidence_paths"])]
        if specific:
            assert len(generic) <= 1, \
                f"row {row['row_id']}: {len(generic)} generic laws when specific exist (cap=1)"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 22: WELD_ARC — FIRE, ELEC, DUST 위험 시나리오
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_weld_arc():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "WELD_ARC", "work_name": "아크용접 작업"},
        "site_context": {"condition_flags": ["chemical_use"]},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["work"]["work_type_code"] == "WELD_ARC"
    assert data["summary"]["hazard_count"] >= 1

    hazard_codes = {r["hazard"]["hazard_code"] for r in data["rows"]}
    # WELD_ARC에는 FIRE, ELEC, DUST 위험 존재
    assert hazard_codes & {"FIRE", "ELEC", "DUST"}, \
        f"WELD_ARC expected FIRE/ELEC/DUST in {hazard_codes}"

    for row in data["rows"]:
        assert len(row["controls"]) >= 1
        assert len(row["laws"]) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 23: CIVIL_EXCAV — 붕괴(COLLAPSE) 위험 시나리오
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_civil_excav():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "CIVIL_EXCAV", "work_name": "터파기 굴착 작업"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["work"]["work_type_code"] == "CIVIL_EXCAV"

    hazard_codes = {r["hazard"]["hazard_code"] for r in data["rows"]}
    assert "COLLAPSE" in hazard_codes, f"CIVIL_EXCAV expected COLLAPSE in {hazard_codes}"

    for row in data["rows"]:
        if row["hazard"]["hazard_code"] == "COLLAPSE":
            assert len(row["laws"]) >= 1, "COLLAPSE row must have law evidence"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 24: WELD_GAS — FIRE, EXPLO 위험 시나리오
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_fire_explo_scenario():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "WELD_GAS", "work_name": "가스용접 작업"},
    })
    assert resp.status_code == 200
    data = resp.json()

    hazard_codes = {r["hazard"]["hazard_code"] for r in data["rows"]}
    assert hazard_codes & {"FIRE", "EXPLO"}, \
        f"WELD_GAS expected FIRE or EXPLO in {hazard_codes}"

    for row in data["rows"]:
        assert len(row["laws"]) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 25: TUNNEL_DRILL — 분진(DUST) 위험 시나리오
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_dust_scenario():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "TUNNEL_DRILL", "work_name": "터널 천공 작업"},
        "site_context": {"condition_flags": ["confined_space"]},
    })
    assert resp.status_code == 200
    data = resp.json()

    hazard_codes = {r["hazard"]["hazard_code"] for r in data["rows"]}
    assert "DUST" in hazard_codes, f"TUNNEL_DRILL expected DUST in {hazard_codes}"

    for row in data["rows"]:
        assert len(row["laws"]) >= 1


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 26: recommend → recalculate 동일 입력 시 law 일치
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_recalculate_law_alignment():
    rec_resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
    })
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()

    first_row = rec_data["rows"][0]
    hcode = first_row["hazard"]["hazard_code"]
    ctrl_codes = [c["control_code"] for c in first_row["controls"]]
    row_id = first_row["row_id"]

    recalc_resp = client.post(RECALCULATE_URL, json={
        "draft_context": {
            "work_type_code": "ELEC_LIVE",
            "condition_flags": ["live_electric"],
        },
        "rows": [{
            "row_id": row_id,
            "hazard_code": hcode,
            "selected_control_codes": ctrl_codes,
        }],
        "options": {"rebuild_law_evidence": True, "max_laws_per_row": 3},
    })
    assert recalc_resp.status_code == 200
    recalc_data = recalc_resp.json()

    rec_law_ids = {l["law_id"] for l in first_row["laws"]}
    recalc_law_ids = {l["law_id"] for l in recalc_data["rows"][0]["laws"]}
    assert rec_law_ids == recalc_law_ids, \
        f"recommend/recalculate law mismatch: {rec_law_ids} vs {recalc_law_ids}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 27: excluded_law_ids — 제외 law가 응답에 미포함
# ─────────────────────────────────────────────────────────────────────────────
def test_recalculate_excluded_law_ids():
    # 먼저 recommend로 law 목록 획득
    rec_resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
    })
    assert rec_resp.status_code == 200
    first_row = rec_resp.json()["rows"][0]
    laws = first_row["laws"]

    if not laws:
        pytest.skip("no laws to exclude")

    excluded_id = laws[0]["law_id"]
    ctrl_codes = [c["control_code"] for c in first_row["controls"]]

    resp = client.post(RECALCULATE_URL, json={
        "draft_context": {
            "work_type_code": "ELEC_LIVE",
            "condition_flags": ["live_electric"],
        },
        "rows": [{
            "row_id": first_row["row_id"],
            "hazard_code": first_row["hazard"]["hazard_code"],
            "selected_control_codes": ctrl_codes,
            "excluded_law_ids": [excluded_id],
        }],
    })
    assert resp.status_code == 200
    result_law_ids = {l["law_id"] for l in resp.json()["rows"][0]["laws"]}
    assert excluded_id not in result_law_ids, \
        f"excluded law_id '{excluded_id}' should not appear in recalculate result"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 28: rebuild_law_evidence=False → laws 빈 배열
# ─────────────────────────────────────────────────────────────────────────────
def test_recalculate_rebuild_false_no_laws():
    resp = client.post(RECALCULATE_URL, json={
        "draft_context": {
            "work_type_code": "ELEC_LIVE",
            "condition_flags": ["live_electric"],
        },
        "rows": [{
            "row_id": "ELEC_LIVE_ELEC_001",
            "hazard_code": "ELEC",
            "selected_control_codes": ["ELEC_C02"],
        }],
        "options": {"rebuild_law_evidence": False},
    })
    assert resp.status_code == 200
    row = resp.json()["rows"][0]
    assert row["laws"] == [], \
        f"rebuild_law_evidence=False must yield empty laws, got: {row['laws']}"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 29: preferred_hazard_codes — 선호 위험이 첫 row로 등장
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_preferred_hazard_first():
    # ELEC_LIVE에서 두 번째로 올 수 있는 hazard를 선호 코드로 지정
    resp_default = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
    })
    assert resp_default.status_code == 200
    rows = resp_default.json()["rows"]
    if len(rows) < 2:
        pytest.skip("need at least 2 hazard rows")

    preferred = rows[1]["hazard"]["hazard_code"]

    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
        "user_inputs": {"preferred_hazard_codes": [preferred]},
    })
    assert resp.status_code == 200
    result_rows = resp.json()["rows"]
    assert result_rows[0]["hazard"]["hazard_code"] == preferred, \
        f"preferred hazard '{preferred}' should be first row"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 30: excluded_hazard_codes — 제외 위험이 rows에 미포함
# ─────────────────────────────────────────────────────────────────────────────
def test_recommend_excluded_hazard():
    resp_default = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
    })
    rows = resp_default.json()["rows"]
    if not rows:
        pytest.skip("no hazard rows")

    excluded = rows[0]["hazard"]["hazard_code"]

    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "ELEC_LIVE"},
        "site_context": {"condition_flags": ["live_electric"]},
        "user_inputs": {"excluded_hazard_codes": [excluded]},
    })
    assert resp.status_code == 200
    result_codes = {r["hazard"]["hazard_code"] for r in resp.json()["rows"]}
    assert excluded not in result_codes, \
        f"excluded hazard '{excluded}' should not appear in rows"


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 31: summary 집계 일치 검증
# ─────────────────────────────────────────────────────────────────────────────
def test_summary_counts_match_rows():
    resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "TEMP_SCAFF"},
        "site_context": {"condition_flags": ["high_place"]},
    })
    assert resp.status_code == 200
    data = resp.json()

    rows = data["rows"]
    expected_hazard = len(rows)
    expected_control = sum(len(r["controls"]) for r in rows)
    expected_law = sum(len(r["laws"]) for r in rows)

    assert data["summary"]["hazard_count"] == expected_hazard
    assert data["summary"]["control_count"] == expected_control
    assert data["summary"]["law_count"] == expected_law


# ─────────────────────────────────────────────────────────────────────────────
# 테스트 32: LIFT_RIGGING — recommend/recalculate 반복 일치 (양중 시나리오)
# ─────────────────────────────────────────────────────────────────────────────
def test_lift_rigging_recommend_recalculate_alignment():
    rec_resp = client.post(RECOMMEND_URL, json={
        "work": {"work_type_code": "LIFT_RIGGING"},
        "site_context": {"condition_flags": ["high_place"]},
    })
    assert rec_resp.status_code == 200
    rows = rec_resp.json()["rows"]
    assert rows

    recalc_rows = [{
        "row_id": r["row_id"],
        "hazard_code": r["hazard"]["hazard_code"],
        "selected_control_codes": [c["control_code"] for c in r["controls"]],
    } for r in rows]

    recalc_resp = client.post(RECALCULATE_URL, json={
        "draft_context": {
            "work_type_code": "LIFT_RIGGING",
            "condition_flags": ["high_place"],
        },
        "rows": recalc_rows,
        "options": {"rebuild_law_evidence": True, "max_laws_per_row": 3},
    })
    assert recalc_resp.status_code == 200
    recalc_data = recalc_resp.json()

    for orig_row, recalc_row in zip(rows, recalc_data["rows"]):
        orig_ids = {l["law_id"] for l in orig_row["laws"]}
        recalc_ids = {l["law_id"] for l in recalc_row["laws"]}
        assert orig_ids == recalc_ids, \
            f"LIFT_RIGGING row {orig_row['row_id']}: " \
            f"recommend/recalculate law mismatch: {orig_ids} vs {recalc_ids}"
