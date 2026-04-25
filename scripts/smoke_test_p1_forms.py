"""
P1 구현 + evidence 연결 완료 — ED-003 / WP-015 smoke test.

검증 항목:
  1. registry: special_education_log 등록됨
  2. get_form_spec() 검증 (display_name, required_fields, repeat_field, max_repeat_rows)
  3. 최소 샘플 입력으로 Excel bytes 생성 확인
  4. 공란 form_data로 bytes 생성 (오류 없음)
  5. 전체 샘플 bytes 생성
  6. 필수 섹션 제목 포함 확인:
     - 특별 안전보건교육 교육일지
     - 교육 기본정보
     - 교육시간 구분
     - 특별교육 대상 작업
     - 교육내용
     - 교육대상자 명단
     - 확인 서명
  7. 개인정보 과다 필드 없음: 주민등록번호, 건강정보, 질병명
  8. 별표 4/별표 5 기준 문구 포함 (VERIFIED 상태)
  9. ED-003 catalog DONE 확인
 10. ED-003 evidence_status == VERIFIED (PARTIAL_VERIFIED도 허용)
 11. evidence_id 4개 연결 확인 (ED-003-L1 ~ L4)
 12. evidence_file 4개 실제 파일 존재 확인
 13. 각 evidence_file verification_result 확인 (VERIFIED 또는 PARTIAL_VERIFIED)
 14. 별표 4 교육시간 구조화 정보 존재 확인
 15. 별표 5 대상 작업 번호 범위 (제1호~제39호) 확인

실행:
    cd <project_root>
    python scripts/smoke_test_p1_forms.py

판정:
    PASS — 모든 항목 통과
    WARN — bytes 생성됐으나 경고 발생
    FAIL — 예외 발생 또는 필수 항목 미충족
"""
from __future__ import annotations

import json
import sys
import traceback
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, ".")

from engine.output.form_registry import build_form_excel, get_form_spec, list_supported_forms

ROOT         = Path(".")
EVIDENCE_DIR = ROOT / "data" / "evidence" / "safety_law_refs"

# ---------------------------------------------------------------------------
# ED-003 샘플 form_data
# ---------------------------------------------------------------------------

SAMPLE_ED003_FULL: dict = {
    "site_name": "테스트건설(주) 테스트현장",
    "site_address": "서울특별시 중구 세종대로 110",
    "education_name": "밀폐공간 작업 특별 안전보건교육",
    "education_date": "2026-04-25",
    "education_location": "현장 교육장",
    "education_target_work": "밀폐공간 작업",
    "related_education": "신규채용 시 교육 병행 실시",
    "duration_category": "16시간 이상 (최초 배치 전)",
    "actual_duration_hours": "16",
    "remaining_hours": "0",
    "subjects": [
        {
            "subject_name": "밀폐공간 작업의 위험성",
            "subject_content": "산소결핍·유해가스 발생 원인 및 사례",
            "subject_hours": "4",
        },
        {
            "subject_name": "가스 측정 및 환기",
            "subject_content": "가스 측정기 사용법, 강제 환기 설비 운영",
            "subject_hours": "4",
        },
        {
            "subject_name": "비상대피 및 구조",
            "subject_content": "비상신호, 대피 절차, 공기호흡기 착용법",
            "subject_hours": "4",
        },
        {
            "subject_name": "실습: 가스 측정·환기·비상대피",
            "subject_content": "현장 실습 (집수정 모의 훈련)",
            "subject_hours": "4",
        },
    ],
    "instructor_name": "홍길동",
    "instructor_org": "현장안전팀",
    "instructor_role": "안전관리자",
    "instructor_qualification": "산업안전지도사 (제2020-00001호)",
    "attendees": [
        {
            "attendee_name": "이순신",
            "attendee_org": "테스트건설(주)",
            "attendee_job_type": "배관공",
            "attendee_birth_year": "1985",
            "attendee_completed": "완료",
        },
        {
            "attendee_name": "강감찬",
            "attendee_org": "협력업체 A",
            "attendee_job_type": "감시인",
            "attendee_birth_year": "1990",
            "attendee_completed": "완료",
        },
    ],
    "comprehension_verbal": "구두 질의응답 완료 (전원 이해 확인)",
    "comprehension_checklist": "10문항 체크리스트 실시 — 전원 8점 이상",
    "comprehension_practice": "가스측정기 사용 실습 완료",
    "retraining_targets": "없음",
    "attachments": "교육자료(PPT) / 현장 실습 사진 3장 / 참석자 서명부",
    "confirmer_name": "김안전",
    "confirmer_role": "안전보건관리책임자",
    "supervisor_name": "박감독",
    "site_manager_name": "최소장",
    "confirm_date": "2026-04-25",
}

SAMPLE_ED003_MINIMAL: dict = {
    "education_date": "2026-04-25",
    "education_location": "현장 교육장",
    "education_target_work": "밀폐공간 작업",
    "instructor_name": "홍길동",
    "confirmer_name": "김안전",
    "confirmer_role": "안전보건관리책임자",
}

# ---------------------------------------------------------------------------
# 필수 섹션 제목
# ---------------------------------------------------------------------------

REQUIRED_HEADINGS = [
    "특별 안전보건교육 교육일지",
    "교육 기본정보",
    "교육시간 구분",
    "특별교육 대상 작업",
    "교육내용",
    "교육대상자 명단",
    "확인 서명",
]

# 워크북에 반드시 포함되어야 하는 별표 관련 문구
REQUIRED_BYEOLPYO_KEYWORDS = ["별표 4", "별표 5"]

# 기본 필드명으로 출력되면 안 되는 개인정보 키워드
FORBIDDEN_PII_KEYWORDS = [
    "주민등록번호",
    "건강정보",
    "질병명",
]

# ED-003 evidence ID 목록
EXPECTED_EVIDENCE_IDS = ["ED-003-L1", "ED-003-L2", "ED-003-L3", "ED-003-L4"]

# evidence 파일명
EXPECTED_EVIDENCE_FILES = [
    "ED-003-L1_industrial_safety_health_act_article_29.json",
    "ED-003-L2_industrial_safety_health_rule_article_26.json",
    "ED-003-L3_industrial_safety_health_rule_attached_table_4.json",
    "ED-003-L4_industrial_safety_health_rule_attached_table_5.json",
]

# catalog evidence_status 허용값
VALID_EVIDENCE_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED"}


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _all_cell_values(wb) -> list[str]:
    return [
        str(cell.value or "")
        for ws in wb.worksheets
        for row in ws.iter_rows()
        for cell in row
    ]


def _check(ok: bool, name: str, detail: str = "") -> tuple[str, str, str]:
    verdict = "PASS" if ok else "FAIL"
    return (verdict, name, detail)


# ---------------------------------------------------------------------------
# 검증 실행
# ---------------------------------------------------------------------------
# (run_smoke_test 정의는 WP-015 추가 후 파일 하단에 통합됨)
# ---------------------------------------------------------------------------

