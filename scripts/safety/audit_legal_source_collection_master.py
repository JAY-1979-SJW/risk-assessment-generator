"""
audit_legal_source_collection_master.py
법령·지침 수집 전수 감사 스크립트 (read-only)

출력:
  docs/reports/legal_source_collection_master_audit.json
  docs/reports/legal_source_collection_master_audit.md

사용법:
  python -m scripts.safety.audit_legal_source_collection_master
  python scripts/safety/audit_legal_source_collection_master.py
"""
from __future__ import annotations

import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ── 경로 ────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
MASTERS = ROOT / "data" / "masters" / "safety"
REGISTRY_PATH  = MASTERS / "legal_sources_registry.yml"
EVIDENCE_REG   = MASTERS / "legal_evidence_registry.yml"
QUEUE_PATH     = MASTERS / "legal_collection_queue.yml"
LAW_CONTENT    = ROOT / "data" / "raw" / "law_content" / "law"
ADMRUL_CONTENT = ROOT / "data" / "raw" / "law_content" / "admrul"
EVIDENCE_DIR   = ROOT / "data" / "evidence" / "safety_law_refs"
REPORTS_DIR    = ROOT / "docs" / "reports"
LOG_DIR        = ROOT / "logs" / "collect"

# ── 로거 ────────────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
_log = logging.getLogger("audit_legal_source_collection_master")
if not _log.handlers:
    _log.setLevel(logging.INFO)
    _fh = logging.FileHandler(LOG_DIR / "audit_legal_source_collection_master.log", encoding="utf-8")
    _fh.setFormatter(_fmt)
    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    _log.addHandler(_fh)
    _log.addHandler(_sh)

log = _log

# ── 상태·액션 enum ───────────────────────────────────────────────────────────────
AUDIT_STATUS = {
    "COLLECTED_VERIFIED",
    "COLLECTED_PARTIAL",
    "RAW_COLLECTED_REGISTRY_MISSING",
    "REGISTRY_ONLY_RAW_MISSING",
    "REFERENCED_ONLY",
    "SCRIPT_EXISTS_NOT_COLLECTED",
    "NOT_COLLECTED",
    "WATCH_ONLY",
    "EXCLUDE_FOR_NOW",
    "UNKNOWN",
}

AUDIT_ACTION = {
    "SKIP_ALREADY_VERIFIED",
    "ADD_TO_REGISTRY",
    "UPDATE_REGISTRY_STATUS",
    "COLLECT_RAW",
    "COLLECT_APPENDIX_FORM",
    "GENERATE_EVIDENCE_CANDIDATE",
    "ADD_TO_REQUIREMENT_MATRIX_CANDIDATE",
    "WATCH_ONLY",
    "EXCLUDE_FOR_NOW",
    "NEEDS_NAME_CONFIRMATION",
    "NEEDS_CONNECTOR",
}

WATCH_SOURCE_TYPES = {"KOSHA_GUIDE", "ACCIDENT_CASE", "STATISTICS", "technical_guideline"}
ELECTRIC_CHEMICAL_KEYWORDS = {"전기", "소방", "통신", "화학", "가스", "건설기계"}

# ── admrul 분류 키워드 ────────────────────────────────────────────────────────────
# P1: 산업안전보건 직접 관련 — 좁고 명확한 키워드만 사용
_P1_KEYWORDS = [
    "산업안전보건관리비",  # 건설업 안전보건관리비
    "안전인증대상기계",   # 위험기계 안전인증
    "위험기계·기구",      # 방호장치·위험기계
    "방호장치",            # 방호장치 고시
    "보호구 안전인증",    # 보호구
    "안전보건교육",        # 교육 고시
    "위험성평가",          # 위험성평가 지침
    "유해·위험",           # 유해위험작업
    "중대산업재해",        # 중대재해처벌법 하위
    "작업환경측정",        # 작업환경측정
    "산업안전보건기준",    # 산업안전보건기준 규칙
    "자율안전확인",        # 자율안전확인 고시
    "안전검사",            # 안전검사 고시
    "화학물질의 분류·표시",  # MSDS
]
# P2: 건설·전기·가스·소방·화학 분야 안전 — 범위 넓지만 안전 관련
_P2_KEYWORDS = [
    "건설공사 안전",
    "건설업 산업안전",
    "고압가스안전",
    "액화석유가스 안전",
    "도시가스 안전",
    "전기안전",
    "소방시설 안전",
    "화학물질 안전",
    "위험물 안전",
    "기계·기구 안전",
    "가스안전",
]
_WATCH_KEYWORDS = [
    "KOSHA", "기술지침", "안전보건자료", "사고사례", "재해사례",
]
_EXCLUDE_KEYWORDS = [
    "산재보험료율", "요양급여", "간병급여", "간병료",
    "보상급여", "장애등급", "진폐", "부담금", "징수금",
    "보험료", "최고·최저보상", "재판예규", "행정소송",
    "추진단", "자문단", "현장실습생", "파견근로자", "기간제",
    "근로시간면제",
]
# EXCLUDE이지만 이 키워드 병존이면 NEEDS_REVIEW
_EXCLUDE_OVERRIDE_KEYWORDS = [
    "산업안전", "안전보건", "위험기계", "방호장치", "보호구", "안전인증",
]
# P1/P2 판정 후 이 키워드가 있으면 관련성 낮다고 NEEDS_REVIEW로 강등
_P1_DOWNGRADE_KEYWORDS = [
    "식품", "수산물", "김치", "어린이제품", "생활용품",
    "재난안전관리", "국립", "수출입", "로봇", "연구실",
    "승강기", "박물관", "과학관", "병원",
]


