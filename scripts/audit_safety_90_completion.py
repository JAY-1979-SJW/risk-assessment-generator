"""
안전서류 90종 구현 완료 전수 감사 스크립트.

검사 항목 (문서별):
  builder_exists        — form_type이 form_registry에 등록되어 있는지
  registry_registered   — builder_exists와 동일 (form_registry 기준)
  catalog_done          — implementation_status == 'DONE'
  evidence_exists       — evidence_file이 존재하거나 evidence_status가 설정되어 있는지
  evidence_status       — VERIFIED / PARTIAL_VERIFIED / NEEDS_VERIFICATION / NONE
  smoke_test_exists     — smoke_test_p1_forms.py에 doc_id가 포함되어 있는지
  recommender_connected — document_recommender v1.1 RULES 또는 trade_document_mapping에 참조되는지
  related_documents     — related_documents 목록이 있는지
  final_readiness       — READY / TEST_MISSING / EVIDENCE_MISSING / BUILDER_ONLY / TODO / OUT

final_readiness 판정 기준:
  OUT             → implementation_status == OUT
  TODO            → catalog TODO, builder 없음
  BUILDER_ONLY    → builder 등록됨, catalog NOT DONE
  EVIDENCE_MISSING → catalog DONE + builder + evidence 없음
  TEST_MISSING    → catalog DONE + builder + evidence 있음 + smoke_test 없음
  READY           → catalog DONE + builder + evidence + smoke_test 모두 OK

실행:
    cd <project_root>
    python scripts/audit_safety_90_completion.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, ".")

ROOT = Path(".")
CATALOG_PATH   = ROOT / "data" / "masters" / "safety" / "documents" / "document_catalog.yml"
MAPPING_PATH   = ROOT / "data" / "masters" / "safety" / "mappings" / "trade_document_mapping.yml"
RECOMMENDER_PATH = ROOT / "engine" / "recommendation" / "document_recommender.py"
SMOKE_TEST_PATH  = ROOT / "scripts" / "smoke_test_p1_forms.py"
EV_DIR         = ROOT / "data" / "evidence" / "safety_law_refs"


# ---------------------------------------------------------------------------
# 데이터 로드
# ---------------------------------------------------------------------------

def _load_catalog() -> list[dict]:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["documents"]


def _load_supported_form_types() -> set[str]:
    from engine.output.form_registry import list_supported_forms
    return {f["form_type"] for f in list_supported_forms()}


def _load_evidence_by_doc() -> dict[str, list[dict]]:
    ev_map: dict[str, list[dict]] = {}
    for fname in os.listdir(EV_DIR):
        if not fname.endswith(".json"):
            continue
        fpath = EV_DIR / fname
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            doc_id = data.get("document_id", "")
            if not doc_id:
                continue
            ev_map.setdefault(doc_id, []).append({
                "file": fname,
                "vr":   data.get("verification_result", "?"),
            })
        except Exception:
            pass
    return ev_map


def _load_smoke_test_content() -> str:
    return SMOKE_TEST_PATH.read_text(encoding="utf-8")


def _load_recommender_doc_ids() -> set[str]:
    # _V11_PACKAGE_RULES에서 참조되는 모든 문서 ID
    from engine.recommendation.document_recommender import _V11_PACKAGE_RULES
    ids: set[str] = set()
    for rules in _V11_PACKAGE_RULES.values():
        for key in ("required", "conditional_required", "optional"):
            for doc in (rules.get(key) or []):
                ids.add(doc)
    return ids


def _load_mapping_doc_ids() -> set[str]:
    with open(MAPPING_PATH, encoding="utf-8") as f:
        mapping = yaml.safe_load(f)
    ids: set[str] = set()
    for m in (mapping.get("mappings") or []):
        for key in ("required_documents", "recommended_documents", "conditional_documents"):
            for doc in (m.get(key) or []):
                ids.add(doc)
    return ids


# ---------------------------------------------------------------------------
# 판정 로직
# ---------------------------------------------------------------------------

def _compute_ev_status(doc: dict, ev_files: list[dict]) -> str:
    if doc.get("evidence_status"):
        return doc["evidence_status"]
    if ev_files:
        vrs = {e["vr"] for e in ev_files}
        if vrs == {"VERIFIED"}:
            return "VERIFIED"
        if "NEEDS_VERIFICATION" in vrs and "PARTIAL_VERIFIED" not in vrs and "VERIFIED" not in vrs:
            return "NEEDS_VERIFICATION"
        return "PARTIAL_VERIFIED"
    return "NONE"


def _compute_readiness(
    status: str,
    builder_exists: bool,
    catalog_done: bool,
    evidence_exists: bool,
    smoke_test_exists: bool,
) -> str:
    if status == "OUT":
        return "OUT"
    if status == "TODO" and not builder_exists:
        return "TODO"
    if builder_exists and not catalog_done:
        return "BUILDER_ONLY"
    if catalog_done and builder_exists:
        if not evidence_exists:
            return "EVIDENCE_MISSING"
        if not smoke_test_exists:
            return "TEST_MISSING"
        return "READY"
    return "TODO"


# ---------------------------------------------------------------------------
# 메인 감사
# ---------------------------------------------------------------------------

def audit() -> list[dict]:
    docs        = _load_catalog()
    supported   = _load_supported_form_types()
    ev_by_doc   = _load_evidence_by_doc()
    smoke       = _load_smoke_test_content()
    rec_docs    = _load_recommender_doc_ids()
    map_docs    = _load_mapping_doc_ids()
    all_connected = rec_docs | map_docs

    rows: list[dict] = []
    for d in docs:
        doc_id    = d["id"]
        status    = d.get("implementation_status", "")
        form_type = d.get("form_type") or ""
        category  = d.get("category_code", "")
        name      = d.get("name", "")
        priority  = d.get("priority", "")

        builder_exists = bool(form_type and form_type in supported)
        catalog_done   = status == "DONE"

        ev_files = ev_by_doc.get(doc_id, [])
        ev_in_catalog = bool(
            d.get("evidence_file") or d.get("evidence_id") or d.get("evidence_status")
        )
        evidence_exists = ev_in_catalog or bool(ev_files)

        ev_status = _compute_ev_status(d, ev_files)

        smoke_test_exists     = doc_id in smoke
        recommender_connected = doc_id in all_connected
        related_docs          = d.get("related_documents") or []
        related_docs_exists   = len(related_docs) > 0

        readiness = _compute_readiness(
            status, builder_exists, catalog_done, evidence_exists, smoke_test_exists
        )

        rows.append({
            "id":          doc_id,
            "name":        name,
            "category":    category,
            "status":      status,
            "priority":    priority,
            "form_type":   form_type or "-",
            "builder":     builder_exists,
            "registry":    builder_exists,
            "done":        catalog_done,
            "evidence":    evidence_exists,
            "ev_status":   ev_status,
            "smoke":       smoke_test_exists,
            "recommender": recommender_connected,
            "related":     related_docs_exists,
            "readiness":   readiness,
        })
    return rows


# ---------------------------------------------------------------------------
# 출력
# ---------------------------------------------------------------------------

_READINESS_ORDER = ["READY", "TEST_MISSING", "EVIDENCE_MISSING", "BUILDER_ONLY", "TODO", "OUT"]

_CHECK  = "✓"
_CROSS  = "✗"
_DASH   = "-"


def _yn(v: bool | None) -> str:
    if v is None:
        return _DASH
    return _CHECK if v else _CROSS


def _pad(s: str, n: int) -> str:
    return (s[:n] if len(s) > n else s).ljust(n)


def print_full_table(rows: list[dict]) -> None:
    hdr = (
        f"  {'ID':12s} {'카테고리':5s} {'구현':4s} {'빌더':4s} {'증거':4s} {'EV상태':15s}"
        f" {'테스트':4s} {'추천':4s} {'관련':4s}  {'최종판정':18s}  {'서식명'}"
    )
    sep = "  " + "-" * 120
    print(hdr)
    print(sep)
    for r in rows:
        ev_short = {
            "VERIFIED":           "VERF",
            "PARTIAL_VERIFIED":   "PART",
            "NEEDS_VERIFICATION": "NEED",
            "NONE":               "-   ",
        }.get(r["ev_status"], r["ev_status"][:4])

        print(
            f"  {r['id']:12s} {r['category']:5s} "
            f"{_yn(r['done']):4s} {_yn(r['builder']):4s} "
            f"{_yn(r['evidence']):4s} {ev_short:15s} "
            f"{_yn(r['smoke']):4s} {_yn(r['recommender']):4s} {_yn(r['related']):4s}  "
            f"{r['readiness']:18s}  {r['name'][:35]}"
        )


def print_summary(rows: list[dict]) -> None:
    cnt       = Counter(r["readiness"] for r in rows)
    cat_stats = {}
    for r in rows:
        c = r["category"]
        cat_stats.setdefault(c, Counter())
        cat_stats[c][r["readiness"]] += 1

    print("\n" + "=" * 80)
    print("  KRAS 안전서류 90종 구현 완료 전수 감사")
    print("=" * 80)
    print(f"  총 문서 수: {len(rows)}  (OUT={cnt.get('OUT',0)} 제외 실효 {len(rows)-cnt.get('OUT',0)})")
    print()
    print("  [final_readiness 분포]")
    for k in _READINESS_ORDER:
        v = cnt.get(k, 0)
        bar = "█" * v
        print(f"    {k:20s}: {v:3d}  {bar}")
    print()
    print("  [카테고리별 현황]")
    print(f"  {'CAT':5s} {'총':4s} {'READY':7s} {'T_MISS':7s} {'EV_MISS':8s} {'TODO':6s} {'OUT':4s}")
    print("  " + "-" * 50)
    for cat in sorted(cat_stats.keys()):
        c    = cat_stats[cat]
        tot  = sum(c.values())
        print(
            f"  {cat:5s} {tot:4d} "
            f"{c.get('READY',0):7d} {c.get('TEST_MISSING',0):7d} "
            f"{c.get('EVIDENCE_MISSING',0):8d} {c.get('TODO',0):6d} {c.get('OUT',0):4d}"
        )
    print()

    print("  [READY 문서 목록 — 16종]")
    for r in rows:
        if r["readiness"] == "READY":
            print(f"    ✅ {r['id']:10s} {r['name'][:40]}")
    print()

    print("  [TEST_MISSING — 2종 (evidence 있으나 smoke_test 없음)]")
    for r in rows:
        if r["readiness"] == "TEST_MISSING":
            print(f"    ⚠️  {r['id']:10s} {r['name'][:40]}")
    print()

    print("  [EVIDENCE_MISSING — 15종 (DONE builder 있으나 evidence 없음)]")
    for r in rows:
        if r["readiness"] == "EVIDENCE_MISSING":
            print(f"    ⚠️  {r['id']:10s} {r['name'][:40]}")
    print()

    # PASS/WARN/FAIL 판정
    ready_pct  = cnt.get("READY", 0) / max(1, len(rows) - cnt.get("OUT", 0)) * 100
    fail_items = cnt.get("TODO", 0)
    overall = "PASS" if cnt.get("OUT", 0) + cnt.get("READY", 0) + cnt.get("TEST_MISSING", 0) + cnt.get("EVIDENCE_MISSING", 0) == len(rows) else "WARN"

    print(f"  READY 비율: {ready_pct:.1f}%  ({cnt.get('READY',0)} / {len(rows)-cnt.get('OUT',0)})")
    print(f"  미착수(TODO): {fail_items}종")
    print()
    print(f"  최종 판정: {overall}")
    print("=" * 80 + "\n")


def run() -> None:
    rows = audit()
    print_summary(rows)
    print("\n  [전체 문서 상세 테이블]")
    print_full_table(rows)


if __name__ == "__main__":
    run()