def _run_ed003_checks_legacy(results, supported) -> None:
    """ED-003 검증 (run_smoke_test에 통합됨, 직접 호출 금지)."""
    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "special_education_log" in supported,
        "registry: special_education_log 등록됨",
    ))

    # ── 2. get_form_spec 검증 ────────────────────────────────────────────
    try:
        spec = get_form_spec("special_education_log")
        results.append(_check(isinstance(spec, dict),
                               "get_form_spec() → dict"))
        results.append(_check(spec.get("display_name") == "특별 안전보건교육 교육일지",
                               "display_name 확인",
                               repr(spec.get("display_name"))))
        results.append(_check(isinstance(spec.get("required_fields"), list)
                               and len(spec["required_fields"]) > 0,
                               "required_fields 비어있지 않음"))
        results.append(_check(spec.get("repeat_field") == "attendees",
                               "repeat_field == 'attendees'"))
        results.append(_check(spec.get("max_repeat_rows") == 30,
                               "max_repeat_rows == 30"))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("special_education_log", SAMPLE_ED003_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("special_education_log", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~8. 전체 샘플 workbook 검증 ────────────────────────────────────
    try:
        full_bytes = build_form_excel("special_education_log", SAMPLE_ED003_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        wb_full = load_workbook(BytesIO(full_bytes))
        all_vals = _all_cell_values(wb_full)
        all_text = " ".join(all_vals)

        # 섹션 제목 포함
        for heading in REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 제목 포함: '{heading}'",
            ))

        # 개인정보 과다 필드 없음
        for keyword in FORBIDDEN_PII_KEYWORDS:
            found = keyword in all_text
            results.append(_check(
                not found,
                f"개인정보 과다 필드 없음: '{keyword}'",
                "FAIL — 기본 필드명에 해당 문구 발견" if found else "",
            ))

        # 별표 4/5 기준 문구 포함 (VERIFIED 상태)
        for kw in REQUIRED_BYEOLPYO_KEYWORDS:
            results.append(_check(
                kw in all_text,
                f"별표 기준 문구 포함: '{kw}'",
            ))

    except Exception as exc:
        tb = traceback.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 9~15. ED-003 catalog + evidence 검증 ────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        ed003 = next(
            (d for d in cat["documents"] if d["id"] == "ED-003"), None
        )

        # 9. catalog 존재
        results.append(_check(ed003 is not None, "catalog: ED-003 항목 존재"))

        if ed003:
            # 10. implementation_status == DONE
            results.append(_check(
                ed003.get("implementation_status") == "DONE",
                "catalog: ED-003 implementation_status == DONE",
                repr(ed003.get("implementation_status")),
            ))
            # form_type 확인
            results.append(_check(
                ed003.get("form_type") == "special_education_log",
                "catalog: ED-003 form_type == 'special_education_log'",
                repr(ed003.get("form_type")),
            ))
            # 11. evidence_status VERIFIED 또는 PARTIAL_VERIFIED
            ev_status = ed003.get("evidence_status", "")
            results.append(_check(
                ev_status in VALID_EVIDENCE_STATUSES,
                f"catalog: ED-003 evidence_status in {VALID_EVIDENCE_STATUSES}",
                repr(ev_status),
            ))

            # 12. evidence_id 4개 포함
            ev_ids = ed003.get("evidence_id") or []
            if isinstance(ev_ids, str):
                ev_ids = [ev_ids]
            for eid in EXPECTED_EVIDENCE_IDS:
                results.append(_check(
                    eid in ev_ids,
                    f"catalog: evidence_id 포함 — {eid}",
                ))

            # 13. evidence_file 실제 존재 확인
            ev_files = ed003.get("evidence_file") or []
            if isinstance(ev_files, str):
                ev_files = [ev_files]
            for efname in EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname}",
                    str(fpath) if not fpath.exists() else "",
                ))

        # 14~15. 각 evidence 파일 내용 검증
        for efname in EXPECTED_EVIDENCE_FILES:
            fpath = EVIDENCE_DIR / efname
            if not fpath.exists():
                continue
            try:
                ev_data = json.loads(fpath.read_text(encoding="utf-8"))
                vr = ev_data.get("verification_result", "")
                results.append(_check(
                    vr in ("VERIFIED", "PARTIAL_VERIFIED"),
                    f"evidence 검증결과: {efname[:30]}... → {vr}",
                ))
                # 별표 4: special_education_hours 구조 확인
                if "table_4" in efname:
                    hours_data = ev_data.get("special_education_hours", {})
                    results.append(_check(
                        bool(hours_data.get("일반근로자")),
                        "별표 4: 일반근로자 특별교육 시간 구조화",
                        repr(hours_data.get("일반근로자", ""))[:60],
                    ))
                # 별표 5: range_phrase 확인
                if "table_5" in efname:
                    works_data = ev_data.get("special_education_target_works", {})
                    results.append(_check(
                        "제1호부터 제39호" in works_data.get("range_phrase", ""),
                        "별표 5: 대상 작업 범위 '제1호부터 제39호까지' 확인",
                        repr(works_data.get("range_phrase", ""))[:60],
                    ))
            except Exception as exc:
                results.append(_check(False, f"evidence 파일 로딩: {efname[:30]}...", str(exc)))

    except Exception as exc:
        tb = traceback.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "catalog/evidence 검증 중 예외", tb))

    # ── 출력 ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    print("  KRAS P1 Smoke Test — ED-003 특별 안전보건교육 교육일지")
    print("=" * 62)

    pass_cnt = warn_cnt = fail_cnt = 0
    for verdict, name, detail in results:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[verdict]
        line = f"  {icon} [{verdict}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)
        if verdict == "PASS":   pass_cnt += 1
        elif verdict == "WARN": warn_cnt += 1
        else:                   fail_cnt += 1; overall = "FAIL"

    print("-" * 62)
    total = len(results)
    print(f"  합계: PASS {pass_cnt}/{total}  WARN {warn_cnt}  FAIL {fail_cnt}")
    print(f"\n  최종 판정: {overall}")
    print("=" * 62 + "\n")

    sys.exit(0 if overall != "FAIL" else 1)


# ---------------------------------------------------------------------------
# WP-015 샘플 form_data
# ---------------------------------------------------------------------------

SAMPLE_WP015_MINIMAL: dict = {
    "structural_review_done": "실시",
    "assembly_drawing_done": "작성 완료",
    "work_location": "3층 슬래브 구간",
}

SAMPLE_WP015_FULL: dict = {
    "site_name": "테스트건설(주) 테스트현장",
    "project_name": "테스트현장 신축공사",
    "work_date": "2026-04-25",
    "work_period": "2026-04-25 ~ 2026-05-10",
    "contractor": "협력업체 A",
    "prepared_by": "홍길동",
    "reviewer": "이순신",
    "approver": "김안전",
    "work_location": "3층 슬래브 구간",
    "work_scope": "3층 슬래브 전면 (240㎡)",
    "formwork_type": "유로폼",
    "shoring_type": "파이프 서포트",
    "floor_section": "3층 (EL+9.0m)",
    "work_phases": "반입 → 운반 → 동바리 설치 → 거푸집 설치 → 타설 전 점검 → 콘크리트 타설 → 양생 → 해체",
    "survey_ground": "콘크리트 슬래브 (하층 완성, 이상 없음)",
    "survey_substructure": "2층 슬래브 및 보 구조물 확인 완료",
    "survey_opening": "계단 개구부 1개소 — 방호조치 필요",
    "survey_material_place": "외부 야적장 (건물 서측)",
    "survey_equipment_route": "타워크레인 양중 후 수레 운반",
    "survey_weather": "강풍(풍속 10m/s 이상), 강우 시 작업 중지",
    "survey_lighting": "조명 설치 완료, 통로 1.5m 이상 확보",
    "structural_review_done": "실시",
    "structural_reviewer": "박구조 (구조기술사)",
    "assembly_drawing_done": "작성 완료",
    "member_spec": "파이프 서포트 Ø60.5×2.3t, 멍에 H-100, 장선 각목 90×90",
    "install_interval": "서포트 간격 900×900mm",
    "joint_method": "커플러 체결, 핀 고정",
    "brace_plan": "수평연결재 3단 이상, 가새 X형 설치",
    "base_plate_plan": "깔판 두께 30mm 이상, 쐐기 고정",
    "structural_doc_attached": "첨부 (별도 보관)",
    "assembly_drawing_attached": "첨부 (별도 보관)",
    "work_sequence": "1.자재반입→ 2.먹매김/위치확인→ 3.동바리설치→ 4.멍에/장선설치→ 5.거푸집설치→ 6.수직·수평도확인→ 7.타설전점검→ 8.콘크리트타설→ 9.양생→ 10.해체전강도확인→ 11.거푸집해체→ 12.동바리해체",
    "hazard_items": [
        {"hazard": "동바리 침하/전도", "safety_measure": "깔판·베이스플레이트 설치, 수직도 확인"},
        {"hazard": "콘크리트 타설 중 붕괴", "safety_measure": "편심하중 방지, 타설 속도 관리"},
        {"hazard": "추락 (개구부)", "safety_measure": "개구부 덮개·안전망 설치"},
        {"hazard": "낙하물", "safety_measure": "낙하물 방지망, 출입통제"},
    ],
    "safety_measures_text": "1)작업구역 출입통제 2)추락방지 안전난간 설치 3)낙하물 방지망 4)동바리 침하방지 깔판 5)타설 순서·속도 관리 6)작업지휘자 배치 7)전원 보호구 착용",
    "work_commander_name": "강감찬",
    "work_commander_org": "테스트건설(주) 안전팀",
    "work_commander_contact": "010-0000-0000",
    "work_commander_duties": "거푸집·동바리 설치 및 해체 전 과정 지휘",
    "work_commander_educated": "완료 (2026-04-24)",
    "education_done": "완료",
    "tbm_done": "완료",
    "sign_date": "2026-04-25",
}

# WP-015 필수 섹션 제목
WP015_REQUIRED_HEADINGS = [
    "거푸집·동바리 작업계획서",
    "작업 개요",
    "사전조사",
    "구조검토 및 조립도",
    "작업 순서 및 방법",
    "주요 위험요인",
    "안전대책",
    "작업지휘자",
    "작업 전 점검표",
    "확인 서명",
]

# WP-015 필수 포함 문구
WP015_REQUIRED_PHRASES = [
    "구조검토서 및 조립도 원본 첨부·보관 필요",
]

# WP-015 evidence ID 목록
WP015_EXPECTED_EVIDENCE_IDS = ["WP-015-L1", "WP-015-L2", "WP-015-L3", "WP-015-L4"]

# WP-015 evidence 파일명
WP015_EXPECTED_EVIDENCE_FILES = [
    "WP-015_safety_rule_article_38.json",
    "WP-015_safety_rule_article_39.json",
    "WP-015_safety_rule_article_331.json",
    "WP-015_safety_rule_articles_328_337.json",
]

# 허용 evidence_status
WP015_VALID_EV_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED"}


