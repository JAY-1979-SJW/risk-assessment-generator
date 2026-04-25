"""
audit_safety_gap.py
안전관리 갭 감사 스크립트 (read-only)
12개 축 기준으로 현재 마스터를 전수 대조하고 결과를 출력한다.
마스터 수정 없음. 출력만.
"""
import yaml
from pathlib import Path

BASE = Path(__file__).parent.parent
MASTERS = BASE / "data" / "masters" / "safety"

# ── 마스터 로드 ────────────────────────────────────────────────────────────

def load(rel):
    with open(MASTERS / rel, encoding="utf-8") as f:
        return yaml.safe_load(f)

doc_cat   = load("documents/document_catalog.yml")
eq_types  = load("equipment/equipment_types.yml")
tr_types  = load("training/training_types.yml")
ins_types = load("inspection/inspection_types.yml")
wk_types  = load("work_types.yml")
eq_doc    = load("mappings/equipment_document_requirements.yml")
eq_tr     = load("mappings/equipment_training_requirements.yml")
eq_ins    = load("mappings/equipment_inspection_requirements.yml")
wk_doc    = load("mappings/work_document_requirements.yml")
wk_tr     = load("mappings/work_training_requirements.yml")
cc        = load("compliance/compliance_clauses.yml")
cl        = load("compliance/compliance_links.yml")

# ── 인덱스 구성 ───────────────────────────────────────────────────────────

docs_by_id      = {d["id"]: d for d in doc_cat["documents"]}
docs_by_cat     = {}
for d in doc_cat["documents"]:
    c = d.get("category_code", "UNK")
    docs_by_cat.setdefault(c, []).append(d["id"])

eq_all_codes    = {e["code"] for t in eq_types["equipment_types"] for e in t.get("equipment", [])}
tr_codes        = {t["training_code"] for t in tr_types["training_types"]}
ins_codes       = {i["inspection_code"] for i in ins_types["inspection_types"]}
wk_codes        = {w["code"] for w in wk_types["work_types"]}

eq_doc_covered  = {r["equipment_code"] for r in eq_doc["requirements"]}
eq_tr_covered   = {r["equipment_code"] for r in eq_tr["requirements"]}
eq_ins_covered  = {r["equipment_code"] for r in eq_ins["requirements"]}
wk_doc_covered  = {r["work_type_code"] for r in wk_doc["requirements"]}
wk_tr_covered   = {r["work_type_code"] for r in wk_tr["requirements"]}

clause_ids      = {c["id"] for c in cc["compliance_clauses"]}
link_targets    = {}
for lk in cl["compliance_links"]:
    tt = lk["target_type"]
    link_targets.setdefault(tt, set()).add(lk["target_id"])

# compliance 연결된 서류 ID
doc_with_compliance = link_targets.get("document", set())

# ── GAP 항목 수집 ─────────────────────────────────────────────────────────

gaps = []  # (axis, item, status, missing_type, engine_coverage, priority, evidence)

COVERED              = "COVERED"
PARTIAL              = "PARTIAL"
MISSING              = "MISSING"
NEEDS_VERIFICATION   = "NEEDS_VERIFICATION"

def add(axis, item, status, gap_type, priority, evidence, engine_coverage=None):
    # gap_type → missing_type 정규화
    if status == COVERED:
        missing_type = "NONE"
        ec = engine_coverage if engine_coverage is not None else "YES"
    elif "builder" in gap_type.lower():
        missing_type = "FORM_BUILDER_MISSING"
        ec = engine_coverage if engine_coverage is not None else "NO"
    elif gap_type in ("DOCUMENT_MISSING", "TRAINING_MISSING", "INSPECTION_MISSING",
                      "MAPPING_MISSING", "ENGINE_MISSING", "COMPLIANCE_MISSING",
                      "DATA_MODEL_MISSING", "UI_MISSING"):
        missing_type = gap_type
        ec = engine_coverage if engine_coverage is not None else "NO"
    else:
        missing_type = gap_type
        ec = engine_coverage if engine_coverage is not None else "NO"
    if status == NEEDS_VERIFICATION:
        ec = engine_coverage if engine_coverage is not None else "PARTIAL"
    gaps.append({
        "axis": axis, "item": item, "status": status,
        "gap_type": gap_type, "missing_type": missing_type,
        "priority": priority, "evidence": evidence,
        "engine_coverage": ec,
    })

# ════════════════════════════════════════════════════════════════
# A축 — 법정 작업계획서
# ════════════════════════════════════════════════════════════════

