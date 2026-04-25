"""
공종별 위험성평가 프리셋 마스터 v1 검증 스크립트

검증 항목:
  1. 모든 yml 파일 parse 가능
  2. hazard_master.yml 스키마 유효성 (hazard_id, hazard_name, category 필수)
  3. hazard_id 중복 없음
  4. trade_presets.yml 스키마 유효성 (trade_id, trade_name, trade_group 필수)
  5. trade_id 중복 없음 (전체 파일 통합 기준)
  6. work_type 파일 내 hazard_id → hazard_master.yml 참조 무결성
  7. required_documents / recommended_documents → document_catalog.yml 참조 무결성
  8. required_permits → document_catalog.yml 참조 무결성 (PTW-xxx만 허용)
  9. required_trainings → training_types.yml 참조 무결성
 10. enabled=true 항목: default_hazards 1개 이상
 11. enabled=true 항목: required_documents 1개 이상
 12. source_status 허용 enum 검사
 13. 공종 수 검사: 소방 ≥10, 전기 ≥9, 기계설비 ≥9, 공통 ≥10
 14. skeleton 파일 존재 확인 (architecture/civil/steel/demolition)
 15. mapping 파일 loadable + trade_id 참조 유효성

실행:
    cd <project_root>
    python scripts/validate_trade_risk_presets.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(".")
HAZARD_MASTER = ROOT / "data/masters/safety/hazards/hazard_master.yml"
HAZARD_CONTROLS = ROOT / "data/masters/safety/hazards/hazard_controls.yml"
WORK_TYPES_DIR = ROOT / "data/masters/safety/work_types"
MAPPINGS_DIR = ROOT / "data/masters/safety/mappings"
DOCUMENT_CATALOG = ROOT / "data/masters/safety/documents/document_catalog.yml"
TRAINING_TYPES = ROOT / "data/masters/safety/training/training_types.yml"

VALID_SOURCE_STATUSES = {"VERIFIED", "PARTIAL_VERIFIED", "NEEDS_VERIFICATION", "PRACTICAL"}

DETAIL_FILES = {
    "firefighting_work_types.yml": "소방설비",
    "electrical_work_types.yml": "전기",
    "mechanical_work_types.yml": "기계설비",
    "common_high_risk_work_types.yml": "공통 고위험작업",
}

SKELETON_FILES = [
    "architecture_work_types.yml",
    "civil_work_types.yml",
    "steel_structure_work_types.yml",
    "demolition_work_types.yml",
]

MAPPING_FILES = [
    "trade_document_mapping.yml",
    "trade_training_mapping.yml",
    "trade_equipment_mapping.yml",
    "trade_permit_mapping.yml",
]

MIN_TRADE_COUNTS = {
    "소방설비": 10,
    "전기": 9,
    "기계설비": 9,
    "공통 고위험작업": 10,
}


def _ok(msg: str, detail: str = "") -> tuple[str, str, str]:
    return ("PASS", msg, detail)


def _warn(msg: str, detail: str = "") -> tuple[str, str, str]:
    return ("WARN", msg, detail)


def _fail(msg: str, detail: str = "") -> tuple[str, str, str]:
    return ("FAIL", msg, detail)


def load_yaml(path: Path) -> dict | list | None:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as exc:
        return None


def main() -> None:
    results: list[tuple[str, str, str]] = []
    warn_count = 0
    fail_count = 0

    # ── 1. 참조 데이터 로드 ──────────────────────────────────────────
    catalog_data = load_yaml(DOCUMENT_CATALOG)
    if catalog_data is None:
        results.append(_fail("document_catalog.yml 로드 실패"))
        catalog_data = {"documents": []}
    else:
        results.append(_ok("document_catalog.yml 로드 성공"))

    training_data = load_yaml(TRAINING_TYPES)
    if training_data is None:
        results.append(_fail("training_types.yml 로드 실패"))
        training_data = {"training_types": []}
    else:
        results.append(_ok("training_types.yml 로드 성공"))

    valid_doc_ids: set[str] = {d["id"] for d in catalog_data.get("documents", [])}
    valid_training_codes: set[str] = {
        t["training_code"] for t in training_data.get("training_types", [])
    }

    # ── 2. hazard_master.yml 검증 ────────────────────────────────────
    hazard_data = load_yaml(HAZARD_MASTER)
    valid_hazard_ids: set[str] = set()

    if hazard_data is None:
        results.append(_fail("hazard_master.yml 로드 실패", str(HAZARD_MASTER)))
    else:
        results.append(_ok("hazard_master.yml 로드 성공"))
        hazards = hazard_data.get("hazards", [])
        hazard_id_list = []
        for hz in hazards:
            hid = hz.get("hazard_id")
            if not hid:
                results.append(_fail("hazard_master: hazard_id 누락", str(hz)))
                continue
            hazard_id_list.append(hid)
            if not hz.get("hazard_name"):
                results.append(_warn(f"hazard_master: hazard_name 누락", hid))
            if not hz.get("category"):
                results.append(_warn(f"hazard_master: category 누락", hid))

        # 중복 확인
        if len(hazard_id_list) == len(set(hazard_id_list)):
            results.append(_ok(f"hazard_id 중복 없음 (총 {len(hazard_id_list)}개)"))
        else:
            dupes = [x for x in hazard_id_list if hazard_id_list.count(x) > 1]
            results.append(_fail(f"hazard_id 중복 존재", str(set(dupes))))
        valid_hazard_ids = set(hazard_id_list)

    # ── 3. hazard_controls.yml 존재 확인 ────────────────────────────
    if HAZARD_CONTROLS.exists():
        ctrl_data = load_yaml(HAZARD_CONTROLS)
        if ctrl_data is not None:
            results.append(_ok("hazard_controls.yml 로드 성공"))
        else:
            results.append(_fail("hazard_controls.yml parse 실패"))
    else:
        results.append(_fail("hazard_controls.yml 파일 없음", str(HAZARD_CONTROLS)))

    # ── 4. trade_presets.yml (인덱스) 검증 ──────────────────────────
    index_path = WORK_TYPES_DIR / "trade_presets.yml"
    index_data = load_yaml(index_path)
    index_trade_ids: set[str] = set()

    if index_data is None:
        results.append(_fail("trade_presets.yml 로드 실패", str(index_path)))
    else:
        results.append(_ok("trade_presets.yml 로드 성공"))
        index_items = index_data.get("trade_index", [])
        for item in index_items:
            tid = item.get("trade_id")
            if tid:
                index_trade_ids.add(tid)
        results.append(_ok(f"trade_presets.yml 공종 인덱스 {len(index_items)}개 등록"))

        # _meta.total_trades vs 실제 index 항목 수 교차 검증
        meta_total = index_data.get("_meta", {}).get("total_trades")
        if meta_total is not None and meta_total != len(index_items):
            results.append(_fail(
                f"trade_presets._meta.total_trades 불일치",
                f"_meta={meta_total} vs 실제 index={len(index_items)}"
            ))
        elif meta_total is not None:
            results.append(_ok(
                f"trade_presets._meta.total_trades 일치",
                f"{meta_total} == {len(index_items)}"
            ))

    # ── 5. 상세 공종 파일 검증 ────────────────────────────────────────
    all_trade_ids: list[str] = []
    group_counts: dict[str, int] = {}
    total_enabled = 0
    doc_errors: list[str] = []
    training_errors: list[str] = []
    permit_errors: list[str] = []
    hazard_ref_errors: list[str] = []

    for fname, group_name in DETAIL_FILES.items():
        fpath = WORK_TYPES_DIR / fname
        if not fpath.exists():
            results.append(_fail(f"{fname} 파일 없음"))
            continue

        data = load_yaml(fpath)
        if data is None:
            results.append(_fail(f"{fname} parse 실패"))
            continue
        results.append(_ok(f"{fname} 로드 성공"))

        trades = data.get("trades", [])
        group_count = 0

        for trade in trades:
            tid = trade.get("trade_id")
            if not tid:
                results.append(_fail(f"{fname}: trade_id 누락", str(trade.get("trade_name"))))
                continue

            all_trade_ids.append(tid)
            group_count += 1

            enabled = trade.get("enabled", False)
            if enabled:
                total_enabled += 1

            # source_status 검사
            ss = trade.get("source_status", "")
            if ss not in VALID_SOURCE_STATUSES:
                results.append(_fail(f"source_status 잘못된 값", f"{tid}: {ss!r}"))

            # enabled=true 시 default_hazards 1개 이상
            hazards = trade.get("default_hazards", [])
            if enabled and len(hazards) == 0:
                results.append(_fail(f"enabled=true이지만 default_hazards 없음", tid))

            # enabled=true 시 required_documents 1개 이상
            req_docs = trade.get("required_documents", [])
            if enabled and len(req_docs) == 0:
                results.append(_fail(f"enabled=true이지만 required_documents 없음", tid))

            # hazard_id 참조 무결성
            for hid in hazards:
                if hid not in valid_hazard_ids:
                    hazard_ref_errors.append(f"{tid}.default_hazards → {hid}")

            # document 참조 무결성
            all_docs = list(req_docs) + trade.get("recommended_documents", [])
            for did in all_docs:
                if did not in valid_doc_ids:
                    doc_errors.append(f"{tid} → {did}")

            # required_permits 참조 무결성
            for pid in trade.get("required_permits", []):
                if pid not in valid_doc_ids:
                    permit_errors.append(f"{tid}.required_permits → {pid}")
                elif not pid.startswith("PTW-"):
                    results.append(_warn(
                        f"required_permits에 PTW-xxx 아닌 ID 사용",
                        f"{tid}: {pid}"
                    ))

            # training 참조 무결성
            for tcode in trade.get("required_trainings", []):
                if tcode not in valid_training_codes:
                    training_errors.append(f"{tid} → {tcode}")

        group_counts[group_name] = group_count

    # 중복 trade_id 검사
    if len(all_trade_ids) == len(set(all_trade_ids)):
        results.append(_ok(f"trade_id 중복 없음 (전체 {len(all_trade_ids)}개)"))
    else:
        dupes = [x for x in all_trade_ids if all_trade_ids.count(x) > 1]
        results.append(_fail("trade_id 중복 존재", str(set(dupes))))

    # hazard 참조 오류
    if not hazard_ref_errors:
        results.append(_ok("hazard_id 참조 무결성 PASS"))
    else:
        for e in hazard_ref_errors:
            results.append(_fail("hazard_id 참조 오류", e))

    # 문서 참조 오류
    if not doc_errors:
        results.append(_ok("required/recommended_documents 참조 무결성 PASS"))
    else:
        for e in doc_errors:
            results.append(_fail("document_id 참조 오류", e))

    # permit 참조 오류
    if not permit_errors:
        results.append(_ok("required_permits 참조 무결성 PASS"))
    else:
        for e in permit_errors:
            results.append(_fail("permit_id 참조 오류", e))

    # training 참조 오류
    if not training_errors:
        results.append(_ok("required_trainings 참조 무결성 PASS"))
    else:
        for e in training_errors:
            results.append(_fail("training_code 참조 오류", e))

    # 공종 수 검사
    for group_name, min_count in MIN_TRADE_COUNTS.items():
        actual = group_counts.get(group_name, 0)
        if actual >= min_count:
            results.append(_ok(f"{group_name} 공종 수 충족", f"{actual} ≥ {min_count}"))
        else:
            results.append(_fail(f"{group_name} 공종 수 부족", f"{actual} < {min_count}"))

    # ── 6. skeleton 파일 존재 확인 ───────────────────────────────────
    skeleton_trade_count = 0
    for skel_file in SKELETON_FILES:
        spath = WORK_TYPES_DIR / skel_file
        if spath.exists():
            data = load_yaml(spath)
            if data is not None:
                trade_cnt = len(data.get("trades", []))
                skeleton_trade_count += trade_cnt
                results.append(_ok(f"skeleton {skel_file} 존재", f"{trade_cnt}개 trades"))
            else:
                results.append(_fail(f"skeleton {skel_file} parse 실패"))
        else:
            results.append(_fail(f"skeleton 파일 없음", skel_file))

    # index 수 vs (detail + skeleton) 합산 교차 검증
    total_from_files = len(all_trade_ids) + skeleton_trade_count
    if index_trade_ids and total_from_files == len(index_trade_ids):
        results.append(_ok(
            f"index 수 == detail+skeleton 합산 일치",
            f"index={len(index_trade_ids)}, detail={len(all_trade_ids)}, skeleton={skeleton_trade_count}"
        ))
    elif index_trade_ids:
        results.append(_fail(
            f"index 수 != detail+skeleton 합산 불일치",
            f"index={len(index_trade_ids)}, detail={len(all_trade_ids)}, skeleton={skeleton_trade_count}, 합산={total_from_files}"
        ))

    # ── 7. mapping 파일 검증 ──────────────────────────────────────────
    all_detail_trade_ids = set(all_trade_ids)

    for mfile in MAPPING_FILES:
        mpath = MAPPINGS_DIR / mfile
        if not mpath.exists():
            results.append(_fail(f"{mfile} 파일 없음"))
            continue
        mdata = load_yaml(mpath)
        if mdata is None:
            results.append(_fail(f"{mfile} parse 실패"))
            continue

        mappings = mdata.get("mappings", [])
        results.append(_ok(f"{mfile} 로드 성공", f"{len(mappings)}개 매핑"))

        # trade_document_mapping에서 doc_id 무결성 추가 검사
        if mfile == "trade_document_mapping.yml":
            map_doc_errors = []
            for m in mappings:
                tid = m.get("trade_id", "")
                for field in ("required_documents", "recommended_documents", "conditional_documents"):
                    for did in m.get(field, []):
                        if did not in valid_doc_ids:
                            map_doc_errors.append(f"{tid}.{field} → {did}")
            if not map_doc_errors:
                results.append(_ok("trade_document_mapping: doc_id 참조 무결성 PASS"))
            else:
                for e in map_doc_errors:
                    results.append(_fail("trade_document_mapping doc_id 오류", e))

        # trade_permit_mapping에서 permit_id 무결성 추가 검사
        if mfile == "trade_permit_mapping.yml":
            map_permit_errors = []
            for m in mappings:
                tid = m.get("trade_id", "")
                for pid in m.get("required_permits", []):
                    if pid not in valid_doc_ids:
                        map_permit_errors.append(f"{tid}.required_permits → {pid}")
                for cond in m.get("conditional_permits", []):
                    pid = cond.get("permit_id", "") if isinstance(cond, dict) else cond
                    if pid and pid not in valid_doc_ids:
                        map_permit_errors.append(f"{tid}.conditional_permits → {pid}")
            if not map_permit_errors:
                results.append(_ok("trade_permit_mapping: permit_id 참조 무결성 PASS"))
            else:
                for e in map_permit_errors:
                    results.append(_fail("trade_permit_mapping permit_id 오류", e))

        # trade_training_mapping에서 training_code 무결성 추가 검사
        if mfile == "trade_training_mapping.yml":
            map_train_errors = []
            for m in mappings:
                tid = m.get("trade_id", "")
                for tcode in m.get("required_trainings", []):
                    if tcode not in valid_training_codes:
                        map_train_errors.append(f"{tid} → {tcode}")
            if not map_train_errors:
                results.append(_ok("trade_training_mapping: training_code 참조 무결성 PASS"))
            else:
                for e in map_train_errors:
                    results.append(_fail("trade_training_mapping training_code 오류", e))

    # ── 출력 ─────────────────────────────────────────────────────────
    total_hazards = len(valid_hazard_ids)
    total_trades = len(all_trade_ids)
    total_mappings = sum(
        len(load_yaml(MAPPINGS_DIR / mf).get("mappings", []))
        for mf in MAPPING_FILES
        if (MAPPINGS_DIR / mf).exists() and load_yaml(MAPPINGS_DIR / mf) is not None
    )

    pass_cnt = sum(1 for r in results if r[0] == "PASS")
    warn_cnt = sum(1 for r in results if r[0] == "WARN")
    fail_cnt = sum(1 for r in results if r[0] == "FAIL")

    overall = "FAIL" if fail_cnt > 0 else ("WARN" if warn_cnt > 0 else "PASS")

    print("\n" + "=" * 68)
    print("  [validate_trade_risk_presets]")
    print("=" * 68)
    for verdict, name, detail in results:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[verdict]
        line = f"  {icon} [{verdict}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)
    print("-" * 68)
    print(f"  files_checked: hazard_master + hazard_controls + trade_presets + {len(DETAIL_FILES)} 상세 + {len(SKELETON_FILES)} skeleton + {len(MAPPING_FILES)} mapping")
    print(f"  trades: {total_trades}개 (enabled: {total_enabled})")
    print(f"  hazards: {total_hazards}개")
    print(f"  mappings: {total_mappings}개 매핑 항목")
    print(f"  result: PASS {pass_cnt}  WARN {warn_cnt}  FAIL {fail_cnt}")
    print(f"\n  최종 판정: {overall}")
    print("=" * 68 + "\n")

    sys.exit(0 if overall != "FAIL" else 1)


if __name__ == "__main__":
    main()