def run_wp015_smoke_test() -> list[tuple[str, str, str]]:
    """WP-015 거푸집·동바리 작업계획서 smoke test. 결과 list 반환."""
    results: list[tuple[str, str, str]] = []
    supported = {f["form_type"] for f in list_supported_forms()}

    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "formwork_shoring_workplan" in supported,
        "registry: formwork_shoring_workplan 등록됨",
    ))

    # ── 2. get_form_spec 검증 ─────────────────────────────────────────────
    try:
        spec = get_form_spec("formwork_shoring_workplan")
        results.append(_check(isinstance(spec, dict),
                               "get_form_spec() → dict"))
        results.append(_check(
            spec.get("display_name") == "거푸집·동바리 작업계획서",
            "display_name 확인",
            repr(spec.get("display_name")),
        ))
        results.append(_check(
            isinstance(spec.get("required_fields"), list)
            and len(spec["required_fields"]) > 0,
            "required_fields 비어있지 않음",
        ))
        results.append(_check(
            spec.get("repeat_field") == "hazard_items",
            "repeat_field == 'hazard_items'",
            repr(spec.get("repeat_field")),
        ))
        results.append(_check(
            spec.get("max_repeat_rows") == 10,
            "max_repeat_rows == 10",
        ))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ─────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("formwork_shoring_workplan", SAMPLE_WP015_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ─────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("formwork_shoring_workplan", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~7. 전체 샘플 workbook 검증 ─────────────────────────────────────
    try:
        full_bytes = build_form_excel("formwork_shoring_workplan", SAMPLE_WP015_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        wb_full = load_workbook(BytesIO(full_bytes))
        all_vals = _all_cell_values(wb_full)
        all_text = " ".join(all_vals)

        # 섹션 제목 포함
        for heading in WP015_REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 제목 포함: '{heading}'",
            ))

        # 필수 문구 포함
        for phrase in WP015_REQUIRED_PHRASES:
            results.append(_check(
                phrase in all_text,
                f"필수 문구 포함: '{phrase}'",
            ))

        # 개인정보 과다 필드 없음
        for keyword in FORBIDDEN_PII_KEYWORDS:
            found = keyword in all_text
            results.append(_check(
                not found,
                f"개인정보 과다 필드 없음: '{keyword}'",
                "FAIL — 기본 필드명에 해당 문구 발견" if found else "",
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 8~11. WP-015 catalog + evidence 검증 ─────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        wp015 = next(
            (d for d in cat["documents"] if d["id"] == "WP-015"), None
        )

        results.append(_check(wp015 is not None, "catalog: WP-015 항목 존재"))

        if wp015:
            results.append(_check(
                wp015.get("implementation_status") == "DONE",
                "catalog: WP-015 implementation_status == DONE",
                repr(wp015.get("implementation_status")),
            ))
            results.append(_check(
                wp015.get("form_type") == "formwork_shoring_workplan",
                "catalog: WP-015 form_type == 'formwork_shoring_workplan'",
                repr(wp015.get("form_type")),
            ))
            ev_status = wp015.get("evidence_status", "")
            results.append(_check(
                ev_status in WP015_VALID_EV_STATUSES,
                f"catalog: WP-015 evidence_status in {WP015_VALID_EV_STATUSES}",
                repr(ev_status),
            ))

            # evidence_id 4개 포함
            ev_ids = wp015.get("evidence_id") or []
            if isinstance(ev_ids, str):
                ev_ids = [ev_ids]
            for eid in WP015_EXPECTED_EVIDENCE_IDS:
                results.append(_check(
                    eid in ev_ids,
                    f"catalog: evidence_id 포함 — {eid}",
                ))

            # evidence_file 실제 존재 확인
            ev_files = wp015.get("evidence_file") or []
            if isinstance(ev_files, str):
                ev_files = [ev_files]
            for efname in WP015_EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname}",
                    str(fpath) if not fpath.exists() else "",
                ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "WP-015 catalog/evidence 검증 중 예외", tb))

    # ── 12. evidence 파일 내용 검증 ───────────────────────────────────────
    for efname in WP015_EXPECTED_EVIDENCE_FILES:
        fpath = EVIDENCE_DIR / efname
        if not fpath.exists():
            continue
        try:
            ev_data = json.loads(fpath.read_text(encoding="utf-8"))
            vr = ev_data.get("verification_result", "")
            results.append(_check(
                vr in ("VERIFIED", "PARTIAL_VERIFIED"),
                f"evidence 검증결과: {efname[:35]}... → {vr}",
            ))
        except Exception as exc:
            results.append(_check(False, f"evidence 파일 로딩: {efname[:35]}...", str(exc)))

    return results


# ---------------------------------------------------------------------------
# ED-004 샘플 form_data
# ---------------------------------------------------------------------------

SAMPLE_ED004_MINIMAL: dict = {
    "role_type": "안전관리자",
    "training_category": "신규교육",
}

SAMPLE_ED004_FULL: dict = {
    "site_name": "테스트건설(주) 테스트현장",
    "field_name": "테스트현장 신축공사",
    "employer_name": "테스트건설(주)",
    "write_date": "2026-04-25",
    "department": "안전보건팀",
    "person_name": "홍길동",
    "person_org": "테스트건설(주)",
    "person_title": "안전관리자",
    "role_type": "안전관리자",
    "appointment_date": "2026-01-01",
    "is_training_target": "대상",
    "training_category": "신규교육",
    "legal_basis_text": "산업안전보건법 제32조, 제17조, 시행규칙 직무교육 조항",
    "new_training_deadline": "선임 후 3개월 이내 (NEEDS_VERIFICATION)",
    "refresher_cycle": "매 2년마다 (NEEDS_VERIFICATION)",
    "doctor_special_case": "해당 없음 (안전관리자)",
    "training_exemption": "없음",
    "training_org": "한국산업안전보건교육원",
    "training_course": "안전관리자 신규 직무교육",
    "training_start_date": "2026-03-10",
    "training_end_date": "2026-03-12",
    "training_hours": "24",
    "completion_no": "2026-SM-00001",
    "certificate_date": "2026-03-12",
    "completion_status": "수료",
    "cert_attached": "첨부",
    "agency_confirm_attached": "첨부",
    "appointment_doc_attached": "첨부",
    "refresher_basis_attached": "해당 없음 (신규교육)",
    "not_completed": "없음",
    "not_completed_reason": "",
    "action_plan": "",
    "scheduled_training_date": "",
    "manager_name": "김안전",
    "writer_name": "홍길동",
    "safety_manager_sign": "홍길동",
    "supervisor_sign": "이감독",
    "site_manager_sign": "최소장",
    "sign_date": "2026-04-25",
}

# ED-004 필수 섹션 제목/문구
ED004_REQUIRED_HEADINGS = [
    "안전보건관리자 직무교육 이수 확인서",
    "직무교육 대상자 정보",
    "역할 구분",
    "신규교육",
    "보수교육",
    "교육 이수 내역",
    "수료증 첨부",
    "확인 및 서명",
]

ED004_REQUIRED_PHRASES = [
    "공식 수료증을 대체하지 않음",
]

ED004_FORBIDDEN_PII = [
    "주민등록번호",
    "건강정보",
    "질병명",
]

ED004_TRAINING_CODES = [
    "EDU_RESP_MANAGER_DUTY",
    "EDU_SAFETY_MANAGER_DUTY",
    "EDU_HEALTH_MANAGER_DUTY",
]

ED004_VALID_EV_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED"}

EVIDENCE_DIR_ED004 = ROOT / "data" / "evidence" / "safety_law_refs"

ED004_EXPECTED_EVIDENCE_FILES = [
    "ED-004-L1_industrial_safety_health_act_article_32.json",
    "ED-004-L2_industrial_safety_health_act_articles_15_17_18.json",
    "ED-004-L3_industrial_safety_health_rule_job_training.json",
]