def _classify_admrul(title: str, law_type: str, ministry: str) -> tuple[str, list[str]]:
    """
    admrul 1건을 분류 그룹으로 판정.
    반환: (group, hit_keywords)
      group: ADMRUL_SAFETY_P1 | ADMRUL_SAFETY_P2 | ADMRUL_WATCH_ONLY
             | ADMRUL_EXCLUDE_CANDIDATE | ADMRUL_NEEDS_REVIEW
    """
    # WATCH
    watch_hits = [kw for kw in _WATCH_KEYWORDS if kw in title]
    if watch_hits:
        return "ADMRUL_WATCH_ONLY", watch_hits

    # EXCLUDE 후보
    exclude_hits = [kw for kw in _EXCLUDE_KEYWORDS if kw in title]
    if exclude_hits:
        override = [kw for kw in _EXCLUDE_OVERRIDE_KEYWORDS if kw in title]
        if override:
            return "ADMRUL_NEEDS_REVIEW", exclude_hits + override
        return "ADMRUL_EXCLUDE_CANDIDATE", exclude_hits

    # P1 — 좁은 키워드로 확인 후 강등 체크
    p1_hits = [kw for kw in _P1_KEYWORDS if kw in title]
    if p1_hits:
        downgrade = [kw for kw in _P1_DOWNGRADE_KEYWORDS if kw in title]
        if downgrade:
            return "ADMRUL_NEEDS_REVIEW", p1_hits + [f"강등:{kw}" for kw in downgrade]
        return "ADMRUL_SAFETY_P1", p1_hits

    # P2 — 좁은 안전 복합 키워드
    p2_hits = [kw for kw in _P2_KEYWORDS if kw in title]
    if p2_hits:
        downgrade = [kw for kw in _P1_DOWNGRADE_KEYWORDS if kw in title]
        if downgrade:
            return "ADMRUL_NEEDS_REVIEW", p2_hits + [f"강등:{kw}" for kw in downgrade]
        return "ADMRUL_SAFETY_P2", p2_hits

    # 고용노동부 소관이면 NEEDS_REVIEW (미분류 안전 관련 가능성)
    if "고용노동부" in ministry:
        return "ADMRUL_NEEDS_REVIEW", [f"소관부처=고용노동부"]

    # 그 외 주요 안전 관련 부처
    review_ministries = {"국토교통부", "소방청", "행정안전부"}
    for m in review_ministries:
        if m in ministry:
            return "ADMRUL_NEEDS_REVIEW", [f"소관부처={m}"]

    return "ADMRUL_NEEDS_REVIEW", []