# WP 카테고리 서류 목록
wp_docs = {d["id"]: d for d in doc_cat["documents"] if d.get("category_code") == "WP"}

# 규칙 제38조 각호 대응 WP 목록 (id, 명칭, 법령 인용)
WP_LEGAL = [
    ("WP-001", "굴착 작업계획서",          "제38조 제1항 제6호"),
    ("WP-002", "터널 굴착 작업계획서",      "제38조 제1항 제7호"),
    ("WP-003", "건축물 해체 작업계획서",    "제38조 제1항 제9호"),
    ("WP-004", "교량 작업계획서",           "제38조 제1항 제8호"),
    ("WP-005", "중량물 취급 작업계획서",    "제38조 제1항 제10호"),
    ("WP-006", "타워크레인 작업계획서",     "제38조 제1항 제1호"),
    ("WP-007", "이동식 크레인 작업계획서",  "제38조 제1항 제14호"),
    ("WP-008", "차량계 건설기계 작업계획서","제38조 제1항 제3호"),
    ("WP-009", "차량계 하역운반기계 작업계획서","제38조 제1항 제2호"),
    ("WP-010", "항타기·항발기 작업계획서",  "제38조 제1항 제12호"),
    ("WP-011", "전기 작업계획서",           "제38조 제1항 (NEEDS_VERIFICATION)"),
    ("WP-012", "궤도 작업계획서",           "제38조 제1항 제11호"),
    ("WP-013", "화학설비 작업계획서",       "제38조 제1항 제4호"),
    ("WP-014", "밀폐공간 작업계획서",       "제619조~제626조"),
]

# 추가: 거푸집·동바리 — WP 카탈로그에 없음
FORMWORK_IN_CATALOG = any(
    "거푸집" in d.get("name", "") or "동바리" in d.get("name", "")
    for d in doc_cat["documents"] if d.get("category_code") == "WP"
)

for doc_id, name, clause in WP_LEGAL:
    if doc_id not in docs_by_id:
        add("A", f"{name} ({doc_id})", MISSING, "DOCUMENT_MISSING", "P0", "NEEDS_VERIFICATION")
        continue
    d = docs_by_id[doc_id]
    impl = d.get("implementation_status", "")
    ev = "VERIFIED" if d.get("source_type") == "law" and "NEEDS_VERIFICATION" not in str(d.get("legal_basis","")) else "NEEDS_VERIFICATION"
    if impl == "DONE":
        add("A", f"{name} ({doc_id})", COVERED, "—", "—", ev)
    else:
        add("A", f"{name} ({doc_id}) [builder 없음]", PARTIAL, "DOCUMENT_MISSING(builder)", "P1" if "P1" in str(d.get("priority","")) else "P2", ev)

if not FORMWORK_IN_CATALOG:
    add("A", "거푸집·동바리 작업계획서 (WP-015 후보)", MISSING, "DOCUMENT_MISSING", "P1", "NEEDS_VERIFICATION")
else:
    _wp015 = next(
        (d for d in doc_cat["documents"]
         if ("거푸집" in d.get("name", "") or "동바리" in d.get("name", ""))
         and d.get("category_code") == "WP"),
        None,
    )
    if _wp015:
        _impl015 = _wp015.get("implementation_status", "")
        _ev015   = _wp015.get("evidence_status", "NEEDS_VERIFICATION")
        if _impl015 == "DONE" and _ev015 in ("VERIFIED", "PARTIAL_VERIFIED"):
            add("A", f"거푸집·동바리 작업계획서 ({_wp015['id']})",
                COVERED, "—", "—", _ev015)
        elif _impl015 == "DONE":
            add("A", f"거푸집·동바리 작업계획서 ({_wp015['id']}) [evidence 재확인 필요]",
                PARTIAL, "COMPLIANCE_MISSING", "P1", "NEEDS_VERIFICATION")
        else:
            add("A", f"거푸집·동바리 작업계획서 ({_wp015['id']}) [builder 없음]",
                PARTIAL, "DOCUMENT_MISSING(builder)", "P1", _ev015)

# ════════════════════════════════════════════════════════════════
# B축 — 위험성평가
# ════════════════════════════════════════════════════════════════