def run_ed004_smoke_test() -> list[tuple[str, str, str]]:
    """ED-004 안전보건관리자 직무교육 이수 확인서 smoke test. 결과 list 반환."""
    results: list[tuple[str, str, str]] = []
    supported = {f["form_type"] for f in list_supported_forms()}

    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "manager_job_training_record" in supported,
        "registry: manager_job_training_record 등록됨",
    ))

    # ── 2. get_form_spec 검증 ─────────────────────────────────────────────
    try:
        spec = get_form_spec("manager_job_training_record")
        results.append(_check(isinstance(spec, dict), "get_form_spec() → dict"))
        results.append(_check(
            spec.get("display_name") == "안전보건관리자 직무교육 이수 확인서",
            "display_name 확인",
            repr(spec.get("display_name")),
        ))
        results.append(_check(
            isinstance(spec.get("required_fields"), list)
            and len(spec["required_fields"]) > 0,
            "required_fields 비어있지 않음",
        ))
        results.append(_check(
            spec.get("repeat_field") is None,
            "repeat_field is None (단일 레코드 서식)",
        ))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ─────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("manager_job_training_record", SAMPLE_ED004_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ─────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("manager_job_training_record", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~8. 전체 샘플 workbook 검증 ─────────────────────────────────────
    try:
        full_bytes = build_form_excel("manager_job_training_record", SAMPLE_ED004_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        from io import BytesIO
        from openpyxl import load_workbook
        wb_full = load_workbook(BytesIO(full_bytes))
        all_vals = [
            str(cell.value or "")
            for ws_obj in wb_full.worksheets
            for r in ws_obj.iter_rows()
            for cell in r
        ]
        all_text = " ".join(all_vals)

        # 필수 섹션/제목/문구 포함
        for heading in ED004_REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 포함: '{heading}'",
            ))

        # 필수 고지 문구
        for phrase in ED004_REQUIRED_PHRASES:
            results.append(_check(
                phrase in all_text,
                f"필수 문구 포함: '{phrase}'",
            ))

        # 개인정보 과다 필드 없음
        for keyword in ED004_FORBIDDEN_PII:
            found = keyword in all_text
            results.append(_check(
                not found,
                f"개인정보 과다 필드 없음: '{keyword}'",
                "FAIL — 해당 문구 발견" if found else "",
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 9. ED-004 catalog 검증 ────────────────────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        ed004 = next((d for d in cat["documents"] if d["id"] == "ED-004"), None)

        results.append(_check(ed004 is not None, "catalog: ED-004 항목 존재"))

        if ed004:
            results.append(_check(
                ed004.get("implementation_status") == "DONE",
                "catalog: ED-004 implementation_status == DONE",
                repr(ed004.get("implementation_status")),
            ))
            results.append(_check(
                ed004.get("form_type") == "manager_job_training_record",
                "catalog: ED-004 form_type == 'manager_job_training_record'",
                repr(ed004.get("form_type")),
            ))
            ev_status = ed004.get("evidence_status", "")
            results.append(_check(
                ev_status in ED004_VALID_EV_STATUSES,
                f"catalog: ED-004 evidence_status in {ED004_VALID_EV_STATUSES}",
                repr(ev_status),
            ))

            # evidence_file 존재 확인
            ev_files = ed004.get("evidence_file") or []
            if isinstance(ev_files, str):
                ev_files = [ev_files]
            for efname in ED004_EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR_ED004 / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname[:50]}",
                    str(fpath) if not fpath.exists() else "",
                ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "ED-004 catalog 검증 중 예외", tb))

    # ── 10. training_types.yml 3종 코드 검증 ─────────────────────────────
    try:
        import yaml
        tt_path = Path("data/masters/safety/training/training_types.yml")
        with open(tt_path, encoding="utf-8") as f:
            tt = yaml.safe_load(f)
        tt_codes = {t["training_code"] for t in tt["training_types"]}

        for code in ED004_TRAINING_CODES:
            results.append(_check(
                code in tt_codes,
                f"training_types: {code} 등록됨",
            ))
            if code in tt_codes:
                entry = next(t for t in tt["training_types"] if t["training_code"] == code)
                results.append(_check(
                    entry.get("related_document_id") == "ED-004",
                    f"training_types: {code} → related_document_id == 'ED-004'",
                    repr(entry.get("related_document_id")),
                ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "training_types.yml 검증 중 예외", tb))

    # ── 11. evidence 파일 내용 검증 ───────────────────────────────────────
    for efname in ED004_EXPECTED_EVIDENCE_FILES:
        fpath = EVIDENCE_DIR_ED004 / efname
        if not fpath.exists():
            continue
        try:
            import json
            ev_data = json.loads(fpath.read_text(encoding="utf-8"))
            vr = ev_data.get("verification_result", "")
            results.append(_check(
                vr in ("VERIFIED", "PARTIAL_VERIFIED"),
                f"evidence 검증결과: {efname[:45]}... → {vr}",
            ))
        except Exception as exc:
            results.append(_check(False, f"evidence 파일 로딩: {efname[:45]}...", str(exc)))

    return results


# ---------------------------------------------------------------------------
# CL-001 샘플 form_data
# ---------------------------------------------------------------------------

SAMPLE_CL001_MINIMAL: dict = {
    "check_date": "2026-04-25",
    "work_location": "외부비계 A구간 (3층~7층)",
    "checker_name": "홍길동",
}

SAMPLE_CL001_FULL: dict = {
    "site_name": "테스트건설(주) 테스트현장",
    "project_name": "테스트현장 신축공사",
    "check_date": "2026-04-25",
    "work_date": "2026-04-25 ~ 2026-05-20",
    "checker_name": "홍길동",
    "supervisor_name": "이감독",
    "work_location": "외부비계 A구간 (3층~7층)",
    "scaffold_type": "강관비계",
    "scaffold_height": "21.0m",
    "scaffold_length": "45.0m",
    "scaffold_location": "건물 남측 외벽",
    "scaffold_work_type": "외부 마감 타일 공사",
    "pre_install_items": [
        {"item": "구조검토서 또는 조립도 작성 여부", "result": "○", "note": ""},
        {"item": "지반 침하·균열 및 지지 상태 확인 여부", "result": "○", "note": ""},
        {"item": "사용 자재 규격·수량 확인 여부", "result": "○", "note": ""},
        {"item": "작업 전 근로자 안전교육 실시 여부", "result": "○", "note": "TBM 실시"},
        {"item": "작업구역 출입통제 및 안전표지 설치 여부", "result": "○", "note": ""},
    ],
    "structure_items": [
        {"item": "비계 기둥 수직도 적합 여부", "result": "○", "note": ""},
        {"item": "벽이음 설치 간격 기준 충족 여부", "result": "○", "note": ""},
        {"item": "가새 설치 상태 (X형 또는 V형 적정 여부)", "result": "○", "note": ""},
        {"item": "받침철물(베이스플레이트) 및 깔판 설치 여부", "result": "○", "note": ""},
        {"item": "부재 손상·변형·부식 없음 여부", "result": "○", "note": ""},
    ],
    "nonconformance_items": [],
    "inspector_sign": "홍길동",
    "supervisor_sign": "이감독",
    "manager_sign": "최소장",
    "sign_date": "2026-04-25",
}

# CL-001 필수 섹션 제목
CL001_REQUIRED_HEADINGS = [
    "비계 설치 점검표",
    "① 현장 기본정보",
    "② 비계 기본정보",
    "③ 설치 전 확인사항",
    "④ 구조·재료 점검",
    "⑤ 작업발판·승강설비 점검",
    "⑥ 안전난간·낙하물 방지 점검",
    "⑦ 조립·해체·변경 작업 점검",
    "⑧ 사용 전·사용 중 점검 결과",
    "⑨ 부적합 및 시정조치",
    "⑩ 확인 서명",
]

# CL-001 필수 고정 문구
CL001_REQUIRED_PHRASES = [
    "거푸집동바리 점검은 CL-002 별도 서식으로 관리한다",
    "법령 조항 및 기준은 현행 법령 원문 확인 후 현장에 적용한다",
    "점검 결과 부적합 사항은 사용 전 시정 완료 후 확인 서명을 받아야 한다",
]

# CL-001 evidence ID
CL001_EXPECTED_EVIDENCE_IDS = ["CL-001-L1", "CL-001-L2"]

# CL-001 evidence 파일명
CL001_EXPECTED_EVIDENCE_FILES = [
    "CL-001-L1_safety_rule_article_57_scaffold.json",
    "CL-001-L2_safety_rule_scaffold_workboard_railing.json",
]

CL001_VALID_EV_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED"}


def run_cl001_smoke_test() -> list[tuple[str, str, str]]:
    """CL-001 비계 설치 점검표 smoke test. 결과 list 반환."""
    results: list[tuple[str, str, str]] = []
    supported = {f["form_type"] for f in list_supported_forms()}

    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "scaffold_installation_checklist" in supported,
        "registry: scaffold_installation_checklist 등록됨",
    ))

    # ── 2. get_form_spec 검증 ─────────────────────────────────────────────
    try:
        spec = get_form_spec("scaffold_installation_checklist")
        results.append(_check(isinstance(spec, dict), "get_form_spec() → dict"))
        results.append(_check(
            spec.get("display_name") == "비계 설치 점검표",
            "display_name 확인",
            repr(spec.get("display_name")),
        ))
        results.append(_check(
            isinstance(spec.get("required_fields"), list)
            and len(spec["required_fields"]) > 0,
            "required_fields 비어있지 않음",
        ))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ─────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("scaffold_installation_checklist", SAMPLE_CL001_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ─────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("scaffold_installation_checklist", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~7. 전체 샘플 workbook 검증 ─────────────────────────────────────
    try:
        full_bytes = build_form_excel("scaffold_installation_checklist", SAMPLE_CL001_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        from io import BytesIO as _BytesIO
        from openpyxl import load_workbook as _load_wb
        wb_full = _load_wb(_BytesIO(full_bytes))
        all_vals = [
            str(cell.value or "")
            for ws_obj in wb_full.worksheets
            for r in ws_obj.iter_rows()
            for cell in r
        ]
        all_text = " ".join(all_vals)

        # 섹션 제목 10개 포함 확인
        for heading in CL001_REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 제목 포함: '{heading}'",
            ))

        # 고정 문구 3개 포함 확인
        for phrase in CL001_REQUIRED_PHRASES:
            results.append(_check(
                phrase in all_text,
                f"고정 문구 포함: '{phrase[:35]}...'",
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 8. CL-001 catalog 검증 ────────────────────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        cl001 = next((d for d in cat["documents"] if d["id"] == "CL-001"), None)
        cl002 = next((d for d in cat["documents"] if d["id"] == "CL-002"), None)

        results.append(_check(cl001 is not None, "catalog: CL-001 항목 존재"))

        if cl001:
            results.append(_check(
                cl001.get("implementation_status") == "DONE",
                "catalog: CL-001 implementation_status == DONE",
                repr(cl001.get("implementation_status")),
            ))
            results.append(_check(
                cl001.get("form_type") == "scaffold_installation_checklist",
                "catalog: CL-001 form_type == 'scaffold_installation_checklist'",
                repr(cl001.get("form_type")),
            ))
            ev_status = cl001.get("evidence_status", "")
            results.append(_check(
                ev_status in CL001_VALID_EV_STATUSES,
                f"catalog: CL-001 evidence_status in {CL001_VALID_EV_STATUSES}",
                repr(ev_status),
            ))
            ev_ids = cl001.get("evidence_id") or []
            for eid in CL001_EXPECTED_EVIDENCE_IDS:
                results.append(_check(
                    eid in ev_ids,
                    f"catalog: evidence_id 포함 — {eid}",
                ))
            # evidence_file 존재 확인
            for efname in CL001_EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname[:50]}",
                    str(fpath) if not fpath.exists() else "",
                ))

        # CL-002 상태 확인 (DONE — CL-002 구현 완료)
        results.append(_check(cl002 is not None, "catalog: CL-002 항목 존재"))
        if cl002:
            results.append(_check(
                cl002.get("implementation_status") == "DONE",
                "catalog: CL-002 implementation_status == DONE",
                repr(cl002.get("implementation_status")),
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "CL-001 catalog 검증 중 예외", tb))

    # ── 9. evidence 파일 내용 검증 ───────────────────────────────────────
    for efname in CL001_EXPECTED_EVIDENCE_FILES:
        fpath = EVIDENCE_DIR / efname
        if not fpath.exists():
            continue
        try:
            ev_data = json.loads(fpath.read_text(encoding="utf-8"))
            vr = ev_data.get("verification_result", "")
            results.append(_check(
                vr in ("VERIFIED", "PARTIAL_VERIFIED", "NEEDS_VERIFICATION"),
                f"evidence 검증결과 유효값: {efname[:45]}... → {vr}",
            ))
        except Exception as exc:
            results.append(_check(False, f"evidence 파일 로딩: {efname[:45]}...", str(exc)))

    return results


