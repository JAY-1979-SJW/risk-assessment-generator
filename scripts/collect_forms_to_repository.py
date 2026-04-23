"""
서식 권위 뷰 구축 스크립트

docs/standards/form_repository_layout.md의 규칙에 따라
원본 수집본을 data/forms/A|B|C/ 권위 뷰로 복사·재명명하고
source_map.csv를 생성한다.

- 원본은 건드리지 않는다 (read-only).
- 재명명 규칙: {source}__{doc_type}__{title_slug}__{date}.{ext}
- 모든 결정은 화이트리스트(키워드) 기반이며, 스크립트 실행 결과만으로
  권위 등급을 확정하지 않는다 (Step 4에서 확정).
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
RAW_LICBYL = ROOT / "data" / "raw" / "law_api" / "licbyl" / "files"
RAW_MOEL = ROOT / "data" / "raw" / "moel_forms" / "policy_data" / "files"
RAW_KOSHA_FILES = ROOT / "scraper" / "kosha_files"
REF_DIR = ROOT / "참조자료"
EXPORT_DIR = ROOT / "export"

FORMS_ROOT = ROOT / "data" / "forms"
SRC_MAP = FORMS_ROOT / "source_map.csv"
LOG = ROOT / "docs" / "standards" / "form_collection_log.md"

TARGET_EXTS = {".hwp", ".hwpx", ".pdf", ".docx", ".xlsx", ".xls"}


# --------------------------------------------------------------------- helpers

def slugify(title: str, max_tokens: int = 8) -> str:
    """공백→_, 특수문자 제거, 한글/영문/숫자 주요 단어만 유지."""
    # 괄호·따옴표 등 제거
    t = re.sub(r"[\[\]\(\)【】〔〕「」『』\"'“”‘’《》<>]", " ", title)
    # 보이지 않는 URL 인코딩 잔재 제거
    t = re.sub(r"%[0-9A-Fa-f]{2}", "", t)
    # ㆍ, ·, /, \, ㆍ, ¸ → _
    t = re.sub(r"[ㆍ·・/\\,、、、¸★☆◈◆◇]", "_", t)
    # 공백 계열 → _
    t = re.sub(r"\s+", "_", t.strip())
    # 한글/영문/숫자/언더스코어 외 제거
    t = re.sub(r"[^0-9A-Za-z가-힣_\-]", "", t)
    # 연속 _ 압축
    t = re.sub(r"_+", "_", t).strip("_")
    if not t:
        return "untitled"
    # 토큰 상한
    parts = t.split("_")
    if len(parts) > max_tokens:
        parts = parts[:max_tokens]
    return "_".join(parts)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return  # 같은 파일명 이미 존재 — 중복 처리는 호출측에서 suffix 부여
    shutil.copy2(src, dst)


def is_uri_encoded_residue(name: str) -> bool:
    """licbyl 파일 중 일부는 URL-인코딩 원본이 잔존 (파일명 앞부분이 % 로 시작)."""
    return name.startswith("%") or "%E" in name[:10]


# -------------------------------------------------------------- classification

RISK_KEYS = ("위험성평가",)
CHECKLIST_KEYS = ("점검표", "자율점검표", "자율안전점검표")
GUIDE_KEYS = ("안내서", "가이드", "활용가이드")
MODEL_KEYS = ("표준모델", "표준안")
PLAN_KEYS = ("작업계획서", "계획서")
MEETING_KEYS = ("회의록", "TBM", "티비엠")
EDU_KEYS = ("교육일지", "교육회람")
REG_KEYS = ("표준실시규정", "실시규정")
BYLAW_KEYS = ("별지", "별표")
EXCLUDE_KEYS = (
    "개정법률", "시행령 일부개정", "시행규칙 일부개정",  # 법 개정문 자체
    "공고문", "옴부즈만",  # 공고·조직 발표문
)


def doc_type_of_moel(name: str) -> str | None:
    """MOEL 파일명 → doc_type 판정. 서식성 아니면 None (진입 제외)."""
    if any(k in name for k in EXCLUDE_KEYS):
        return None
    if any(k in name for k in CHECKLIST_KEYS):
        return "자율점검표"
    if any(k in name for k in MODEL_KEYS):
        return "표준모델"
    if any(k in name for k in GUIDE_KEYS) and any(k in name for k in RISK_KEYS + ("중소기업",)):
        return "안내서"
    if any(k in name for k in GUIDE_KEYS):
        return "가이드"
    if any(k in name for k in RISK_KEYS):
        return "표준모델"  # 위험성평가 관련 서식성
    if any(k in name for k in BYLAW_KEYS) and ("서식" in name or "시행규칙" in name):
        return "별지"
    if any(k in name for k in PLAN_KEYS):
        return "계획서"
    if any(k in name for k in MEETING_KEYS):
        return "TBM"
    if any(k in name for k in EDU_KEYS):
        return "교육"
    if any(k in name for k in REG_KEYS):
        return "규정"
    if "중대재해" in name and "서식" in name:
        return "안내서"
    return None


def target_dir_for_moel(doc_type: str) -> Path:
    mapping = {
        "자율점검표": FORMS_ROOT / "B_semi_official" / "moel_checklist",
        "안내서": FORMS_ROOT / "B_semi_official" / "moel_guide",
        "가이드": FORMS_ROOT / "B_semi_official" / "moel_guide",
        "표준모델": FORMS_ROOT / "B_semi_official" / "moel_model",
        "별지": FORMS_ROOT / "A_official" / "licbyl",  # MOEL 재배포본
        "계획서": FORMS_ROOT / "B_semi_official" / "moel_guide",
        "TBM": FORMS_ROOT / "B_semi_official" / "moel_guide",
        "교육": FORMS_ROOT / "B_semi_official" / "moel_guide",
        "규정": FORMS_ROOT / "A_official" / "regulation",
    }
    return mapping[doc_type]


# ------------------------------------------------------------------- records

@dataclass
class MappingRow:
    view_path: str
    source_path: str
    source_url: str
    source_code: str
    source_id: str
    doc_type: str
    doc_title: str
    date: str
    ext: str
    authority_grade: str
    is_original: str
    checksum_sha256: str
    size_bytes: int
    notes: str = ""


@dataclass
class LogEntry:
    path: Path
    action: str  # copied / skipped / failed
    reason: str = ""


# ------------------------------------------------------------ licbyl (Group A)

def process_licbyl() -> tuple[list[MappingRow], list[LogEntry]]:
    rows: list[MappingRow] = []
    log: list[LogEntry] = []
    if not RAW_LICBYL.exists():
        log.append(LogEntry(RAW_LICBYL, "skipped", "디렉토리 없음"))
        return rows, log

    for src in RAW_LICBYL.rglob("*"):
        if not src.is_file():
            continue
        if src.suffix.lower() not in TARGET_EXTS:
            continue
        name = src.name
        if is_uri_encoded_residue(name):
            log.append(LogEntry(src, "skipped", "파일명 URL 인코딩 잔재"))
            continue

        # 제목/번호 파싱 — "[별지 제19호서식] 유해위험방지계획서 …"
        title = src.stem
        m = re.match(r"\[(별지|별표)\s*([^]\]]+)\]\s*(.+)", title)
        if m:
            bylaw_type, number, rest = m.groups()
            doc_type = bylaw_type  # 별지/별표
            title_clean = rest.strip()
            number_slug = slugify(number, max_tokens=4)
            title_slug = slugify(title_clean, max_tokens=6)
            new_stem = f"LAW__{doc_type}__{title_slug}_{number_slug}__N_A"
        else:
            doc_type = "기타"
            title_slug = slugify(title, max_tokens=8)
            new_stem = f"LAW__{doc_type}__{title_slug}__N_A"

        new_name = f"{new_stem}{src.suffix.lower()}"
        dst = FORMS_ROOT / "A_official" / "licbyl" / new_name

        i = 1
        while dst.exists() and sha256_of(dst) != sha256_of(src):
            dst = FORMS_ROOT / "A_official" / "licbyl" / f"{new_stem}__dup{i}{src.suffix.lower()}"
            i += 1
        if dst.exists():
            log.append(LogEntry(src, "skipped", f"동일 해시 기존 {dst.name}"))
            continue

        try:
            safe_copy(src, dst)
        except Exception as e:  # noqa: BLE001
            log.append(LogEntry(src, "failed", f"{e.__class__.__name__}: {e}"))
            continue

        rows.append(MappingRow(
            view_path=str(dst.relative_to(ROOT)).replace("\\", "/"),
            source_path=str(src.relative_to(ROOT)).replace("\\", "/"),
            source_url="",  # licbyl rename_map.json 후처리로 채움
            source_code="LAW",
            source_id=src.parent.name,
            doc_type=doc_type,
            doc_title=title,
            date="N/A",
            ext=src.suffix.lower().lstrip("."),
            authority_grade="A",
            is_original="Y",
            checksum_sha256=sha256_of(src),
            size_bytes=src.stat().st_size,
            notes="산안법 시행규칙 별지/별표 원본",
        ))
        log.append(LogEntry(src, "copied", dst.name))

    return rows, log


# -------------------------------------------------------------- moel (Group B)

def process_moel() -> tuple[list[MappingRow], list[LogEntry]]:
    rows: list[MappingRow] = []
    log: list[LogEntry] = []
    if not RAW_MOEL.exists():
        log.append(LogEntry(RAW_MOEL, "skipped", "디렉토리 없음"))
        return rows, log

    for src in RAW_MOEL.rglob("*"):
        if not src.is_file():
            continue
        if src.suffix.lower() not in TARGET_EXTS:
            continue
        name = src.name
        doc_type = doc_type_of_moel(name)
        if doc_type is None:
            log.append(LogEntry(src, "skipped", "서식성 키워드 미포함"))
            continue

        title = src.stem
        # 앞머리 날짜 추출 (YYMMDD / YYYYMMDD / 230918 / 220310 등)
        date_match = re.match(r"^(\d{6,8})[\s_\-.]", title)
        if date_match:
            d = date_match.group(1)
            if len(d) == 6:
                date = f"20{d[:2]}{d[2:4]}{d[4:6]}"  # YY→20YY
            elif len(d) == 8:
                date = d
            else:
                date = "N_A"
            title_body = title[len(d):].lstrip(" _-.")
        else:
            date = "N_A"
            title_body = title

        title_slug = slugify(title_body, max_tokens=8)
        new_stem = f"MOEL__{doc_type}__{title_slug}__{date}"
        new_name = f"{new_stem}{src.suffix.lower()}"

        target = target_dir_for_moel(doc_type)
        dst = target / new_name

        i = 1
        while dst.exists() and sha256_of(dst) != sha256_of(src):
            dst = target / f"{new_stem}__dup{i}{src.suffix.lower()}"
            i += 1
        if dst.exists():
            log.append(LogEntry(src, "skipped", f"동일 해시 기존 {dst.name}"))
            continue

        try:
            safe_copy(src, dst)
        except Exception as e:  # noqa: BLE001
            log.append(LogEntry(src, "failed", f"{e.__class__.__name__}: {e}"))
            continue

        authority = "A" if doc_type in ("별지", "규정") else "B"

        rows.append(MappingRow(
            view_path=str(dst.relative_to(ROOT)).replace("\\", "/"),
            source_path=str(src.relative_to(ROOT)).replace("\\", "/"),
            source_url="",
            source_code="MOEL",
            source_id=src.parent.name,
            doc_type=doc_type,
            doc_title=title,
            date=date.replace("N_A", "N/A"),
            ext=src.suffix.lower().lstrip("."),
            authority_grade=authority,
            is_original="Y" if doc_type != "별지" else "N",
            checksum_sha256=sha256_of(src),
            size_bytes=src.stat().st_size,
            notes="MOEL 정책자료실 배포본",
        ))
        log.append(LogEntry(src, "copied", dst.name))

    return rows, log


# ----------------------------------------------------------- internal files

INTERNAL_RULES: list[tuple[Path, str, str, str, str]] = [
    # (src, doc_type, dst_subdir, authority, notes)
    (REF_DIR / "위험성평가 표준안(경비).xls", "표준안",
     "A_official/kras", "A", "KRAS 17컬럼 원형 (경비업)"),
    (REF_DIR / "표준실시규정.docx", "규정",
     "A_official/regulation", "A", "산안법 제36조 기반 실시규정 표준문서"),
    (EXPORT_DIR / "위험성평가표_공문기반_20250114_v2.xlsx", "본표",
     "B_semi_official/ref_template", "A", "공문기반 16컬럼 본표 v2 — 본 프로젝트 준공식 준거"),
    (EXPORT_DIR / "위험성평가표_공문기반_20250114.xlsx", "본표",
     "C_field_practice/internal_draft", "B", "공문기반 v1 선행본"),
    (EXPORT_DIR / "위험성평가표_표준양식_테스트.xlsx", "본표_축약",
     "C_field_practice/compact", "B", "KRAS 12컬럼 축약형"),
    (EXPORT_DIR / "위험성평가표_최종.xlsx", "테스트",
     "C_field_practice/internal_test", "C", "엔진 출력 테스트"),
    (EXPORT_DIR / "test.xlsx", "테스트",
     "C_field_practice/internal_test", "C", "최소 테스트 파일"),
    (ROOT / "test_output.xlsx", "테스트",
     "C_field_practice/internal_test", "C", "개발 샘플"),
    (ROOT / "test_output_v2.xlsx", "테스트",
     "C_field_practice/internal_test", "C", "개발 샘플"),
    (ROOT / "test_output_final.xlsx", "테스트",
     "C_field_practice/internal_test", "C", "개발 샘플"),
]


def process_internal() -> tuple[list[MappingRow], list[LogEntry]]:
    rows: list[MappingRow] = []
    log: list[LogEntry] = []
    for src, doc_type, sub, authority, notes in INTERNAL_RULES:
        if not src.exists():
            log.append(LogEntry(src, "skipped", "원본 없음"))
            continue
        title = src.stem
        title_slug = slugify(title, max_tokens=8)
        # 파일명에 날짜가 있으면 추출
        date_match = re.search(r"(20\d{6})", title)
        date = date_match.group(1) if date_match else "N_A"
        source_code = "KOSHA" if "경비" in title else ("INTERNAL" if "표준실시규정" not in title else "INTERNAL")
        # 표준실시규정은 공식 규정이므로 INTERNAL 소스에서 채택
        new_stem = f"{source_code}__{doc_type}__{title_slug}__{date}"
        new_name = f"{new_stem}{src.suffix.lower()}"
        dst = FORMS_ROOT / sub / new_name

        if dst.exists() and sha256_of(dst) == sha256_of(src):
            log.append(LogEntry(src, "skipped", "동일 해시 기존"))
            continue
        try:
            safe_copy(src, dst)
        except Exception as e:  # noqa: BLE001
            log.append(LogEntry(src, "failed", f"{e.__class__.__name__}: {e}"))
            continue

        rows.append(MappingRow(
            view_path=str(dst.relative_to(ROOT)).replace("\\", "/"),
            source_path=str(src.relative_to(ROOT)).replace("\\", "/"),
            source_url="",
            source_code=source_code,
            source_id=src.parent.name,
            doc_type=doc_type,
            doc_title=title,
            date=date.replace("N_A", "N/A"),
            ext=src.suffix.lower().lstrip("."),
            authority_grade=authority,
            is_original="Y" if authority == "A" else "N",
            checksum_sha256=sha256_of(src),
            size_bytes=src.stat().st_size,
            notes=notes,
        ))
        log.append(LogEntry(src, "copied", dst.name))
    return rows, log


# ----------------------------------------------------------------- main

def write_source_map(rows: Iterable[MappingRow]) -> None:
    SRC_MAP.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "view_path", "source_path", "source_url", "source_code", "source_id",
        "doc_type", "doc_title", "date", "ext", "authority_grade",
        "is_original", "checksum_sha256", "size_bytes", "notes",
    ]
    with SRC_MAP.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r.__dict__)


def write_log_md(all_logs: list[LogEntry], totals: dict[str, int]) -> None:
    lines = [
        "# 서식 수집 실행 로그 v1",
        "",
        "**실행일**: 2026-04-23",
        "**스크립트**: `scripts/collect_forms_to_repository.py`",
        "**근거**: `docs/standards/form_repository_layout.md`",
        "",
        "## 요약",
        "",
        f"- 복사 성공: **{totals['copied']}**",
        f"- 스킵: **{totals['skipped']}**",
        f"- 실패: **{totals['failed']}**",
        f"- 총 처리 대상: **{totals['total']}**",
        "",
        "## 상세 (최초 500건)",
        "",
        "| # | action | source | detail |",
        "|---|--------|--------|--------|",
    ]
    for i, e in enumerate(all_logs[:500], 1):
        rel = str(e.path).replace(str(ROOT) + "\\", "").replace(str(ROOT) + "/", "").replace("\\", "/")
        detail = e.reason.replace("|", "/")
        lines.append(f"| {i} | {e.action} | `{rel}` | {detail} |")

    if len(all_logs) > 500:
        lines.append("")
        lines.append(f"(이하 {len(all_logs) - 500}건 생략 — `data/forms/source_map.csv` 참조)")

    LOG.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    all_rows: list[MappingRow] = []
    all_logs: list[LogEntry] = []
    for fn in (process_licbyl, process_moel, process_internal):
        rows, log = fn()
        all_rows.extend(rows)
        all_logs.extend(log)

    totals = {
        "copied": sum(1 for e in all_logs if e.action == "copied"),
        "skipped": sum(1 for e in all_logs if e.action == "skipped"),
        "failed": sum(1 for e in all_logs if e.action == "failed"),
        "total": len(all_logs),
    }
    write_source_map(all_rows)
    write_log_md(all_logs, totals)
    print(f"copied={totals['copied']} skipped={totals['skipped']} failed={totals['failed']} total={totals['total']}")
    print(f"source_map: {SRC_MAP}")
    print(f"log: {LOG}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