RA_ITEMS = [
    ("RA-001", "위험성평가표"),
    ("RA-002", "위험성평가 관리 등록부 (기록 보존 3년)"),
    ("RA-003", "위험성평가 참여 회의록 (근로자 참여)"),
    ("RA-004", "TBM 안전점검 일지"),
    ("RA-005", "위험성평가 실시 규정"),
    ("RA-006", "위험성평가 결과 근로자 공지문"),
]
for doc_id, name in RA_ITEMS:
    if doc_id not in docs_by_id:
        add("B", name, MISSING, "DOCUMENT_MISSING", "P1", "NEEDS_VERIFICATION")
        continue
    d = docs_by_id[doc_id]
    impl = d.get("implementation_status", "")
    if impl == "DONE":
        add("B", name, COVERED, "—", "—", "VERIFIED")
    else:
        p = d.get("priority", "P3")
        add("B", f"{name} [builder 없음]", PARTIAL, "DOCUMENT_MISSING(builder)", p, "PRACTICAL")

# 최초/수시/정기 유형 구분
add("B", "위험성평가 유형 구분 (최초/수시/정기)", PARTIAL, "MAPPING_MISSING", "P1", "NEEDS_VERIFICATION")
# 잔여위험 관리
add("B", "잔여위험 관리 기록", MISSING, "DOCUMENT_MISSING", "P2", "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# C축 — 근로자 교육
# ════════════════════════════════════════════════════════════════

C_TRAINING = [
    ("EDU_REG_WORKER_HALFYEAR", "근로자 정기안전보건교육 (매반기)", "P0"),
    ("EDU_ONBOARD_WORKER",      "채용 시 안전보건교육",            "P0"),
    ("EDU_TASK_CHANGE",         "작업변경 시 안전보건교육",         "P0"),
    ("EDU_SPECIAL_16H",         "특별안전보건교육 16시간",          "P0"),
]
for code, name, prio in C_TRAINING:
    if code in tr_codes:
        add("C", name, COVERED, "—", "—", "VERIFIED")
    else:
        add("C", name, MISSING, "TRAINING_MISSING", prio, "VERIFIED")

# 건설업 기초안전보건교육 (산안법 제31조)
if "EDU_CONSTRUCTION_BASIC" not in tr_codes:
    add("C", "건설업 기초안전보건교육 (산안법 제31조)", MISSING, "TRAINING_MISSING", "P0", "NEEDS_VERIFICATION")
else:
    edu_cb = next((t for t in tr_types["training_types"] if t["training_code"] == "EDU_CONSTRUCTION_BASIC"), {})
    vs = edu_cb.get("verification_status", "NEEDS_VERIFICATION")
    if vs == "confirmed":
        add("C", "건설업 기초안전보건교육 (EDU_CONSTRUCTION_BASIC)", COVERED, "—", "—", "VERIFIED")
    else:
        # 마스터 등록됨, 법령 미확인 → PARTIAL (NEEDS_VERIFICATION이면 COVERED 불가)
        add("C", "건설업 기초안전보건교육 (EDU_CONSTRUCTION_BASIC) [법령 미확인]",
            PARTIAL, "COMPLIANCE_MISSING", "P0", "NEEDS_VERIFICATION", "NO")

# 일용근로자 교육 별도 유형
if "EDU_DAILY_WORKER" not in tr_codes:
    add("C", "일용근로자 교육 (별도 유형)", PARTIAL, "TRAINING_MISSING", "P1", "VERIFIED")

# 외국인 근로자 교육
if "EDU_FOREIGN_WORKER" not in tr_codes:
    add("C", "외국인 근로자 안전교육", PARTIAL, "TRAINING_MISSING", "P2", "PRACTICAL")

# ED-001 교육일지 builder
d = docs_by_id.get("ED-001", {})
if d.get("implementation_status") == "DONE":
    add("C", "안전보건교육 일지 (ED-001)", COVERED, "—", "—", "VERIFIED")
else:
    add("C", "안전보건교육 일지 (ED-001)", PARTIAL, "DOCUMENT_MISSING(builder)", "P1", "VERIFIED")

# ED-003 특별교육 일지
d = docs_by_id.get("ED-003", {})
impl = d.get("implementation_status", "")
add("C", f"특별안전보건교육 일지 (ED-003)", PARTIAL if impl != "DONE" else COVERED,
    "DOCUMENT_MISSING(builder)" if impl != "DONE" else "—", "P1", "VERIFIED")

# 별표5 특별교육 전수 매핑
all_wt_tr = set(r["work_type_code"] for r in wk_tr["requirements"]
                if r.get("training_code") in ("EDU_SPECIAL_16H","EDU_CONFINED_SPACE","EDU_SPECIAL_2H"))
# 7종 작업유형 중 특별교육 매핑 현황
add("C", f"특별교육 별표5 work_type 매핑 ({len(all_wt_tr)}/7 커버)", PARTIAL, "MAPPING_MISSING", "P1", "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# D축 — 관리자/직무교육
# ════════════════════════════════════════════════════════════════

D_TRAINING = [
    ("EDU_REG_MANAGER_QUARTERLY", "관리감독자 정기교육 (매분기)"),
]
for code, name in D_TRAINING:
    if code in tr_codes:
        add("D", name, COVERED, "—", "—", "VERIFIED")
    else:
        add("D", name, MISSING, "TRAINING_MISSING", "P0", "VERIFIED")

# 직무교육 3종 누락
for code, name, prio in [
    ("EDU_SAFETY_MANAGER_DUTY",  "안전관리자 직무교육 (산안법 제17조)", "P1"),
    ("EDU_HEALTH_MANAGER_DUTY",  "보건관리자 직무교육 (산안법 제18조)", "P1"),
    ("EDU_RESP_MANAGER_DUTY",    "안전보건관리책임자 교육 (산안법 제15조)", "P1"),
    ("EDU_SAFETY_REP_DUTY",      "안전보건관리담당자 교육",            "P2"),
    ("EDU_COORD_DUTY",           "안전보건조정자 관련 교육",           "P3"),
]:
    if code not in tr_codes:
        add("D", name, MISSING, "TRAINING_MISSING", prio, "NEEDS_VERIFICATION")

# ED-004 직무교육 이수 확인서
d = docs_by_id.get("ED-004", {})
add("D", "안전보건관리자 직무교육 이수 확인서 (ED-004)",
    PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
    "DOCUMENT_MISSING(builder)", "P3", "VERIFIED")

# ════════════════════════════════════════════════════════════════
# E축 — 장비/기계/기구
# ════════════════════════════════════════════════════════════════

# 점검 유형 커버 현황 (NV=True: 적용 범위 법령 미확인)
for code, name, is_nv, prio in [
    ("INSP_DAILY_PRE_WORK",     "작업 시작 전 일상점검",  False, "—"),
    ("INSP_MONTHLY",             "월 1회 정기점검",        False, "—"),
    ("INSP_WEEKLY",              "주 1회 정기점검",        True,  "P2"),
    ("INSP_SELF_EXAM_ANNUAL",   "자체검사 (연 1회)",       True,  "P1"),
    ("INSP_SELF_EXAM_HALFYEAR", "자체검사 (반기 1회)",     True,  "P2"),
]:
    if code in ins_codes:
        if is_nv:
            add("E", f"{name} ({code})", NEEDS_VERIFICATION,
                "MAPPING_MISSING", prio, "NEEDS_VERIFICATION", "PARTIAL")
        else:
            add("E", f"{name} ({code})", COVERED, "—", "—", "VERIFIED", "YES")

# 비계 조립 후 점검 — inspection_types 미등록
add("E", "비계 조립 후 점검 (INSP_SCAFF_AFTER_ASSEMBLY)", MISSING, "INSPECTION_MISSING", "P1", "NEEDS_VERIFICATION")

# 화학설비 정기점검 — inspection_types 미등록
add("E", "화학설비 정기점검", MISSING, "INSPECTION_MISSING", "P2", "NEEDS_VERIFICATION")

# 운전원 자격/면허 마스터
license_master = MASTERS / "worker" / "worker_licenses.yml"
if not license_master.exists():
    add("E", "운전원 자격/면허 마스터 (worker_licenses.yml)", MISSING, "DATA_MODEL_MISSING", "P0", "NEEDS_VERIFICATION")
else:
    import yaml as _yaml
    with open(license_master, encoding="utf-8") as _f:
        _lm = _yaml.safe_load(_f)
    _licenses = _lm.get("worker_licenses", [])
    _all_nv = all(lic.get("evidence_status") == "NEEDS_VERIFICATION" for lic in _licenses) if _licenses else True
    if _all_nv:
        # 파일 존재, 전항목 법령 미확인 → PARTIAL
        add("E", "운전원 자격/면허 마스터 (worker_licenses.yml) [법령 미확인]",
            PARTIAL, "COMPLIANCE_MISSING", "P0", "NEEDS_VERIFICATION", "NO")
    else:
        add("E", "운전원 자격/면허 마스터 (worker_licenses.yml)", COVERED, "—", "—", "VERIFIED")

# 장비 반입/검사증
for doc_id, name, prio in [
    ("PPE-002", "건설 장비 반입 신청서", "P2"),
    ("PPE-003", "건설 장비 보험·정기검사증 확인서", "P3"),
]:
    d = docs_by_id.get(doc_id, {})
    add("E", f"{name} ({doc_id})",
        PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
        "DOCUMENT_MISSING(builder)", prio, "PRACTICAL")

# 장비별 매핑 커버리지 (31종 중 실제 매핑 수)
add("E", f"equipment_document_requirements 커버리지 ({len(eq_doc_covered)}/31종)",
    PARTIAL, "MAPPING_MISSING", "P1", "VERIFIED")
add("E", f"equipment_training_requirements 커버리지 ({len(eq_tr_covered)}/31종)",
    PARTIAL, "MAPPING_MISSING", "P1", "VERIFIED")
add("E", f"equipment_inspection_requirements 커버리지 ({len(eq_ins_covered)}/31종)",
    PARTIAL, "MAPPING_MISSING", "P1", "VERIFIED")

# ════════════════════════════════════════════════════════════════
# F축 — 작업허가/PTW
# ════════════════════════════════════════════════════════════════

PTW_ITEMS = [
    ("PTW-001", "밀폐공간 작업 허가서"),
    ("PTW-002", "화기작업 허가서"),
    ("PTW-003", "고소작업 허가서"),
    ("PTW-004", "전기작업 허가서 (LOTO)"),
    ("PTW-005", "굴착 작업 허가서"),
    ("PTW-006", "방사선 투과검사 허가서"),
    ("PTW-007", "중량물 인양 허가서"),
    ("PTW-008", "임시전기 설치·연결 허가서"),
]
PTW_PRIO = {"PTW-001":"—","PTW-002":"P1","PTW-003":"P1","PTW-004":"P2",
            "PTW-005":"P2","PTW-006":"P3","PTW-007":"P1","PTW-008":"P2"}
for doc_id, name in PTW_ITEMS:
    d = docs_by_id.get(doc_id, {})
    impl = d.get("implementation_status", "")
    if impl == "DONE":
        add("F", f"{name} ({doc_id})", COVERED, "—", "—", "VERIFIED")
    else:
        add("F", f"{name} ({doc_id}) [builder 없음]", PARTIAL, "DOCUMENT_MISSING(builder)", PTW_PRIO[doc_id], "PRACTICAL")

# PTW 엔진 연결: 밀폐공간 외 미연결
ptw_in_engine_links = {lk["target_id"] for lk in cl["compliance_links"]
                       if lk["target_type"] == "document" and lk["target_id"].startswith("PTW")}
add("F", f"PTW 자동판정 엔진 연결 ({len(ptw_in_engine_links)}/8종 연결됨)",
    PARTIAL, "ENGINE_MISSING", "P1", "PRACTICAL")

# ════════════════════════════════════════════════════════════════
# G축 — 보건관리
# ════════════════════════════════════════════════════════════════

# 일반건강진단
d = docs_by_id.get("CM-003", {})
add("G", "일반건강진단 결과 확인서 (CM-003)",
    PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
    "DOCUMENT_MISSING(builder)", "P3", "VERIFIED")

# 작업환경측정 — 카탈로그 미등록 여부 확인
work_env_in_catalog = any(
    "작업환경측정" in d.get("name", "")
    for d in doc_cat["documents"]
)
if not work_env_in_catalog:
    add("G", "작업환경측정 관련 서류 (산안법 제125조 추정)", MISSING, "DOCUMENT_MISSING", "P0", "NEEDS_VERIFICATION")
else:
    hm001 = docs_by_id.get("HM-001", {})
    hm001_ev = hm001.get("evidence_status", "NEEDS_VERIFICATION")
    hm001_done = hm001.get("implementation_status") == "DONE"
    if hm001_ev == "VERIFIED" and hm001_done:
        add("G", "작업환경측정 관련 서류 (HM-001)", COVERED, "—", "—", "VERIFIED")
    elif hm001_done:
        # builder 구현 완료, 법령 evidence 재확인 필요 → PARTIAL/WARN (P0 해소)
        add("G", "작업환경측정 관련 서류 (HM-001) [법령 evidence 재확인 필요]",
            PARTIAL, "FORM_BUILDER_MISSING", "P1", "NEEDS_VERIFICATION", "PARTIAL")
    else:
        # 카탈로그 등록됨, builder 없음 → PARTIAL/P0
        add("G", "작업환경측정 관련 서류 (HM-001) [builder 없음]",
            PARTIAL, "FORM_BUILDER_MISSING", "P0", "NEEDS_VERIFICATION", "NO")

# 특수건강진단
special_health_in_catalog = any(
    "특수건강진단" in d.get("name", "")
    for d in doc_cat["documents"]
)
if not special_health_in_catalog:
    add("G", "특수건강진단 결과 관리 (산안법 제130조 추정)", MISSING, "DOCUMENT_MISSING", "P0", "NEEDS_VERIFICATION")
else:
    hm002 = docs_by_id.get("HM-002", {})
    hm002_ev = hm002.get("evidence_status", "NEEDS_VERIFICATION")
    hm002_done = hm002.get("implementation_status") == "DONE"
    if hm002_ev == "VERIFIED" and hm002_done:
        add("G", "특수건강진단 결과 관리 (HM-002)", COVERED, "—", "—", "VERIFIED")
    elif hm002_done:
        # builder 구현 완료, 법령 evidence 재확인 필요 → PARTIAL/WARN (P0 해소)
        add("G", "특수건강진단 결과 관리 (HM-002) [법령 evidence 재확인 필요]",
            PARTIAL, "FORM_BUILDER_MISSING", "P1", "NEEDS_VERIFICATION", "PARTIAL")
    else:
        # 카탈로그 등록됨, builder 없음 → PARTIAL/P0
        add("G", "특수건강진단 결과 관리 (HM-002) [builder 없음]",
            PARTIAL, "FORM_BUILDER_MISSING", "P0", "NEEDS_VERIFICATION", "NO")

# 나머지 보건관리 항목
for item, prio in [
    ("유해인자 노출 근로자 관리 대장", "P1"),
    ("온열질환 예방 관리 기록",       "P1"),
    ("소음·진동 관련 점검/기록",       "P2"),
    ("분진 관련 점검/기록",            "P2"),
    ("근골격계 부담작업 유해요인 조사", "P2"),
    ("휴게시설 확인 점검표",           "P2"),
]:
    in_catalog = any(kw in d.get("name","") for d in doc_cat["documents"] for kw in item.split("·")[:1])
    if not in_catalog:
        add("G", item, MISSING, "DOCUMENT_MISSING", prio, "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# H축 — 화학물질/MSDS
# ════════════════════════════════════════════════════════════════

for doc_id, name, prio, ev in [
    ("PPE-004", "MSDS 비치 및 교육 확인서", "P3", "VERIFIED"),
    ("CL-009",  "유해화학물질 취급 점검표", "P3", "PRACTICAL"),
]:
    d = docs_by_id.get(doc_id, {})
    add("H", f"{name} ({doc_id})",
        PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
        "DOCUMENT_MISSING(builder)", prio, ev)

# MSDS 교육 — NEEDS_VERIFICATION
add("H", "MSDS 교육 (EDU_MSDS) [교육시간 미확인]",
    PARTIAL if "EDU_MSDS" in tr_codes else MISSING, "COMPLIANCE_MISSING", "P2", "NEEDS_VERIFICATION")

# 누락 항목
for item, prio in [
    ("화학물질 경고표지 관리",      "P2"),
    ("화학물질 저장·보관·폐기 관리", "P2"),
    ("화학물질 취급 환기 점검",      "P2"),
]:
    add("H", item, MISSING, "DOCUMENT_MISSING", prio, "NEEDS_VERIFICATION")

# WT_CHEMICAL_HANDLING 매핑 연결
chem_in_links = any(lk["target_id"] == "WT_CHEMICAL_HANDLING"
                    for lk in cl["compliance_links"] if lk["target_type"] == "work")
add("H", "WT_CHEMICAL_HANDLING compliance_links 연결",
    COVERED if chem_in_links else PARTIAL, "COMPLIANCE_MISSING", "P2", "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# I축 — 보호구/PPE
# ════════════════════════════════════════════════════════════════

for doc_id, name, prio in [
    ("PPE-001", "보호구 지급 대장",        "P2"),
    ("CL-007",  "추락 방호 설비 점검표",   "P2"),
    ("CL-008",  "보호구 지급 및 관리 점검표","P3"),
]:
    d = docs_by_id.get(doc_id, {})
    add("I", f"{name} ({doc_id})",
        PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
        "DOCUMENT_MISSING(builder)", prio, "PRACTICAL")

for item, prio in [
    ("보호구 착용 확인 기록",  "P2"),
    ("적정 보호구 선정 기준표", "P3"),
    ("보호구 교체·폐기 기록",  "P3"),
    ("호흡보호구 관리 기록",   "P2"),
    ("절연보호구 관리 기록",   "P2"),
]:
    add("I", item, MISSING, "DOCUMENT_MISSING", prio, "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# J축 — 도급/협력업체
# ════════════════════════════════════════════════════════════════

for doc_id, name, prio, ev in [
    ("CM-001", "협력업체 안전보건 관련 서류 확인서", "P2", "VERIFIED"),
    ("CM-002", "도급·용역 안전보건 협의서",         "P2", "VERIFIED"),
    ("ED-005", "안전보건협의체 회의록",             "P2", "VERIFIED"),
    ("SP-002", "협력업체 안전보건 수준 평가표",      "P3", "PRACTICAL"),
    ("CM-006", "외국인 근로자 안전보건 교육 확인서",  "P3", "PRACTICAL"),
]:
    d = docs_by_id.get(doc_id, {})
    add("J", f"{name} ({doc_id})",
        PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
        "DOCUMENT_MISSING(builder)", prio, ev)

for item, prio in [
    ("혼재작업 조정 기록",  "P1"),
    ("현장 출입자 관리 대장","P2"),
]:
    add("J", item, MISSING, "DOCUMENT_MISSING", prio, "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# K축 — 사고/비상대응
# ════════════════════════════════════════════════════════════════

for doc_id, name, prio, ev in [
    ("EM-001", "산업재해조사표",               "P2", "VERIFIED"),
    ("EM-002", "아차사고 보고서",              "P2", "PRACTICAL"),
    ("EM-003", "비상 연락망 및 대피 계획서",   "P2", "VERIFIED"),
    ("EM-004", "중대재해 발생 즉시 보고서",    "P2", "VERIFIED"),
    ("EM-005", "재해 원인 분석 및 재발방지 보고서","P3","PRACTICAL"),
    ("EM-006", "응급조치 실시 기록서",         "P3", "PRACTICAL"),
    ("CM-007", "산업재해 발생 현황 관리 대장", "P3", "VERIFIED"),
]:
    d = docs_by_id.get(doc_id, {})
    add("K", f"{name} ({doc_id})",
        PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
        "DOCUMENT_MISSING(builder)", prio, ev)

add("K", "비상대응 훈련 기록", MISSING, "DOCUMENT_MISSING", "P1", "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# L축 — 현장 운영관리
# ════════════════════════════════════════════════════════════════

for doc_id, name, prio in [
    ("DL-001", "안전관리 일지",               "P1"),
    ("DL-002", "관리감독자 안전보건 업무 일지","P2"),
    ("DL-003", "안전순찰 점검 일지",          "P2"),
    ("DL-004", "기상 조건 기록 일지",         "P3"),
    ("DL-005", "작업 전 안전 확인서",         "P3"),
    ("TS-004", "산업안전보건관리비 사용계획서","P2"),
    ("CM-004", "안전보건관리자 선임 신고서",  "P3"),
    ("SP-001", "안전보건 방침 및 목표 게시문","P3"),
]:
    d = docs_by_id.get(doc_id, {})
    add("L", f"{name} ({doc_id})",
        PARTIAL if d.get("implementation_status") != "DONE" else COVERED,
        "DOCUMENT_MISSING(builder)", prio, "PRACTICAL")

add("L", "노동부 점검 대응 체크리스트", MISSING, "DOCUMENT_MISSING", "P1", "NEEDS_VERIFICATION")

# ════════════════════════════════════════════════════════════════
# 출력
# ════════════════════════════════════════════════════════════════

from collections import Counter

covered = [g for g in gaps if g["status"] == COVERED]
partial  = [g for g in gaps if g["status"] == PARTIAL]
missing  = [g for g in gaps if g["status"] == MISSING]
nv       = [g for g in gaps if g["status"] == NEEDS_VERIFICATION]

print("=" * 70)
print("안전관리 갭 감사 결과  (audit_safety_gap.py v3.0)")
print("=" * 70)
print(f"전체 항목     : {len(gaps)}건")
print(f"  COVERED            : {len(covered)}건")
print(f"  PARTIAL            : {len(partial)}건")
print(f"  MISSING            : {len(missing)}건")
print(f"  NEEDS_VERIFICATION : {len(nv)}건")
print()

# ── 우선순위별 집계 ──────────────────────────────────────────────
prio_counts = Counter(g["priority"] for g in gaps if g["priority"] != "—")
print("── 우선순위별 집계 ──")
for p in ["P0", "P1", "P2", "P3"]:
    print(f"  {p}: {prio_counts.get(p, 0)}건")
print()

# ── missing_type별 집계 ──────────────────────────────────────────
mt_counts = Counter()
for g in gaps:
    for mt in g.get("missing_type", "").split(","):
        mt = mt.strip()
        if mt and mt not in ("NONE", "—"):
            mt_counts[mt] += 1
print("── 누락 유형(missing_type)별 집계 ──")
for mt, cnt in mt_counts.most_common():
    print(f"  {mt}: {cnt}건")
print()

# ── engine_coverage별 집계 ───────────────────────────────────────
ec_counts = Counter(g.get("engine_coverage", "NO") for g in gaps)
print("── 엔진 커버리지(engine_coverage)별 집계 ──")
for ec in ["YES", "PARTIAL", "NO", "NOT_APPLICABLE"]:
    print(f"  {ec}: {ec_counts.get(ec, 0)}건")
print()

# ── 축별 집계 ────────────────────────────────────────────────────
axes = sorted(set(g["axis"] for g in gaps))
print("── 축별 집계 ──")
for ax in axes:
    ax_gaps = [g for g in gaps if g["axis"] == ax]
    c = sum(1 for g in ax_gaps if g["status"] == COVERED)
    p = sum(1 for g in ax_gaps if g["status"] == PARTIAL)
    m = sum(1 for g in ax_gaps if g["status"] == MISSING)
    n = sum(1 for g in ax_gaps if g["status"] == NEEDS_VERIFICATION)
    print(f"  {ax}축: 총{len(ax_gaps):2d} COVERED={c} PARTIAL={p} MISSING={m} NV={n}")
print()

# ── MISSING 항목 전체 ────────────────────────────────────────────
print("── MISSING 항목 전체 ──")
for g in sorted(missing, key=lambda x: (x["priority"] if x["priority"] != "—" else "P9")):
    print(f"  [{g['axis']}축 {g['priority']}] {g['item']}")
    print(f"         missing_type={g['missing_type']}  engine={g['engine_coverage']}  근거:{g['evidence']}")
print()

# ── NEEDS_VERIFICATION 항목 ──────────────────────────────────────
if nv:
    print("── NEEDS_VERIFICATION 항목 ──")
    for g in nv:
        print(f"  [{g['axis']}축 {g['priority']}] {g['item']}  | 근거:{g['evidence']}")
    print()

# ── Top 20 MISSING 후보 ──────────────────────────────────────────
prio_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "—": 9}
top_missing = sorted(missing, key=lambda x: prio_order.get(x["priority"], 9))[:20]
print("── Top 20 MISSING 후보 ──")
print(f"  {'순위':<4} {'우선순위':<6} {'축':<3} {'missing_type':<30} 항목")
for i, g in enumerate(top_missing, 1):
    print(f"  {i:<4} {g['priority']:<6} {g['axis']:<3} {g['missing_type']:<30} {g['item'][:50]}")
print()

# ── 매핑 커버리지 요약 ───────────────────────────────────────────
print("── 매핑 커버리지 요약 ──")
print(f"  eq→doc    : {len(eq_doc_covered)}/31종 장비 커버")
print(f"  eq→train  : {len(eq_tr_covered)}/31종 장비 커버")
print(f"  eq→inspect: {len(eq_ins_covered)}/31종 장비 커버")
print(f"  work→doc  : {len(wk_doc_covered)}/7종 작업유형 커버")
print(f"  work→train: {len(wk_tr_covered)}/7종 작업유형 커버")
print(f"  compliance link 대상 서류: {len(doc_with_compliance)}건 / 90종")
print()

# ── P0 form_builder 잔여 / evidence verification 잔여 (분리 요약) ──
_p0_builder = [g for g in gaps
               if g["priority"] == "P0" and "FORM_BUILDER_MISSING" in g.get("missing_type","")]
_ev_nv_done = [d for d in doc_cat["documents"]
               if d.get("implementation_status") == "DONE"
               and d.get("evidence_status") == "NEEDS_VERIFICATION"]
_overall_ok = len(_p0_builder) == 0 and len(_ev_nv_done) == 0
print("── P0 / evidence 분리 요약 ──")
print(f"  P0 form_builder 잔여: {len(_p0_builder)}건")
if _p0_builder:
    for g in _p0_builder:
        print(f"    [{g['axis']}축] {g['item']}")
print(f"  evidence NEEDS_VERIFICATION (DONE builder 기준): {len(_ev_nv_done)}건")
if _ev_nv_done:
    for d in _ev_nv_done:
        print(f"    {d['id']}: {d['name']}")
print(f"  overall 판정: {'PASS' if _overall_ok else 'WARN'}")
print()
print("감사 완료.")