# ---------------------------------------------------------------------------
# CL-006 샘플 form_data
# ---------------------------------------------------------------------------

SAMPLE_CL006_MINIMAL: dict = {
    "check_date": "2026-04-25",
    "work_location": "A동 북측 타워크레인 (TC-01)",
    "checker_name": "홍길동",
}

SAMPLE_CL006_FULL: dict = {
    "site_name": "테스트건설(주) 테스트현장",
    "project_name": "테스트현장 신축공사",
    "check_date": "2026-04-25",
    "work_date": "2026-04-25",
    "checker_name": "홍길동",
    "supervisor_name": "이감독",
    "work_location": "A동 북측 타워크레인 (TC-01)",
    "crane_model": "POTAIN MCT 385",
    "crane_reg_no": "TC-2024-0001",
    "crane_capacity": "16ton",
    "crane_height": "78.0m",
    "crane_work_radius": "60.0m",
    "installation_date": "2026-01-15",
    "next_inspection_date": "2026-07-15",
    "operator_name": "김조종",
    "operator_license_no": "타워-2020-0001",
    "doc_check_items": [
        {"item": "설치검사 또는 정기검사 유효 여부", "result": "○", "note": "유효기간 2026-07-15"},
        {"item": "검사증·등록증 현장 비치 여부",     "result": "○", "note": ""},
        {"item": "타워크레인 작업계획서 작성 여부",   "result": "○", "note": ""},
        {"item": "장비사용계획서 작성 여부",          "result": "○", "note": ""},
        {"item": "제조사 사용설명서 현장 비치 여부",  "result": "○", "note": ""},
    ],
    "rope_check_items": [
        {"item": "와이어로프 마모·단선·킹크·부식 없음 여부", "result": "○", "note": ""},
        {"item": "와이어로프 윤활 상태 적정 여부",            "result": "○", "note": ""},
        {"item": "훅 해지장치 정상 작동 여부",                "result": "○", "note": ""},
        {"item": "권과방지장치 정상 작동 여부",               "result": "○", "note": ""},
        {"item": "과부하방지장치 정상 작동 여부",             "result": "○", "note": ""},
    ],
    "signal_check_items": [
        {"item": "신호수 배치 여부 (타워크레인마다)",  "result": "○", "note": "2명 배치"},
        {"item": "신호수 신호방법 및 신호 일치 여부", "result": "○", "note": ""},
        {"item": "조종자 자격·면허 유효 여부",         "result": "○", "note": ""},
        {"item": "정격하중 초과 인양 없음 여부",       "result": "○", "note": ""},
        {"item": "인양물 결박 및 슬링 상태 확인 여부", "result": "○", "note": ""},
    ],
    "nonconformance_items": [],
    "daily_inspector_sign": "홍길동",
    "operator_sign": "김조종",
    "supervisor_sign": "이감독",
    "manager_sign": "최소장",
    "sign_date": "2026-04-25",
}

# CL-006 필수 섹션 제목
CL006_REQUIRED_HEADINGS = [
    "타워크레인 자체 점검표",
    "① 현장 기본정보",
    "② 타워크레인 기본정보",
    "③ 검사·인증·서류 확인",
    "④ 설치 상태 점검",
    "⑤ 구조부·마스트·지브 점검",
    "⑥ 와이어로프·훅·권과방지장치 점검",
    "⑦ 브레이크·제동·리미트 장치 점검",
    "⑧ 전기·제어·비상정지장치 점검",
    "⑨ 작업반경·충돌방지·출입통제 점검",
    "⑩ 신호수·조종자·작업방법 점검",
    "⑪ 부적합 및 시정조치",
    "⑫ 확인 서명",
]

# CL-006 필수 포함 키워드
CL006_REQUIRED_KEYWORDS = [
    "이동식 크레인 점검표를 대체하지 않는다",
    "신호수",
    "충돌방지",
    "권과방지장치",
]

# CL-006 필수 고정 문구
CL006_REQUIRED_PHRASES = [
    "이동식 크레인 점검표를 대체하지 않는다",
]

# CL-006 evidence ID
CL006_EXPECTED_EVIDENCE_IDS = ["CL-006-L1", "CL-006-L2", "CL-006-L3"]

# CL-006 evidence 파일명
CL006_EXPECTED_EVIDENCE_FILES = [
    "CL-006-L1_safety_rule_articles_142_145_tower_crane.json",
    "CL-006-L2_safety_rule_article_146_crane_work.json",
    "CL-006-L3_safety_rule_crane_inspection_common.json",
]

CL006_VALID_EV_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED"}


def run_cl006_smoke_test() -> list[tuple[str, str, str]]:
    """CL-006 타워크레인 자체 점검표 smoke test. 결과 list 반환."""
    results: list[tuple[str, str, str]] = []
    supported = {f["form_type"] for f in list_supported_forms()}

    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "tower_crane_self_inspection_checklist" in supported,
        "registry: tower_crane_self_inspection_checklist 등록됨",
    ))

    # ── 2. get_form_spec 검증 ─────────────────────────────────────────────
    try:
        spec = get_form_spec("tower_crane_self_inspection_checklist")
        results.append(_check(isinstance(spec, dict), "get_form_spec() → dict"))
        results.append(_check(
            spec.get("display_name") == "타워크레인 자체 점검표",
            "display_name 확인",
            repr(spec.get("display_name")),
        ))
        results.append(_check(
            isinstance(spec.get("required_fields"), list)
            and len(spec["required_fields"]) > 0,
            "required_fields 비어있지 않음",
        ))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ─────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("tower_crane_self_inspection_checklist", SAMPLE_CL006_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ─────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("tower_crane_self_inspection_checklist", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~7. 전체 샘플 workbook 검증 ─────────────────────────────────────
    try:
        full_bytes = build_form_excel("tower_crane_self_inspection_checklist", SAMPLE_CL006_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        from io import BytesIO as _BytesIO
        from openpyxl import load_workbook as _load_wb
        wb_full = _load_wb(_BytesIO(full_bytes))
        all_vals = [
            str(cell.value or "")
            for ws_obj in wb_full.worksheets
            for r in ws_obj.iter_rows()
            for cell in r
        ]
        all_text = " ".join(all_vals)

        # 섹션 제목 12개 + 제목 포함 확인
        for heading in CL006_REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 제목 포함: '{heading}'",
            ))

        # 필수 키워드 포함
        for kw in CL006_REQUIRED_KEYWORDS:
            results.append(_check(
                kw in all_text,
                f"필수 키워드 포함: '{kw}'",
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 8. CL-006 catalog 검증 ────────────────────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        cl006 = next((d for d in cat["documents"] if d["id"] == "CL-006"), None)
        cl001 = next((d for d in cat["documents"] if d["id"] == "CL-001"), None)
        cl002 = next((d for d in cat["documents"] if d["id"] == "CL-002"), None)

        results.append(_check(cl006 is not None, "catalog: CL-006 항목 존재"))

        if cl006:
            results.append(_check(
                cl006.get("implementation_status") == "DONE",
                "catalog: CL-006 implementation_status == DONE",
                repr(cl006.get("implementation_status")),
            ))
            results.append(_check(
                cl006.get("form_type") == "tower_crane_self_inspection_checklist",
                "catalog: CL-006 form_type == 'tower_crane_self_inspection_checklist'",
                repr(cl006.get("form_type")),
            ))
            ev_status = cl006.get("evidence_status", "")
            results.append(_check(
                ev_status in CL006_VALID_EV_STATUSES,
                f"catalog: CL-006 evidence_status in {CL006_VALID_EV_STATUSES}",
                repr(ev_status),
            ))
            ev_ids = cl006.get("evidence_id") or []
            for eid in CL006_EXPECTED_EVIDENCE_IDS:
                results.append(_check(
                    eid in ev_ids,
                    f"catalog: evidence_id 포함 — {eid}",
                ))
            for efname in CL006_EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname[:55]}",
                    str(fpath) if not fpath.exists() else "",
                ))

        # CL-001, CL-002 상태 변경 없음 확인
        if cl001:
            results.append(_check(
                cl001.get("implementation_status") == "DONE",
                "catalog: CL-001 상태 변경 없음 (== DONE)",
                repr(cl001.get("implementation_status")),
            ))
        if cl002:
            results.append(_check(
                cl002.get("implementation_status") == "DONE",
                "catalog: CL-002 상태 변경 없음 (== DONE)",
                repr(cl002.get("implementation_status")),
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "CL-006 catalog 검증 중 예외", tb))

    # ── 9. evidence 파일 내용 검증 ───────────────────────────────────────
    for efname in CL006_EXPECTED_EVIDENCE_FILES:
        fpath = EVIDENCE_DIR / efname
        if not fpath.exists():
            continue
        try:
            ev_data = json.loads(fpath.read_text(encoding="utf-8"))
            vr = ev_data.get("verification_result", "")
            results.append(_check(
                vr in ("VERIFIED", "PARTIAL_VERIFIED", "NEEDS_VERIFICATION"),
                f"evidence 검증결과 유효값: {efname[:50]}... → {vr}",
            ))
        except Exception as exc:
            results.append(_check(False, f"evidence 파일 로딩: {efname[:50]}...", str(exc)))

    return results