# ── 유틸 ────────────────────────────────────────────────────────────────────────
def _load_yaml(path: Path) -> dict | list | None:
    if not path.exists():
        log.warning(f"파일 없음: {path.relative_to(ROOT)}")
        return None
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _scan_jsonl(base: Path) -> list[dict]:
    """base 하위 모든 *.jsonl 레코드 반환."""
    records = []
    if not base.exists():
        return records
    for f in sorted(base.rglob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def _scan_json(base: Path) -> list[dict]:
    """base 하위 모든 *.json 레코드 반환."""
    records = []
    if not base.exists():
        return records
    for f in sorted(base.rglob("*.json")):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return records


def _norm_name(s: str) -> str:
    """법령명 정규화: 공백·가운뎃점 제거, 소문자 변환."""
    return re.sub(r"[\s·\-]", "", s).lower()


# ── 1. raw 법령 집계 ─────────────────────────────────────────────────────────────
def _build_raw_law_index() -> dict[str, dict]:
    """law raw_id(MST 5~6자리) → {title, article_count, ...} 매핑. admrul 제외."""
    idx: dict[str, dict] = {}

    law_records = _scan_jsonl(LAW_CONTENT)
    for rec in law_records:
        mst = str(rec.get("raw_id", "")).strip()
        if not mst:
            continue
        title = rec.get("title", "").split(" 제")[0].strip()
        if mst not in idx:
            idx[mst] = {
                "mst": mst,
                "law_id": rec.get("law_id", ""),
                "title": title,
                "source_type": rec.get("law_type", "법률"),
                "article_count": 0,
                "file": str(Path(rec.get("source_url", "")).name),
                "raw_kind": "law",
            }
        idx[mst]["article_count"] += 1

    log.info(f"raw law index (법률·시행령·시행규칙): {len(idx)}개")
    return idx


def _build_raw_admrul_index() -> dict[str, dict]:
    """admrul raw_id(14자리) → {title, article_count, law_type, ministry} 매핑."""
    idx: dict[str, dict] = {}
    admrul_records = _scan_jsonl(ADMRUL_CONTENT)
    for rec in admrul_records:
        rid = str(rec.get("raw_id", "")).strip()
        if not rid:
            continue
        title = rec.get("title", "").split(" 제")[0].strip()
        if rid not in idx:
            idx[rid] = {
                "raw_id": rid,
                "law_id": rec.get("law_id", ""),
                "title": title,
                "norm_title": _norm_name(title),
                "law_type": rec.get("law_type", ""),
                "ministry": rec.get("ministry", ""),
                "article_count": 0,
                "raw_kind": "admrul",
            }
        idx[rid]["article_count"] += 1

    log.info(f"raw admrul index (행정규칙): {len(idx)}개")
    return idx


# ── 2. evidence 집계 ─────────────────────────────────────────────────────────────
def _build_evidence_index(evidence_reg: dict | None) -> dict[str, list[str]]:
    """source_code → [evidence_id, ...] 매핑."""
    idx: dict[str, list[str]] = defaultdict(list)
    if not evidence_reg:
        return idx
    for ev in evidence_reg.get("evidences", []):
        sc = ev.get("source_code", "")
        eid = ev.get("evidence_id", "")
        if sc and eid:
            idx[sc].append(eid)
    log.info(f"evidence index: {sum(len(v) for v in idx.values())}개 (source {len(idx)}종)")
    return idx


# ── 3. queue 집계 ────────────────────────────────────────────────────────────────
def _build_queue_index(queue_data: dict | None) -> dict[str, dict]:
    """source_code → queue item 매핑."""
    idx: dict[str, dict] = {}
    if not queue_data:
        return idx
    for group in queue_data.values():
        if isinstance(group, list):
            for item in group:
                sc = item.get("source_code", "")
                if sc:
                    idx[sc] = item
    log.info(f"queue index: {len(idx)}개 항목")
    return idx


# ── 4. registry source 감사 ──────────────────────────────────────────────────────
def _audit_registry_source(
    src: dict,
    raw_by_mst: dict[str, dict],
    evidence_idx: dict[str, list[str]],
    queue_idx: dict[str, dict],
    issues: list[dict],
) -> dict:
    sc = src.get("source_code", "?")
    reg_status = src.get("collection_status", "UNKNOWN")
    mst = str(src.get("law_mst", "") or "").strip()
    raw_path = src.get("raw_path", "")
    source_type = src.get("source_type", "")
    evidences = evidence_idx.get(sc, [])
    q_item = queue_idx.get(sc)

    # raw 존재 여부
    raw_exists = False
    raw_article_count = 0
    if mst and mst in raw_by_mst:
        raw_exists = True
        raw_article_count = raw_by_mst[mst]["article_count"]
    elif raw_path and Path(ROOT / raw_path).exists():
        raw_exists = True

    # ── 판정 규칙 적용 ──────────────────────────────────────────────────────────

    # R07: 이미 COLLECTED_VERIFIED → SKIP
    if reg_status == "COLLECTED_VERIFIED":
        audit_status = "COLLECTED_VERIFIED"
        action = "SKIP_ALREADY_VERIFIED"

        # R09: queue에 enabled=true로 남아있으면 중복수집 위험 WARN
        if q_item and q_item.get("enabled", False):
            issues.append({
                "level": "WARN", "rule": "R09",
                "source_code": sc,
                "msg": f"COLLECTED_VERIFIED인데 queue enabled=true (중복수집 위험)",
            })
        return {"source_code": sc, "audit_status": audit_status, "proposed_action": action,
                "evidence_count": len(evidences), "raw_exists": raw_exists,
                "raw_article_count": raw_article_count, "issues": []}

    # R05: WATCH_ONLY 계열 source_type
    if source_type in WATCH_SOURCE_TYPES or reg_status == "WATCH_ONLY":
        audit_status = "WATCH_ONLY"
        action = "WATCH_ONLY"
        return {"source_code": sc, "audit_status": audit_status, "proposed_action": action,
                "evidence_count": len(evidences), "raw_exists": raw_exists,
                "raw_article_count": raw_article_count, "issues": []}

    src_issues: list[str] = []

    # R02: registry에 있으나 raw도 없고 evidence도 없으면
    if not raw_exists and not evidences:
        if src.get("existing_script"):
            audit_status = "SCRIPT_EXISTS_NOT_COLLECTED"
            action = "COLLECT_RAW"
        else:
            audit_status = "NOT_COLLECTED"
            action = "COLLECT_RAW" if not src.get("enabled") is False else "EXCLUDE_FOR_NOW"
    # R03: evidence 있으면 PARTIAL 또는 VERIFIED 후보
    elif evidences:
        if raw_exists:
            audit_status = "COLLECTED_PARTIAL"
            action = "GENERATE_EVIDENCE_CANDIDATE"
        else:
            audit_status = "REFERENCED_ONLY"
            action = "COLLECT_RAW"
    else:
        # raw는 있지만 evidence 없음
        audit_status = "COLLECTED_PARTIAL"
        action = "GENERATE_EVIDENCE_CANDIDATE"

    # R04: 별표/서식 관련 notes 또는 미수집 가능성
    notes = src.get("notes", "") or ""
    if "별표" in notes or "서식" in notes:
        if audit_status == "COLLECTED_PARTIAL":
            action = "COLLECT_APPENDIX_FORM"
            src_issues.append("별표/서식 수집 필요")

    # R08: queue enabled=false인데 raw/evidence 없으면 상태 불일치
    if q_item and not q_item.get("enabled", True) and not raw_exists and not evidences:
        issues.append({
            "level": "WARN", "rule": "R08",
            "source_code": sc,
            "msg": "queue enabled=false인데 raw/evidence 없음 — 상태 불일치",
        })

    return {
        "source_code": sc,
        "official_name": src.get("official_name", ""),
        "audit_status": audit_status,
        "proposed_action": action,
        "registry_status": reg_status,
        "evidence_count": len(evidences),
        "evidence_ids": evidences,
        "raw_exists": raw_exists,
        "raw_article_count": raw_article_count,
        "mst": mst,
        "priority": src.get("priority", ""),
        "source_type": source_type,
        "notes": src_issues,
    }


# ── 5a. admrul ↔ registry 정규화 매칭 ──────────────────────────────────────────
def _match_admrul_to_registry(
    raw_admrul: dict[str, dict],
    sources: list[dict],
) -> tuple[dict[str, str], dict[str, str], dict]:
    """
    admrul raw_id → matched source_code 매핑 반환.
    매칭 방법(method): exact / partial / none
    반환: (raw_id→source_code, source_code→raw_id, 통계 dict)
    """
    # registry에서 mst=None인 source만 대상 (mst가 있으면 law index에서 처리)
    admrul_registry: list[dict] = [
        s for s in sources
        if not s.get("law_mst") and s.get("source_type") not in WATCH_SOURCE_TYPES
        and s.get("source_type") not in {"CASE_DATA", "ACCIDENT_DATA", "GUIDE", "STANDARD"}
    ]
    reg_norm_map = {
        _norm_name(s.get("official_name", "")): s.get("source_code", "")
        for s in admrul_registry if s.get("official_name")
    }

    rid_to_sc: dict[str, str] = {}
    sc_to_rid: dict[str, str] = {}
    method_counts: dict[str, int] = defaultdict(int)

    for rid, info in raw_admrul.items():
        norm = info["norm_title"]
        if not norm:
            method_counts["no_title"] += 1
            continue

        # 1순위: 완전일치
        if norm in reg_norm_map:
            sc = reg_norm_map[norm]
            rid_to_sc[rid] = sc
            sc_to_rid[sc] = rid
            method_counts["exact"] += 1
            continue

        # 2순위: registry name이 raw name에 포함 (부분일치, 최소 6자)
        matched_sc = None
        for reg_norm, sc in reg_norm_map.items():
            if len(reg_norm) >= 6 and reg_norm in norm:
                matched_sc = sc
                break
        if matched_sc:
            rid_to_sc[rid] = matched_sc
            sc_to_rid[matched_sc] = rid
            method_counts["partial"] += 1
            continue

        method_counts["unmatched"] += 1

    log.info(
        f"admrul 매칭: exact={method_counts['exact']}, "
        f"partial={method_counts['partial']}, "
        f"unmatched={method_counts['unmatched']}, "
        f"no_title={method_counts.get('no_title', 0)}"
    )
    return rid_to_sc, sc_to_rid, dict(method_counts)


# ── 5b. registry 미등록 raw source 탐지 (R01, R06) ──────────────────────────────
def _find_unregistered_raw(
    raw_by_mst: dict[str, dict],
    raw_admrul: dict[str, dict],
    registry_msts: set[str],
    admrul_rid_to_sc: dict[str, str],
    issues: list[dict],
) -> list[dict]:
    """law raw 미등록 + admrul raw 미등록(오탐 제거 후) 합산."""
    unregistered = []

    # law raw (MST 기반) — 기존 로직 유지
    for mst, info in raw_by_mst.items():
        if mst in registry_msts:
            continue
        title = info.get("title", "")
        action = "ADD_TO_REGISTRY"
        for kw in ELECTRIC_CHEMICAL_KEYWORDS:
            if kw in title:
                break
        else:
            action = "NEEDS_NAME_CONFIRMATION"
        unregistered.append({
            "raw_id": mst,
            "title": title,
            "source_type": info.get("source_type", ""),
            "article_count": info.get("article_count", 0),
            "raw_kind": "law",
            "proposed_action": action,
        })
        issues.append({
            "level": "WARN", "rule": "R01",
            "raw_id": mst,
            "msg": f"law raw 미등록: {title} (MST={mst})",
        })

    # admrul raw — 매칭된 것은 오탐, 미매칭만 진짜 미등록
    for rid, info in raw_admrul.items():
        if rid in admrul_rid_to_sc:
            continue  # registry에 매칭됨 → 오탐 아님
        title = info.get("title", "")
        action = "ADD_TO_REGISTRY"
        for kw in ELECTRIC_CHEMICAL_KEYWORDS:
            if kw in title:
                break
        else:
            action = "NEEDS_NAME_CONFIRMATION"
        unregistered.append({
            "raw_id": rid,
            "title": title,
            "source_type": info.get("law_type", ""),
            "ministry": info.get("ministry", ""),
            "article_count": info.get("article_count", 0),
            "raw_kind": "admrul",
            "proposed_action": action,
        })
        issues.append({
            "level": "WARN", "rule": "R01",
            "raw_id": rid,
            "msg": f"admrul raw 미등록: {title} (raw_id={rid}, {info.get('law_type','')})",
        })

    log.info(f"registry 미등록 raw source: {len(unregistered)}개 (law+admrul 합산, 오탐 제거 후)")
    return unregistered


# ── 6. evidence_registry → sources_registry 역참조 검증 (R10) ──────────────────
def _check_evidence_orphan(
    evidence_reg: dict | None,
    registry_codes: set[str],
    issues: list[dict],
) -> list[str]:
    orphans = []
    if not evidence_reg:
        return orphans
    for ev in evidence_reg.get("evidences", []):
        sc = ev.get("source_code", "")
        eid = ev.get("evidence_id", "")
        if sc and sc not in registry_codes:
            issues.append({
                "level": "FAIL", "rule": "R10",
                "evidence_id": eid,
                "msg": f"evidence {eid}의 source_code={sc}가 registry에 없음",
            })
            orphans.append(eid)
    return orphans


# ── 메인 감사 ────────────────────────────────────────────────────────────────────
def run_audit() -> int:
    log.info("=" * 60)
    log.info("법령·지침 수집 전수 감사 시작")
    log.info("=" * 60)

    # 데이터 로드
    registry_data  = _load_yaml(REGISTRY_PATH)
    evidence_data  = _load_yaml(EVIDENCE_REG)
    queue_data     = _load_yaml(QUEUE_PATH)

    if not registry_data:
        log.error("registry 파일 없음 — 감사 중단")
        return 1

    sources: list[dict] = registry_data.get("sources", [])
    registry_codes = {s.get("source_code") for s in sources}
    registry_msts  = {str(s.get("law_mst", "") or "").strip() for s in sources} - {""}

    log.info(f"registry: {len(sources)}개 source 로드")

    raw_by_mst     = _build_raw_law_index()
    raw_admrul     = _build_raw_admrul_index()
    evidence_idx   = _build_evidence_index(evidence_data)
    queue_idx      = _build_queue_index(queue_data)

    issues: list[dict] = []

    # admrul ↔ registry 정규화 매칭 (오탐 분리)
    admrul_rid_to_sc, admrul_sc_to_rid, admrul_match_stats = _match_admrul_to_registry(
        raw_admrul, sources
    )
    admrul_matched_count   = admrul_match_stats.get("exact", 0) + admrul_match_stats.get("partial", 0)
    admrul_unmatched_count = admrul_match_stats.get("unmatched", 0)
    admrul_false_positive_reduction = admrul_matched_count

    # registry source 전수 감사
    audited: list[dict] = []
    for src in sources:
        result = _audit_registry_source(src, raw_by_mst, evidence_idx, queue_idx, issues)
        audited.append(result)

    # registry 미등록 raw source (법률 MST + admrul 오탐 제거 후)
    unregistered_raw = _find_unregistered_raw(
        raw_by_mst, raw_admrul, registry_msts, admrul_rid_to_sc, issues
    )

    # evidence orphan 검증
    orphan_evidences = _check_evidence_orphan(evidence_data, registry_codes, issues)

    # ── 집계 ──────────────────────────────────────────────────────────────────
    status_counts: dict[str, int] = defaultdict(int)
    action_counts: dict[str, int] = defaultdict(int)
    for a in audited:
        status_counts[a["audit_status"]] += 1
        action_counts[a["proposed_action"]] += 1

    fail_count = sum(1 for i in issues if i["level"] == "FAIL")
    warn_count = sum(1 for i in issues if i["level"] == "WARN")
    info_count = sum(1 for i in issues if i["level"] == "INFO")

    # 부족분 보강 큐 (proposed_action 기준)
    restock_queue = [
        a for a in audited
        if a["proposed_action"] not in ("SKIP_ALREADY_VERIFIED", "WATCH_ONLY", "EXCLUDE_FOR_NOW")
    ]
    restock_queue.sort(key=lambda x: (
        {"COLLECT_RAW": 0, "COLLECT_APPENDIX_FORM": 1,
         "GENERATE_EVIDENCE_CANDIDATE": 2, "ADD_TO_REQUIREMENT_MATRIX_CANDIDATE": 3}.get(
            x["proposed_action"], 9),
        x.get("priority", "P9"),
    ))

    # TOP 10 후보 목록
    registry_add_candidates = sorted(
        unregistered_raw,
        key=lambda x: -x.get("article_count", 0),
    )[:10]

    appendix_candidates = [
        a for a in audited
        if a["proposed_action"] == "COLLECT_APPENDIX_FORM"
    ][:10]

    evidence_candidates = [
        a for a in audited
        if a["proposed_action"] in ("GENERATE_EVIDENCE_CANDIDATE",) and a["raw_exists"]
    ][:10]

    matrix_candidates = [
        a for a in audited
        if a["proposed_action"] == "ADD_TO_REQUIREMENT_MATRIX_CANDIDATE"
    ][:10]

    dup_risk = [
        a for a in audited
        if a["audit_status"] == "COLLECTED_VERIFIED"
        and any(i["rule"] == "R09" and i["source_code"] == a["source_code"] for i in issues)
    ]

    now_kst = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M KST")

    # ── JSON 리포트 ────────────────────────────────────────────────────────────
    # admrul 미매칭 상위 50개 + 자동 분류
    admrul_unmatched_list = [
        info for rid, info in raw_admrul.items()
        if rid not in admrul_rid_to_sc
    ]
    admrul_unmatched_list.sort(key=lambda x: -x.get("article_count", 0))

    # admrul 189건 자동 분류 dry-run
    admrul_classified: dict[str, list[dict]] = {
        "ADMRUL_SAFETY_P1": [],
        "ADMRUL_SAFETY_P2": [],
        "ADMRUL_WATCH_ONLY": [],
        "ADMRUL_EXCLUDE_CANDIDATE": [],
        "ADMRUL_NEEDS_REVIEW": [],
    }
    keyword_hit_counter: dict[str, int] = defaultdict(int)

    for info in admrul_unmatched_list:
        group, hits = _classify_admrul(
            info.get("title", ""),
            info.get("law_type", ""),
            info.get("ministry", ""),
        )
        for kw in hits:
            keyword_hit_counter[kw] += 1
        entry = {
            "raw_id": info["raw_id"],
            "title": info["title"],
            "law_type": info.get("law_type", ""),
            "ministry": info.get("ministry", ""),
            "article_count": info.get("article_count", 0),
            "classification": group,
            "hit_keywords": hits,
        }
        admrul_classified[group].append(entry)

    log.info(
        f"admrul 분류: P1={len(admrul_classified['ADMRUL_SAFETY_P1'])}, "
        f"P2={len(admrul_classified['ADMRUL_SAFETY_P2'])}, "
        f"WATCH={len(admrul_classified['ADMRUL_WATCH_ONLY'])}, "
        f"EXCLUDE={len(admrul_classified['ADMRUL_EXCLUDE_CANDIDATE'])}, "
        f"REVIEW={len(admrul_classified['ADMRUL_NEEDS_REVIEW'])}"
    )

    # registry 편입 추천 TOP 20: P1 우선, 그 다음 P2 (조문수 내림차순)
    recommended_add = sorted(
        admrul_classified["ADMRUL_SAFETY_P1"] + admrul_classified["ADMRUL_SAFETY_P2"],
        key=lambda x: (
            0 if x["classification"] == "ADMRUL_SAFETY_P1" else 1,
            -x.get("article_count", 0),
        ),
    )[:20]

    # 제외 추천 TOP 20: EXCLUDE_CANDIDATE (조문수 오름차순 — 작은 것 먼저 제외)
    recommended_exclude = sorted(
        admrul_classified["ADMRUL_EXCLUDE_CANDIDATE"],
        key=lambda x: x.get("article_count", 0),
    )[:20]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline": {
            "registry_source_count": len(sources),
            "raw_law_count": len(raw_by_mst),
            "raw_admrul_count": len(raw_admrul),
            "evidence_file_count": len(list(EVIDENCE_DIR.glob("*.json"))) if EVIDENCE_DIR.exists() else 0,
            "evidence_registry_count": sum(len(v) for v in evidence_idx.values()),
            "law_content_article_count": sum(
                v["article_count"] for v in raw_by_mst.values()
            ),
            "admrul_article_count": sum(
                v["article_count"] for v in raw_admrul.values()
            ),
        },
        "admrul_matching": {
            "admrul_raw_total": len(raw_admrul),
            "admrul_matched_count": admrul_matched_count,
            "admrul_unmatched_count": admrul_unmatched_count,
            "admrul_match_method_breakdown": admrul_match_stats,
            "admrul_false_positive_reduction_count": admrul_false_positive_reduction,
            "admrul_unmatched_top50": admrul_unmatched_list[:50],
        },
        "admrul_classification": {
            "admrul_unregistered_total": len(admrul_unmatched_list),
            "admrul_safety_p1_count": len(admrul_classified["ADMRUL_SAFETY_P1"]),
            "admrul_safety_p2_count": len(admrul_classified["ADMRUL_SAFETY_P2"]),
            "admrul_watch_only_count": len(admrul_classified["ADMRUL_WATCH_ONLY"]),
            "admrul_exclude_candidate_count": len(admrul_classified["ADMRUL_EXCLUDE_CANDIDATE"]),
            "admrul_needs_review_count": len(admrul_classified["ADMRUL_NEEDS_REVIEW"]),
            "admrul_safety_p1_candidates": admrul_classified["ADMRUL_SAFETY_P1"],
            "admrul_safety_p2_candidates": admrul_classified["ADMRUL_SAFETY_P2"],
            "admrul_watch_only_candidates": admrul_classified["ADMRUL_WATCH_ONLY"],
            "admrul_exclude_candidates": admrul_classified["ADMRUL_EXCLUDE_CANDIDATE"],
            "admrul_needs_review": admrul_classified["ADMRUL_NEEDS_REVIEW"],
            "recommended_registry_add_top20": recommended_add,
            "recommended_exclude_top20": recommended_exclude,
            "classification_keyword_hit_summary": dict(
                sorted(keyword_hit_counter.items(), key=lambda x: -x[1])
            ),
        },
        "status_summary": dict(status_counts),
        "action_summary": dict(action_counts),
        "issue_summary": {"FAIL": fail_count, "WARN": warn_count, "INFO": info_count},
        "audited_sources": audited,
        "unregistered_raw_sources": unregistered_raw,
        "orphan_evidences": orphan_evidences,
        "restock_queue": restock_queue,
        "registry_add_candidates_top10": registry_add_candidates,
        "appendix_form_candidates_top10": appendix_candidates,
        "evidence_candidates_top10": evidence_candidates,
        "matrix_candidates_top10": matrix_candidates,
        "duplicate_collection_risk": dup_risk,
        "all_issues": issues,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / "legal_source_collection_master_audit.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"JSON 리포트: {json_path.relative_to(ROOT)}")

    # ── MD 리포트 ──────────────────────────────────────────────────────────────
    def _status_rows(status: str) -> list[dict]:
        return [a for a in audited if a["audit_status"] == status]

    md_lines = [
        f"# 법령·지침 수집 전수 감사 리포트",
        f"",
        f"> 생성: {now_kst}  |  스크립트: `scripts/safety/audit_legal_source_collection_master.py`",
        f"",
        f"---",
        f"",
        f"## 1. 현재 기준선",
        f"",
        f"| 항목 | 값 |",
        f"|---|---|",
        f"| registry source 수 | {len(sources)}개 |",
        f"| raw 수집 법령 종류 | {len(raw_by_mst)}개 |",
        f"| evidence 파일 수 | {report['baseline']['evidence_file_count']}개 |",
        f"| evidence registry 매핑 수 | {report['baseline']['evidence_registry_count']}개 |",
        f"| law_content 총 조문 수 | {report['baseline']['law_content_article_count']}조 |",
        f"",
        f"---",
        f"",
        f"## 2. 전체 source 상태 요약",
        f"",
        f"| 상태 | 건수 |",
        f"|---|---|",
    ]
    for st, cnt in sorted(status_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f"| {st} | {cnt} |")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 3. COLLECTED_VERIFIED — 재수집 금지 목록",
        f"",
    ]
    for a in _status_rows("COLLECTED_VERIFIED"):
        md_lines.append(f"- `{a['source_code']}` — evidence {a['evidence_count']}개")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 4. COLLECTED_PARTIAL — 부족분 목록",
        f"",
    ]
    for a in _status_rows("COLLECTED_PARTIAL"):
        md_lines.append(
            f"- `{a['source_code']}` ({a.get('official_name','')}) — "
            f"evidence {a['evidence_count']}개, raw {'있음' if a['raw_exists'] else '없음'}, "
            f"action={a['proposed_action']}"
        )

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 5. RAW_COLLECTED_REGISTRY_MISSING — registry 미등록 raw source",
        f"",
        f"| raw_id | 법령명 | 조문수 | 제안 action | raw_kind |",
        f"|---|---|---|---|---|",
    ]
    for u in unregistered_raw:
        md_lines.append(
            f"| {u['raw_id']} | {u['title']} | {u['article_count']} | {u['proposed_action']} "
            f"| {u.get('raw_kind','law')} |"
        )

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 6. REGISTRY_ONLY_RAW_MISSING — raw 없는 registry source",
        f"",
    ]
    for a in _status_rows("REGISTRY_ONLY_RAW_MISSING"):
        md_lines.append(f"- `{a['source_code']}` ({a.get('official_name','')})")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 7. NOT_COLLECTED — 미수집 source",
        f"",
    ]
    for a in _status_rows("NOT_COLLECTED") + _status_rows("SCRIPT_EXISTS_NOT_COLLECTED"):
        md_lines.append(
            f"- `{a['source_code']}` ({a.get('official_name','')}) — {a['audit_status']}"
        )

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 8. WATCH_ONLY — 관찰 대상",
        f"",
    ]
    for a in _status_rows("WATCH_ONLY"):
        md_lines.append(f"- `{a['source_code']}`")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 9. registry 편입 후보 TOP 10",
        f"",
        f"| 순위 | MST | 법령명 | 조문수 |",
        f"|---|---|---|---|",
    ]
    for i, c in enumerate(registry_add_candidates, 1):
        md_lines.append(f"| {i} | {c['raw_id']} | {c['title']} | {c['article_count']} |")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 10. 별표/서식 추가 수집 후보 TOP 10",
        f"",
    ]
    for i, c in enumerate(appendix_candidates, 1):
        md_lines.append(f"{i}. `{c['source_code']}`")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 11. evidence 생성 후보 TOP 10",
        f"",
    ]
    for i, c in enumerate(evidence_candidates, 1):
        md_lines.append(
            f"{i}. `{c['source_code']}` — raw {c['raw_article_count']}조, evidence {c['evidence_count']}개"
        )

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 12. requirement matrix 반영 후보 TOP 10",
        f"",
    ]
    for i, c in enumerate(matrix_candidates, 1):
        md_lines.append(f"{i}. `{c['source_code']}`")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 13. 중복 수집 위험 목록",
        f"",
    ]
    if dup_risk:
        for a in dup_risk:
            md_lines.append(f"- `{a['source_code']}` — COLLECTED_VERIFIED인데 queue enabled=true")
    else:
        md_lines.append("없음")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 13-A. admrul 매칭 분석",
        f"",
        f"| 항목 | 값 |",
        f"|---|---|",
        f"| admrul raw 총계 | {len(raw_admrul)}개 |",
        f"| registry 매칭 성공 (exact) | {admrul_match_stats.get('exact', 0)}개 |",
        f"| registry 매칭 성공 (partial) | {admrul_match_stats.get('partial', 0)}개 |",
        f"| 오탐 감소 (매칭 성공) | {admrul_false_positive_reduction}개 |",
        f"| 진짜 미등록 (unmatched) | {admrul_unmatched_count}개 |",
        f"",
        f"### admrul 매칭 성공 목록",
        f"",
    ]
    for rid, sc in sorted(admrul_rid_to_sc.items()):
        info = raw_admrul.get(rid, {})
        md_lines.append(f"- `{sc}` ← raw_id={rid} [{info.get('law_type','')}] {info.get('title','')}")

    md_lines += [
        f"",
        f"### admrul 미매칭 (진짜 미등록) 상위 20개",
        f"",
        f"| raw_id | 법령명 | 종류 | 소관부처 | 조문수 |",
        f"|---|---|---|---|---|",
    ]
    for info in admrul_unmatched_list[:20]:
        md_lines.append(
            f"| {info['raw_id']} | {info['title']} | {info.get('law_type','')} "
            f"| {info.get('ministry','')} | {info.get('article_count',0)} |"
        )

    # ── 13-B. admrul 189건 자동분류 ────────────────────────────────────────────
    cl = admrul_classified
    md_lines += [
        f"",
        f"---",
        f"",
        f"## 13-B. admrul 미등록 {len(admrul_unmatched_list)}건 자동분류 결과",
        f"",
        f"| 분류 | 건수 |",
        f"|---|---|",
        f"| ADMRUL_SAFETY_P1 (안전인증·방호·보호구 등) | {len(cl['ADMRUL_SAFETY_P1'])} |",
        f"| ADMRUL_SAFETY_P2 (건설·기계·화학·가스 등) | {len(cl['ADMRUL_SAFETY_P2'])} |",
        f"| ADMRUL_WATCH_ONLY | {len(cl['ADMRUL_WATCH_ONLY'])} |",
        f"| ADMRUL_EXCLUDE_CANDIDATE | {len(cl['ADMRUL_EXCLUDE_CANDIDATE'])} |",
        f"| ADMRUL_NEEDS_REVIEW | {len(cl['ADMRUL_NEEDS_REVIEW'])} |",
        f"",
        f"### ADMRUL_SAFETY_P1 후보",
        f"",
        f"| raw_id | 법령명 | 종류 | 소관부처 | 조문수 | 키워드 |",
        f"|---|---|---|---|---|---|",
    ]
    for e in cl["ADMRUL_SAFETY_P1"]:
        md_lines.append(
            f"| {e['raw_id']} | {e['title']} | {e['law_type']} "
            f"| {e['ministry']} | {e['article_count']} | {', '.join(e['hit_keywords'][:3])} |"
        )

    md_lines += [
        f"",
        f"### ADMRUL_SAFETY_P2 후보",
        f"",
        f"| raw_id | 법령명 | 종류 | 소관부처 | 조문수 | 키워드 |",
        f"|---|---|---|---|---|---|",
    ]
    for e in cl["ADMRUL_SAFETY_P2"]:
        md_lines.append(
            f"| {e['raw_id']} | {e['title']} | {e['law_type']} "
            f"| {e['ministry']} | {e['article_count']} | {', '.join(e['hit_keywords'][:3])} |"
        )

    md_lines += [
        f"",
        f"### ADMRUL_WATCH_ONLY",
        f"",
    ]
    for e in cl["ADMRUL_WATCH_ONLY"]:
        md_lines.append(f"- `{e['raw_id']}` {e['title']} ({e['law_type']})")

    md_lines += [
        f"",
        f"### ADMRUL_EXCLUDE_CANDIDATE",
        f"",
    ]
    for e in cl["ADMRUL_EXCLUDE_CANDIDATE"]:
        md_lines.append(f"- `{e['raw_id']}` {e['title']} — {', '.join(e['hit_keywords'][:2])}")

    md_lines += [
        f"",
        f"### ADMRUL_NEEDS_REVIEW",
        f"",
    ]
    for e in cl["ADMRUL_NEEDS_REVIEW"]:
        md_lines.append(f"- `{e['raw_id']}` [{e['law_type']}] {e['title']} ({e['ministry']})")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 13-C. registry 편입 추천 TOP 20",
        f"",
        f"| 순위 | 분류 | raw_id | 법령명 | 조문수 | 키워드 |",
        f"|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(recommended_add, 1):
        md_lines.append(
            f"| {i} | {e['classification']} | {e['raw_id']} | {e['title']} "
            f"| {e['article_count']} | {', '.join(e['hit_keywords'][:3])} |"
        )

    md_lines += [
        f"",
        f"## 13-D. 제외 추천 TOP 20",
        f"",
        f"| 순위 | raw_id | 법령명 | 조문수 | 이유 |",
        f"|---|---|---|---|---|",
    ]
    for i, e in enumerate(recommended_exclude, 1):
        md_lines.append(
            f"| {i} | {e['raw_id']} | {e['title']} "
            f"| {e['article_count']} | {', '.join(e['hit_keywords'][:2])} |"
        )

    md_lines += [
        f"",
        f"## 13-E. 키워드 적중 빈도 요약",
        f"",
        f"| 키워드 | 적중 건수 |",
        f"|---|---|",
    ]
    for kw, cnt in sorted(keyword_hit_counter.items(), key=lambda x: -x[1])[:20]:
        md_lines.append(f"| {kw} | {cnt} |")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 14. FAIL / WARN / INFO 요약",
        f"",
        f"| 레벨 | 건수 |",
        f"|---|---|",
        f"| FAIL | {fail_count} |",
        f"| WARN | {warn_count} |",
        f"| INFO | {info_count} |",
        f"",
    ]
    for iss in issues:
        lv = iss.get("level", "INFO")
        rule = iss.get("rule", "")
        msg = iss.get("msg", "")
        md_lines.append(f"- [{lv}] ({rule}) {msg}")

    md_lines += [
        f"",
        f"---",
        f"",
        f"## 15. 다음 실행 순서 제안",
        f"",
        f"1. **registry 편입**: raw에 있지만 registry 미등록 법령 {len(unregistered_raw)}개 → `ADD_TO_REGISTRY`",
        f"2. **별표/서식 수집**: `COLLECT_APPENDIX_FORM` 대상 {len(appendix_candidates)}개",
        f"3. **evidence 생성**: raw 있는 PARTIAL source {len(evidence_candidates)}개 → `GENERATE_EVIDENCE_CANDIDATE`",
        f"4. **미수집 수집**: `NOT_COLLECTED` / `SCRIPT_EXISTS_NOT_COLLECTED` 대상 {len(_status_rows('NOT_COLLECTED')) + len(_status_rows('SCRIPT_EXISTS_NOT_COLLECTED'))}개",
        f"5. **requirement matrix 반영**: evidence 충분한 source {len(matrix_candidates)}개",
        f"",
        f"---",
        f"",
        f"## 최종 판정",
        f"",
    ]

    if fail_count > 0:
        verdict = "FAIL"
        md_lines.append(f"**{verdict}** — FAIL {fail_count}건 해결 후 재실행 필요")
    elif warn_count > 0:
        verdict = "WARN"
        md_lines.append(f"**{verdict}** — WARN {warn_count}건 확인 후 진행 가능")
    else:
        verdict = "PASS"
        md_lines.append(f"**{verdict}** — 이상 없음")

    md_path = REPORTS_DIR / "legal_source_collection_master_audit.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    log.info(f"MD  리포트: {md_path.relative_to(ROOT)}")

    # ── 콘솔 요약 ──────────────────────────────────────────────────────────────
    log.info("=" * 60)
    log.info("감사 결과 요약")
    log.info("=" * 60)
    for st, cnt in sorted(status_counts.items(), key=lambda x: -x[1]):
        log.info(f"  {st:<40} {cnt:>3}개")
    log.info(f"registry 미등록 raw: {len(unregistered_raw)}개")
    log.info(f"orphan evidence:     {len(orphan_evidences)}개")
    log.info(f"FAIL={fail_count}  WARN={warn_count}  INFO={info_count}")
    log.info(f"최종 판정: {verdict}")
    log.info("=" * 60)

    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    sys.exit(run_audit())
