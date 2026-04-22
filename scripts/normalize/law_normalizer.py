"""
law raw JSONL → normalized JSON 변환기

입력: data/raw/law_content/law/*/law_content.jsonl  (조문 단위, law_content.py 출력)
출력: data/normalized/law/law_{MST}_{seq}.json
매핑: data/risk_db/mapping/*.json

각 JSONL 레코드는 law_content.py의 _make_record() 출력 스키마를 따른다.
"""
import json
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

LOG_DIR = ROOT / "logs" / "normalize"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "law_normalizer.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

RAW_DIR = ROOT / "data" / "raw" / "law_content" / "law"
OUT_DIR = ROOT / "data" / "normalized" / "law"
MAP_DIR = ROOT / "data" / "risk_db" / "mapping"

_TITLE_STRIP = re.compile(
    r"\[.*?\]"
    r"|\(법률\s*제\d+호[^)]*\)"
    r"|【.*?】"
    r"|◆|▶|■|▷|●|○|※"
)
_WHITESPACE = re.compile(r"\s+")
_PAGE_LINE  = re.compile(r"^\d+$", re.MULTILINE)
_RULE_LINE  = re.compile(r"^[─━═\-=]{5,}$", re.MULTILINE)


class LawNormalizer:
    def __init__(self):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        self.hazards    = []
        self.work_types = []
        self.equipment  = []
        self.load_mappings()

    # ── 매핑 사전 로딩 ───────────────────────────────────────────────────────

    def load_mappings(self) -> None:
        def _load(filename: str, key: str) -> list[dict]:
            p = MAP_DIR / filename
            if not p.exists():
                log.warning(f"매핑 파일 없음: {p}")
                return []
            return json.loads(p.read_text(encoding="utf-8")).get(key, [])

        self.hazards    = _load("hazard_keywords.json",    "hazards")
        self.work_types = _load("work_type_keywords.json", "work_types")
        self.equipment  = _load("equipment_keywords.json", "equipment")
        log.info(
            f"매핑 로드 — 위험요인:{len(self.hazards)} "
            f"작업유형:{len(self.work_types)} 장비:{len(self.equipment)}"
        )

    # ── 제목 정규화 ──────────────────────────────────────────────────────────

    def normalize_title(self, title: str) -> str:
        t = _TITLE_STRIP.sub("", title)
        t = _WHITESPACE.sub(" ", t).strip()
        return t

    # ── 본문 정제 ────────────────────────────────────────────────────────────

    def normalize_body(self, text: str) -> str:
        if not text:
            return ""
        t = _PAGE_LINE.sub("", text)
        t = _RULE_LINE.sub("", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()[:8000]

    # ── 법령 메타 추출 ───────────────────────────────────────────────────────

    def extract_law_meta(self, record: dict) -> dict:
        return {
            "law_name":         record.get("title", "").split(" 제")[0].strip(),
            "law_id":           record.get("law_id", "") or record.get("raw_id", ""),
            "article_no":       record.get("article_no", ""),
            "promulgation_date": record.get("published_at", ""),
            "effective_date":   record.get("enforcement_date") or record.get("published_at", ""),
            "ministry":         record.get("ministry", ""),
        }

    # ── 키워드 매핑 ──────────────────────────────────────────────────────────

    def _match(self, text: str, entries: list[dict], code_key: str) -> list[str]:
        matched = []
        for entry in entries:
            for kw in entry.get("keywords", []):
                if kw in text:
                    matched.append(entry[code_key])
                    break
        return matched

    def map_hazards(self, text: str) -> list[str]:
        return self._match(text, self.hazards, "hazard_code")

    def map_work_types(self, text: str) -> list[str]:
        return self._match(text, self.work_types, "work_type_code")

    def map_equipment(self, text: str) -> list[str]:
        return self._match(text, self.equipment, "equipment_code")

    # ── 단일 레코드 처리 ─────────────────────────────────────────────────────

    def process_record(self, record: dict) -> dict:
        title   = record.get("title", "")
        content = self.normalize_body(record.get("content_raw") or "")
        analysis_text = title + " " + content

        law_meta = self.extract_law_meta(record)
        hazards    = self.map_hazards(analysis_text)
        work_types = self.map_work_types(analysis_text)

        return {
            "source":           "law",
            "doc_category":     record.get("law_type", "law_statute"),
            "source_id":        record.get("doc_id", ""),
            "title":            title,
            "title_normalized": self.normalize_title(title),
            "body_text":        content,
            "has_text":         bool(content),
            "content_length":   len(content),
            "hazards":          hazards,
            "work_types":       work_types,
            "equipment":        self.map_equipment(analysis_text),
            "tags":             [],
            "collected_at":     record.get("collected_at", ""),
            "extra": {
                "law_name":         law_meta["law_name"],
                "law_id":           law_meta["law_id"],
                "article_no":       law_meta["article_no"],
                "promulgation_date": law_meta["promulgation_date"],
                "effective_date":   law_meta["effective_date"],
                "ministry":         law_meta["ministry"],
            },
            "status": "mapped" if (hazards or work_types) else "normalized",
        }

    # ── JSONL 파일 처리 ──────────────────────────────────────────────────────

    def process_file(self, path: Path) -> list[dict]:
        results = []
        try:
            lines = path.read_text(encoding="utf-8").strip().splitlines()
        except Exception as e:
            log.warning(f"읽기 실패 [{path.name}]: {e}")
            return []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                log.warning(f"JSON 파싱 실패 [{path.name}]: {e}")
                continue

            normalized = self.process_record(record)
            results.append(normalized)

            out_path = OUT_DIR / f"{normalized['source_id']}.json"
            try:
                out_path.write_text(
                    json.dumps(normalized, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception as e:
                log.warning(f"저장 실패 [{normalized['source_id']}]: {e}")

        return results

    # ── 전체 실행 ────────────────────────────────────────────────────────────

    def run(self) -> bool:
        jsonl_files = sorted(RAW_DIR.glob("*/law_content.jsonl"))
        if not jsonl_files:
            log.warning(f"JSONL 파일 없음: {RAW_DIR}")
            return False

        log.info(f"=== law 정규화 시작 | JSONL 파일: {len(jsonl_files)}개 ===")

        total = h_cnt = wt_cnt = eq_cnt = fail_cnt = 0

        for path in jsonl_files:
            log.info(f"처리 중: {path}")
            records = self.process_file(path)
            for r in records:
                total += 1
                if r["hazards"]:   h_cnt  += 1
                if r["work_types"]: wt_cnt += 1
                if r["equipment"]: eq_cnt += 1
            if not records:
                fail_cnt += 1

        self._report(total, h_cnt, wt_cnt, eq_cnt, fail_cnt)
        return total > 0

    def _report(self, total: int, h: int, wt: int, eq: int, fail: int) -> None:
        h_r  = h  / total * 100 if total else 0
        wt_r = wt / total * 100 if total else 0
        h_v  = "PASS" if h_r  >= 60 else "WARN"
        wt_v = "PASS" if wt_r >= 50 else "WARN"
        overall = "PASS" if h_v == "PASS" and wt_v == "PASS" else "WARN"

        lines = [
            "=" * 52,
            f"총 처리 건수    : {total} (실패 파일: {fail})",
            f"hazard 매핑     : {h}/{total} ({h_r:.1f}%) [{h_v}]",
            f"work_type 매핑  : {wt}/{total} ({wt_r:.1f}%) [{wt_v}]",
            f"equipment 매핑  : {eq}/{total} ({eq_r:.1f}%)" if total else "equipment 매핑  : 0/0",
            f"검증 결과       : {overall}",
            f"저장 경로       : {OUT_DIR}",
            "=" * 52,
        ]
        for ln in lines:
            log.info(ln)
        print("\n" + "\n".join(lines) + "\n")


def _sample_test() -> None:
    """law 인덱스에서 샘플 3건을 구성해 process_record() 단위 검증."""
    index_path = ROOT / "data" / "raw" / "law_api" / "law" / "2026-04-21" / "laws_index.json"
    if not index_path.exists():
        print("[WARN] 인덱스 파일 없음, 샘플 테스트 생략")
        return

    items = json.loads(index_path.read_text(encoding="utf-8")).get("items", [])[:3]
    if not items:
        print("[WARN] 인덱스 항목 없음")
        return

    norm = LawNormalizer()
    print("\n" + "=" * 52)
    print("law_normalizer 샘플 테스트 (3건)")
    print("=" * 52)

    pass_cnt = 0
    for i, item in enumerate(items, 1):
        mst   = item.get("법령일련번호", "")
        title = item.get("법령명한글", "")
        # 인덱스 기반 최소 mock record (본문 없음 — 키워드 매핑 WARN 예상)
        mock = {
            "doc_id":           f"law_{mst}_0000",
            "source_type":      "law",
            "title":            title + " 제1조(목적) 이 법은 산업 안전 및 보건에 관한 기준을 확립하고 추락·낙하·감전 등 산업재해를 예방함을 목적으로 한다.",
            "content_raw":      "근로자의 안전보건을 위하여 비계, 굴착, 용접 작업 시 추락 방지 조치를 하여야 한다.",
            "has_text":         True,
            "law_id":           item.get("법령ID", ""),
            "raw_id":           mst,
            "article_no":       "제1조",
            "law_type":         item.get("법령구분명", ""),
            "ministry":         item.get("소관부처명", ""),
            "enforcement_date": item.get("시행일자", ""),
            "published_at":     item.get("공포일자", ""),
            "collected_at":     "2026-04-21",
        }
        result = norm.process_record(mock)
        ok = bool(result["hazards"] or result["work_types"])
        status = "PASS" if ok else "WARN"
        if ok:
            pass_cnt += 1
        print(f"\n[{i}] {title}")
        print(f"  title_normalized : {result['title_normalized'][:60]}")
        print(f"  hazards          : {result['hazards']}")
        print(f"  work_types       : {result['work_types']}")
        print(f"  equipment        : {result['equipment']}")
        print(f"  extra.ministry   : {result['extra']['ministry']}")
        print(f"  → {status}")

    overall = "PASS" if pass_cnt >= 2 else "WARN"
    print(f"\n샘플 결과: {pass_cnt}/3 매핑 성공 → 전체 {overall}")
    print("=" * 52 + "\n")


def run() -> bool:
    return LawNormalizer().run()


if __name__ == "__main__":
    if "--sample" in sys.argv:
        _sample_test()
        sys.exit(0)
    sys.exit(0 if run() else 1)