# ---------------------------------------------------------------------------
# CL-002 샘플 form_data
# ---------------------------------------------------------------------------

SAMPLE_CL002_MINIMAL: dict = {
    "check_date":    "2026-04-25",
    "work_location": "지상 3층 슬래브",
    "checker_name":  "홍길동",
}

SAMPLE_CL002_FULL: dict = {
    "site_name":            "테스트건설(주) 테스트현장",
    "project_name":         "테스트현장 신축공사",
    "check_date":           "2026-04-25",
    "work_location":        "지상 3층 슬래브",
    "work_date":            "2026-04-25 ~ 2026-04-26",
    "supervisor_name":      "이감독",
    "structure_type":       "슬래브",
    "floor_level":          "지상 3층",
    "work_area":            "A동 북측",
    "formwork_type":        "합판 거푸집",
    "shoring_type":         "시스템동바리",
    "checker_name":         "홍길동",
    "inspector_sign":       "홍길동",
    "supervisor_sign":      "이감독",
    "work_commander_sign":  "박지휘",
    "manager_sign":         "장소장",
    "sign_date":            "2026-04-25",
    "nonconformance_items": [
        {
            "content":   "3번 동바리 베이스플레이트 미설치",
            "location":  "A동 북측 3열",
            "action":    "베이스플레이트 추가 설치",
            "deadline":  "2026-04-25",
            "completed": "완료",
        }
    ],
}

# CL-002 필수 섹션 제목 (13개)
CL002_REQUIRED_HEADINGS = [
    "거푸집 및 동바리 설치 점검표",
    "1. 현장 기본정보",
    "2. 구조물 및 작업구간 정보",
    "3. 조립도·작업계획서 확인",
    "4. 재료 및 부재 상태 점검",
    "5. 동바리 설치 상태 점검",
    "6. 거푸집 설치 상태 점검",
    "7. 침하·전도·변형 방지 조치",
    "8. 작업발판·통로·추락방지 조치",
    "9. 콘크리트 타설 전 점검",
    "10. 콘크리트 타설 중 점검",
    "11. 해체 전 안전조치",
    "12. 부적합 및 시정조치",
    "13. 확인 서명",
]

# CL-002 필수 고정 문구
CL002_REQUIRED_PHRASES = [
    "비계 점검표(CL-001)를 대체하지 않는다",
    "조립도와 작업계획서에 따라 설치·점검한다",
    "콘크리트 타설 전 부적합 사항은 사용 전 시정 완료 후 재확인한다",
    "법령 조항은 현행 원문 확인 후 현장에 적용한다",
]

# CL-002 필수 키워드 (조립도, 콘크리트, 해체)
CL002_REQUIRED_KEYWORDS = [
    "조립도",
    "콘크리트 타설 전 점검",
    "해체 전 안전조치",
]

# CL-002 evidence
CL002_EXPECTED_EVIDENCE_IDS = ["CL-002-L1", "CL-002-L2", "CL-002-L3"]
CL002_EXPECTED_EVIDENCE_FILES = [
    "CL-002-L1_safety_rule_articles_328_330_formwork_material.json",
    "CL-002-L2_safety_rule_articles_331_333_assembly_drawing.json",
    "CL-002-L3_safety_rule_articles_334_337_concrete_pour.json",
]
CL002_VALID_EV_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED"}


def run_cl002_smoke_test() -> list[tuple[str, str, str]]:
    """CL-002 거푸집 및 동바리 설치 점검표 smoke test. 결과 list 반환."""
    results: list[tuple[str, str, str]] = []
    supported = {f["form_type"] for f in list_supported_forms()}

    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "formwork_shoring_installation_checklist" in supported,
        "registry: formwork_shoring_installation_checklist 등록됨",
    ))

    # ── 2. get_form_spec 검증 ─────────────────────────────────────────────
    try:
        spec = get_form_spec("formwork_shoring_installation_checklist")
        results.append(_check(isinstance(spec, dict), "get_form_spec() → dict"))
        results.append(_check(
            spec.get("display_name") == "거푸집 및 동바리 설치 점검표",
            "display_name 확인",
            repr(spec.get("display_name")),
        ))
        results.append(_check(
            isinstance(spec.get("required_fields"), list)
            and len(spec["required_fields"]) > 0,
            "required_fields 비어있지 않음",
        ))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ─────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("formwork_shoring_installation_checklist", SAMPLE_CL002_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ─────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("formwork_shoring_installation_checklist", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~11. 전체 샘플 workbook 검증 ────────────────────────────────────
    try:
        full_bytes = build_form_excel("formwork_shoring_installation_checklist", SAMPLE_CL002_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        from io import BytesIO as _BytesIO
        from openpyxl import load_workbook as _load_wb
        wb_full = _load_wb(_BytesIO(full_bytes))
        all_vals = [
            str(cell.value or "")
            for ws_obj in wb_full.worksheets
            for r in ws_obj.iter_rows()
            for cell in r
        ]
        all_text = " ".join(all_vals)

        # 시트명에 "거푸집" 또는 "동바리" 포함
        sheet_names = wb_full.sheetnames
        results.append(_check(
            any("거푸집" in n or "동바리" in n for n in sheet_names),
            f"시트명 확인 — {sheet_names}",
        ))

        # 섹션 제목 13개 포함
        for heading in CL002_REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 제목 포함: '{heading}'",
            ))

        # 필수 고정 문구 4개 포함
        for phrase in CL002_REQUIRED_PHRASES:
            results.append(_check(
                phrase in all_text,
                f"고정 문구 포함: '{phrase[:50]}...'",
            ))

        # 필수 키워드 포함
        for kw in CL002_REQUIRED_KEYWORDS:
            results.append(_check(
                kw in all_text,
                f"필수 키워드 포함: '{kw}'",
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 12. catalog + evidence 검증 ──────────────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        cl002 = next((d for d in cat["documents"] if d["id"] == "CL-002"), None)
        cl001 = next((d for d in cat["documents"] if d["id"] == "CL-001"), None)
        cl003 = next((d for d in cat["documents"] if d["id"] == "CL-003"), None)
        cl006 = next((d for d in cat["documents"] if d["id"] == "CL-006"), None)

        results.append(_check(cl002 is not None, "catalog: CL-002 항목 존재"))

        if cl002:
            results.append(_check(
                cl002.get("implementation_status") == "DONE",
                "catalog: CL-002 implementation_status == DONE",
                repr(cl002.get("implementation_status")),
            ))
            results.append(_check(
                cl002.get("form_type") == "formwork_shoring_installation_checklist",
                "catalog: CL-002 form_type == 'formwork_shoring_installation_checklist'",
                repr(cl002.get("form_type")),
            ))
            ev_status = cl002.get("evidence_status", "")
            results.append(_check(
                ev_status in CL002_VALID_EV_STATUSES,
                f"catalog: CL-002 evidence_status in {CL002_VALID_EV_STATUSES}",
                repr(ev_status),
            ))

            # evidence_id 3개 포함
            ev_ids = cl002.get("evidence_id") or []
            if isinstance(ev_ids, str):
                ev_ids = [ev_ids]
            for eid in CL002_EXPECTED_EVIDENCE_IDS:
                results.append(_check(
                    eid in ev_ids,
                    f"catalog: evidence_id 포함 — {eid}",
                ))

            # evidence_file 실제 존재 확인
            for efname in CL002_EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname[:65]}",
                    str(fpath) if not fpath.exists() else "",
                ))

        # CL-001, CL-003, CL-006 상태 변경 없음 확인
        if cl001:
            results.append(_check(
                cl001.get("implementation_status") == "DONE",
                "CL-001 상태 변경 없음 (DONE 유지)",
                repr(cl001.get("implementation_status")),
            ))
        if cl003:
            results.append(_check(
                cl003.get("implementation_status") == "DONE",
                "CL-003 상태 변경 없음 (DONE 유지)",
                repr(cl003.get("implementation_status")),
            ))
        if cl006:
            results.append(_check(
                cl006.get("implementation_status") == "DONE",
                "CL-006 상태 변경 없음 (DONE 유지)",
                repr(cl006.get("implementation_status")),
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "CL-002 catalog/evidence 검증 중 예외", tb))

    # ── 13. evidence 파일 내용 검증 ───────────────────────────────────────
    for efname in CL002_EXPECTED_EVIDENCE_FILES:
        fpath = EVIDENCE_DIR / efname
        if not fpath.exists():
            continue
        try:
            ev_data = json.loads(fpath.read_text(encoding="utf-8"))
            vr = ev_data.get("verification_result", "")
            results.append(_check(
                vr in ("VERIFIED", "PARTIAL_VERIFIED", "NEEDS_VERIFICATION"),
                f"evidence 검증결과 유효값: {efname[:60]}... → {vr}",
            ))
        except Exception as exc:
            results.append(_check(False, f"evidence 파일 로딩: {efname[:60]}...", str(exc)))

    return results


# ---------------------------------------------------------------------------
# CL-003 샘플 form_data
# ---------------------------------------------------------------------------

SAMPLE_CL003_MINIMAL: dict = {
    "check_date":    "2026-04-25",
    "work_location": "테스트현장 1공구",
    "checker_name":  "홍길동",
}

SAMPLE_CL003_FULL: dict = {
    "site_name":            "테스트건설(주) 테스트현장",
    "project_name":         "테스트현장 신축공사",
    "check_date":           "2026-04-25",
    "work_location":        "1공구 굴착구간",
    "equipment_type":       "지게차",
    "equipment_model":      "현대 20BH",
    "equipment_reg_no":     "12가 3456",
    "equipment_capacity":   "2.0 ton",
    "operator_name":        "이운전",
    "operator_license_no":  "지게차운전기능사 제2020-12345호",
    "guide_worker_name":    "김유도",
    "work_commander_name":  "박지휘",
    "checker_name":         "홍길동",
    "operator_sign":        "이운전",
    "guide_worker_sign":    "김유도",
    "work_commander_sign":  "박지휘",
    "supervisor_sign":      "최감독",
    "manager_sign":         "장소장",
    "sign_date":            "2026-04-25",
    "nonconformance_items": [
        {
            "content":   "좌측 후미등 작동 불량",
            "location":  "후미등 좌측",
            "action":    "교체 조치",
            "deadline":  "2026-04-25",
            "completed": "완료",
        }
    ],
}

# CL-003 필수 섹션 제목 (13개)
CL003_REQUIRED_HEADINGS = [
    "건설장비 일일 사전점검표",
    "1. 현장 기본정보",
    "2. 장비 기본정보",
    "3. 운전자·유도자·작업지휘자 확인",
    "4. 서류·검사·보험 확인",
    "5. 외관·누유·타이어/궤도 점검",
    "6. 전조등·후미등·경광등·후진경보기 점검",
    "7. 제동장치·조향장치·비상정지 점검",
    "8. 전도·전락·지반 상태 점검",
    "9. 접촉·충돌·작업반경 통제 점검",
    "10. 적재·인양·하역 상태 점검",
    "11. 장비별 추가 점검",
    "12. 부적합 및 시정조치",
    "13. 확인 서명",
]

# CL-003 필수 고정 문구
CL003_REQUIRED_PHRASES = [
    "작업계획서 및 장비사용계획서를 대체하지 않는다",
    "타워크레인, 이동식 크레인, 비계, 거푸집동바리 전용 점검은 별도 서식으로 관리한다",
    "부적합 사항은 사용 전 시정 완료 후 재확인한다",
    "법령 조항은 현행 원문 확인 후 현장에 적용한다",
]

# CL-003 장비별 추가 점검 — 지게차 필수 포함 항목 키워드
CL003_FORKLIFT_KEYWORDS = [
    "후진경보기",
    "헤드가드",
    "백레스트",
    "좌석안전띠",
    "포크",
]

# CL-003 evidence
CL003_EXPECTED_EVIDENCE_IDS = ["CL-003-L1", "CL-003-L2", "CL-003-L3"]
CL003_EXPECTED_EVIDENCE_FILES = [
    "CL-003-L1_safety_rule_vehicle_construction_equipment.json",
    "CL-003-L2_safety_rule_material_handling_equipment_common.json",
    "CL-003-L3_safety_rule_forklift_specific.json",
]
CL003_VALID_EV_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED"}


def run_cl003_smoke_test() -> list[tuple[str, str, str]]:
    """CL-003 건설장비 일일 사전점검표 smoke test. 결과 list 반환."""
    results: list[tuple[str, str, str]] = []
    supported = {f["form_type"] for f in list_supported_forms()}

    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "construction_equipment_daily_checklist" in supported,
        "registry: construction_equipment_daily_checklist 등록됨",
    ))

    # ── 2. get_form_spec 검증 ─────────────────────────────────────────────
    try:
        spec = get_form_spec("construction_equipment_daily_checklist")
        results.append(_check(isinstance(spec, dict), "get_form_spec() → dict"))
        results.append(_check(
            spec.get("display_name") == "건설장비 일일 사전점검표",
            "display_name 확인",
            repr(spec.get("display_name")),
        ))
        results.append(_check(
            isinstance(spec.get("required_fields"), list)
            and len(spec["required_fields"]) > 0,
            "required_fields 비어있지 않음",
        ))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ─────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("construction_equipment_daily_checklist", SAMPLE_CL003_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ─────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("construction_equipment_daily_checklist", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~11. 전체 샘플 workbook 검증 ────────────────────────────────────
    try:
        full_bytes = build_form_excel("construction_equipment_daily_checklist", SAMPLE_CL003_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        from io import BytesIO as _BytesIO
        from openpyxl import load_workbook as _load_wb
        wb_full = _load_wb(_BytesIO(full_bytes))
        all_vals = [
            str(cell.value or "")
            for ws_obj in wb_full.worksheets
            for r in ws_obj.iter_rows()
            for cell in r
        ]
        all_text = " ".join(all_vals)

        # 시트 이름에 "건설장비" 또는 "점검" 포함
        sheet_names = wb_full.sheetnames
        results.append(_check(
            any("건설장비" in n or "점검" in n for n in sheet_names),
            f"시트명 확인 — {sheet_names}",
        ))

        # 섹션 제목 13개 포함
        for heading in CL003_REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 제목 포함: '{heading}'",
            ))

        # 필수 고정 문구 4개 포함
        for phrase in CL003_REQUIRED_PHRASES:
            results.append(_check(
                phrase in all_text,
                f"고정 문구 포함: '{phrase[:45]}...'",
            ))

        # 지게차 추가 점검 키워드 확인 (equipment_type = 지게차)
        for kw in CL003_FORKLIFT_KEYWORDS:
            results.append(_check(
                kw in all_text,
                f"지게차 점검 키워드 포함: '{kw}'",
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 12. catalog + evidence 검증 ──────────────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        cl003 = next((d for d in cat["documents"] if d["id"] == "CL-003"), None)
        cl001 = next((d for d in cat["documents"] if d["id"] == "CL-001"), None)
        cl002 = next((d for d in cat["documents"] if d["id"] == "CL-002"), None)
        cl006 = next((d for d in cat["documents"] if d["id"] == "CL-006"), None)

        results.append(_check(cl003 is not None, "catalog: CL-003 항목 존재"))

        if cl003:
            results.append(_check(
                cl003.get("implementation_status") == "DONE",
                "catalog: CL-003 implementation_status == DONE",
                repr(cl003.get("implementation_status")),
            ))
            results.append(_check(
                cl003.get("form_type") == "construction_equipment_daily_checklist",
                "catalog: CL-003 form_type == 'construction_equipment_daily_checklist'",
                repr(cl003.get("form_type")),
            ))
            ev_status = cl003.get("evidence_status", "")
            results.append(_check(
                ev_status in CL003_VALID_EV_STATUSES,
                f"catalog: CL-003 evidence_status in {CL003_VALID_EV_STATUSES}",
                repr(ev_status),
            ))

            # evidence_id 3개 포함
            ev_ids = cl003.get("evidence_id") or []
            if isinstance(ev_ids, str):
                ev_ids = [ev_ids]
            for eid in CL003_EXPECTED_EVIDENCE_IDS:
                results.append(_check(
                    eid in ev_ids,
                    f"catalog: evidence_id 포함 — {eid}",
                ))

            # evidence_file 실제 존재 확인
            for efname in CL003_EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname[:60]}",
                    str(fpath) if not fpath.exists() else "",
                ))

        # CL-001, CL-002, CL-006 상태 변경 없음 확인
        if cl001:
            results.append(_check(
                cl001.get("implementation_status") == "DONE",
                "CL-001 상태 변경 없음 (DONE 유지)",
                repr(cl001.get("implementation_status")),
            ))
        if cl002:
            results.append(_check(
                cl002.get("implementation_status") == "DONE",
                "CL-002 상태 변경 없음 (DONE 유지)",
                repr(cl002.get("implementation_status")),
            ))
        if cl006:
            results.append(_check(
                cl006.get("implementation_status") == "DONE",
                "CL-006 상태 변경 없음 (DONE 유지)",
                repr(cl006.get("implementation_status")),
            ))

    except Exception as exc:
        import traceback as _tb
        tb = _tb.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "CL-003 catalog/evidence 검증 중 예외", tb))

    # ── 13. evidence 파일 내용 검증 ───────────────────────────────────────
    for efname in CL003_EXPECTED_EVIDENCE_FILES:
        fpath = EVIDENCE_DIR / efname
        if not fpath.exists():
            continue
        try:
            ev_data = json.loads(fpath.read_text(encoding="utf-8"))
            vr = ev_data.get("verification_result", "")
            results.append(_check(
                vr in ("VERIFIED", "PARTIAL_VERIFIED", "NEEDS_VERIFICATION"),
                f"evidence 검증결과 유효값: {efname[:55]}... → {vr}",
            ))
        except Exception as exc:
            results.append(_check(False, f"evidence 파일 로딩: {efname[:55]}...", str(exc)))

    return results


def run_smoke_test() -> None:
    results: list[tuple[str, str, str]] = []
    overall = "PASS"

    supported = {f["form_type"] for f in list_supported_forms()}

    # ════════════════════════════════════════════════════════════
    # ED-003 검증
    # ════════════════════════════════════════════════════════════

    # ── 1. registry 등록 확인 ────────────────────────────────────────────
    results.append(_check(
        "special_education_log" in supported,
        "registry: special_education_log 등록됨",
    ))

    # ── 2. get_form_spec 검증 ────────────────────────────────────────────
    try:
        spec = get_form_spec("special_education_log")
        results.append(_check(isinstance(spec, dict),
                               "get_form_spec() → dict"))
        results.append(_check(spec.get("display_name") == "특별 안전보건교육 교육일지",
                               "display_name 확인",
                               repr(spec.get("display_name"))))
        results.append(_check(isinstance(spec.get("required_fields"), list)
                               and len(spec["required_fields"]) > 0,
                               "required_fields 비어있지 않음"))
        results.append(_check(spec.get("repeat_field") == "attendees",
                               "repeat_field == 'attendees'"))
        results.append(_check(spec.get("max_repeat_rows") == 30,
                               "max_repeat_rows == 30"))
    except Exception as exc:
        results.append(_check(False, "get_form_spec() 호출 성공", str(exc)))

    # ── 3. 최소 샘플 → bytes ────────────────────────────────────────────
    try:
        xlsx_bytes = build_form_excel("special_education_log", SAMPLE_ED003_MINIMAL)
        results.append(_check(
            isinstance(xlsx_bytes, bytes) and len(xlsx_bytes) > 0,
            "최소 샘플 → bytes 생성",
            f"{len(xlsx_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "최소 샘플 → bytes 생성", str(exc)))

    # ── 4. 공란 form_data → bytes ────────────────────────────────────────
    try:
        empty_bytes = build_form_excel("special_education_log", {})
        results.append(_check(
            isinstance(empty_bytes, bytes) and len(empty_bytes) > 0,
            "공란 form_data → bytes 생성 (오류 없음)",
            f"{len(empty_bytes):,} bytes",
        ))
    except Exception as exc:
        results.append(_check(False, "공란 form_data → bytes 생성", str(exc)))

    # ── 5~8. 전체 샘플 workbook 검증 ────────────────────────────────────
    try:
        full_bytes = build_form_excel("special_education_log", SAMPLE_ED003_FULL)
        results.append(_check(
            isinstance(full_bytes, bytes) and len(full_bytes) > 0,
            "전체 샘플 → bytes 생성",
            f"{len(full_bytes):,} bytes",
        ))
        wb_full = load_workbook(BytesIO(full_bytes))
        all_vals = _all_cell_values(wb_full)
        all_text = " ".join(all_vals)

        # 섹션 제목 포함
        for heading in REQUIRED_HEADINGS:
            results.append(_check(
                heading in all_text,
                f"섹션 제목 포함: '{heading}'",
            ))

        # 개인정보 과다 필드 없음
        for keyword in FORBIDDEN_PII_KEYWORDS:
            found = keyword in all_text
            results.append(_check(
                not found,
                f"개인정보 과다 필드 없음: '{keyword}'",
                "FAIL — 기본 필드명에 해당 문구 발견" if found else "",
            ))

        # 별표 4/5 기준 문구 포함 (VERIFIED 상태)
        for kw in REQUIRED_BYEOLPYO_KEYWORDS:
            results.append(_check(
                kw in all_text,
                f"별표 기준 문구 포함: '{kw}'",
            ))

    except Exception as exc:
        tb = traceback.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "전체 샘플 처리 중 예외", tb))

    # ── 9~15. ED-003 catalog + evidence 검증 ────────────────────────────
    try:
        import yaml
        catalog_path = Path("data/masters/safety/documents/document_catalog.yml")
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        ed003 = next(
            (d for d in cat["documents"] if d["id"] == "ED-003"), None
        )

        # 9. catalog 존재
        results.append(_check(ed003 is not None, "catalog: ED-003 항목 존재"))

        if ed003:
            # 10. implementation_status == DONE
            results.append(_check(
                ed003.get("implementation_status") == "DONE",
                "catalog: ED-003 implementation_status == DONE",
                repr(ed003.get("implementation_status")),
            ))
            # form_type 확인
            results.append(_check(
                ed003.get("form_type") == "special_education_log",
                "catalog: ED-003 form_type == 'special_education_log'",
                repr(ed003.get("form_type")),
            ))
            # 11. evidence_status VERIFIED 또는 PARTIAL_VERIFIED
            ev_status = ed003.get("evidence_status", "")
            results.append(_check(
                ev_status in VALID_EVIDENCE_STATUSES,
                f"catalog: ED-003 evidence_status in {VALID_EVIDENCE_STATUSES}",
                repr(ev_status),
            ))

            # 12. evidence_id 4개 포함
            ev_ids = ed003.get("evidence_id") or []
            if isinstance(ev_ids, str):
                ev_ids = [ev_ids]
            for eid in EXPECTED_EVIDENCE_IDS:
                results.append(_check(
                    eid in ev_ids,
                    f"catalog: evidence_id 포함 — {eid}",
                ))

            # 13. evidence_file 실제 존재 확인
            ev_files = ed003.get("evidence_file") or []
            if isinstance(ev_files, str):
                ev_files = [ev_files]
            for efname in EXPECTED_EVIDENCE_FILES:
                fpath = EVIDENCE_DIR / efname
                results.append(_check(
                    fpath.exists(),
                    f"evidence_file 존재: {efname}",
                    str(fpath) if not fpath.exists() else "",
                ))

        # 14~15. 각 evidence 파일 내용 검증
        for efname in EXPECTED_EVIDENCE_FILES:
            fpath = EVIDENCE_DIR / efname
            if not fpath.exists():
                continue
            try:
                ev_data = json.loads(fpath.read_text(encoding="utf-8"))
                vr = ev_data.get("verification_result", "")
                results.append(_check(
                    vr in ("VERIFIED", "PARTIAL_VERIFIED"),
                    f"evidence 검증결과: {efname[:30]}... → {vr}",
                ))
                # 별표 4: special_education_hours 구조 확인
                if "table_4" in efname:
                    hours_data = ev_data.get("special_education_hours", {})
                    results.append(_check(
                        bool(hours_data.get("일반근로자")),
                        "별표 4: 일반근로자 특별교육 시간 구조화",
                        repr(hours_data.get("일반근로자", ""))[:60],
                    ))
                # 별표 5: range_phrase 확인
                if "table_5" in efname:
                    works_data = ev_data.get("special_education_target_works", {})
                    results.append(_check(
                        "제1호부터 제39호" in works_data.get("range_phrase", ""),
                        "별표 5: 대상 작업 범위 '제1호부터 제39호까지' 확인",
                        repr(works_data.get("range_phrase", ""))[:60],
                    ))
            except Exception as exc:
                results.append(_check(False, f"evidence 파일 로딩: {efname[:30]}...", str(exc)))

    except Exception as exc:
        tb = traceback.format_exc().strip().splitlines()[-1]
        results.append(_check(False, "catalog/evidence 검증 중 예외", tb))

    # ════════════════════════════════════════════════════════════
    # WP-015 검증
    # ════════════════════════════════════════════════════════════
    wp015_results = run_wp015_smoke_test()
    results.extend(wp015_results)

    # ════════════════════════════════════════════════════════════
    # ED-004 검증
    # ════════════════════════════════════════════════════════════
    ed004_results = run_ed004_smoke_test()
    results.extend(ed004_results)

    # ════════════════════════════════════════════════════════════
    # CL-001 검증
    # ════════════════════════════════════════════════════════════
    cl001_results = run_cl001_smoke_test()
    results.extend(cl001_results)

    # ════════════════════════════════════════════════════════════
    # CL-006 검증
    # ════════════════════════════════════════════════════════════
    cl006_results = run_cl006_smoke_test()
    results.extend(cl006_results)

    # ════════════════════════════════════════════════════════════
    # CL-003 검증
    # ════════════════════════════════════════════════════════════
    cl003_results = run_cl003_smoke_test()
    results.extend(cl003_results)

    # ════════════════════════════════════════════════════════════
    # CL-002 검증
    # ════════════════════════════════════════════════════════════
    cl002_results = run_cl002_smoke_test()
    results.extend(cl002_results)

    # ── 출력 ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 76)
    print("  KRAS P1 Smoke Test — ED-003 + WP-015 + ED-004 + CL-001 + CL-006 + CL-003 + CL-002")
    print("=" * 76)

    pass_cnt = warn_cnt = fail_cnt = 0
    for verdict, name, detail in results:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[verdict]
        line = f"  {icon} [{verdict}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)
        if verdict == "PASS":   pass_cnt += 1
        elif verdict == "WARN": warn_cnt += 1
        else:                   fail_cnt += 1; overall = "FAIL"

    print("-" * 62)
    total = len(results)
    print(f"  합계: PASS {pass_cnt}/{total}  WARN {warn_cnt}  FAIL {fail_cnt}")
    print(f"\n  최종 판정: {overall}")
    print("=" * 62 + "\n")

    sys.exit(0 if overall != "FAIL" else 1)


if __name__ == "__main__":
    run_smoke_test()

