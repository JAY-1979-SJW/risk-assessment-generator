"""
KOSHA raw JSON → normalized JSON 변환기

입력: data/raw/kosha/*.json
출력: data/normalized/kosha/*.json
매핑: data/risk_db/mapping/*.json
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
        logging.FileHandler(LOG_DIR / "kosha_normalizer.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

RAW_DIR    = ROOT / "data" / "raw" / "kosha"
OUT_DIR    = ROOT / "data" / "normalized" / "kosha"
MAP_DIR    = ROOT / "data" / "risk_db" / "mapping"

# 제목 정규화 — 제거 패턴
_TITLE_STRIP = re.compile(
    r"\[.*?\]"           # [중대재해_건설업] 등 대괄호 전체
    r"|\(KOSHA[^)]*\)"   # (KOSHA GUIDE ...) 등
    r"|\(개정[^)]*\)"    # (개정 YYYY-MM-DD)
    r"|◆|▶|■|▷|●|○|※"  # 특수 불릿 문자
)
_WHITESPACE = re.compile(r"\s+")


class KoshaNormalizer:
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
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get(key, [])

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

    # ── 키워드 매핑 ──────────────────────────────────────────────────────────

    def _match(self, text: str, entries: list[dict], code_key: str) -> list[str]:
        matched = []
        for entry in entries:
            code = entry.get(code_key, "")
            for kw in entry.get("keywords", []):
                if kw in text:
                    matched.append(code)
                    break
        return matched

    def map_hazards(self, text: str) -> list[str]:
        return self._match(text, self.hazards, "hazard_code")

    def map_work_types(self, text: str) -> list[str]:
        return self._match(text, self.work_types, "work_type_code")

    def map_equipment(self, text: str) -> list[str]:
        return self._match(text, self.equipment, "equipment_code")

    # ── 단일 파일 처리 ───────────────────────────────────────────────────────

    def process_file(self, path: Path) -> dict | None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"읽기 실패 [{path.name}]: {e}")
            return None

        title   = raw.get("title", "")
        content = raw.get("content", "")

        # 분석 대상 텍스트 = 제목 + 본문
        analysis_text = title + " " + content

        normalized = {
            "source":           raw.get("source", "kosha"),
            "source_type":      "portal_api",
            "doc_category":     raw.get("category") or raw.get("doc_category", ""),
            "source_id":        raw.get("item_id", ""),
            "title":            title,
            "title_normalized": self.normalize_title(title),
            "body_text":        content,
            "has_text":         raw.get("has_text", False),
            "content_length":   len(content),
            "hazards":          self.map_hazards(analysis_text),
            "work_types":       self.map_work_types(analysis_text),
            "equipment":        self.map_equipment(analysis_text),
            "tags":             [],
            "url":              raw.get("url") or raw.get("download_url", ""),
            "file_url":         raw.get("file_url") or raw.get("download_url", ""),
            "pdf_path":         raw.get("pdf_path", ""),
            "file_sha256":      raw.get("file_sha256", ""),
            "industry":         raw.get("industry", ""),
            "published_at":     raw.get("reg_date", ""),
            "collected_at":     raw.get("collected_at", ""),
            "language":         "ko",
            "status":           "mapped" if (self.map_hazards(analysis_text) or self.map_work_types(analysis_text)) else "normalized",
        }

        return normalized

    # ── 전체 실행 ────────────────────────────────────────────────────────────

    def run(self) -> bool:
        raw_files = sorted(RAW_DIR.glob("kosha_*.json"))
        if not raw_files:
            log.warning(f"raw 파일 없음: {RAW_DIR}")
            return False

        log.info(f"=== KOSHA 정규화 시작 | 대상: {len(raw_files)}건 ===")

        total = 0
        h_cnt = wt_cnt = eq_cnt = fail_cnt = 0

        for path in raw_files:
            result = self.process_file(path)
            if result is None:
                fail_cnt += 1
                continue

            out_path = OUT_DIR / path.name
            try:
                out_path.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception as e:
                log.warning(f"저장 실패 [{path.name}]: {e}")
                fail_cnt += 1
                continue

            total += 1
            if result["hazards"]:
                h_cnt += 1
            if result["work_types"]:
                wt_cnt += 1
            if result["equipment"]:
                eq_cnt += 1

        self._report(total, h_cnt, wt_cnt, eq_cnt, fail_cnt)
        return total > 0

    def _report(self, total: int, h: int, wt: int, eq: int, fail: int) -> None:
        h_r  = h  / total * 100 if total else 0
        wt_r = wt / total * 100 if total else 0
        eq_r = eq / total * 100 if total else 0

        h_v  = "PASS" if h_r  >= 80 else "WARN"
        wt_v = "PASS" if wt_r >= 70 else "WARN"
        overall = "PASS" if h_v == "PASS" and wt_v == "PASS" else "WARN"

        lines = [
            "=" * 52,
            f"총 처리 건수    : {total} (실패: {fail})",
            f"hazard 매핑     : {h}/{total} ({h_r:.1f}%) [{h_v}]",
            f"work_type 매핑  : {wt}/{total} ({wt_r:.1f}%) [{wt_v}]",
            f"equipment 매핑  : {eq}/{total} ({eq_r:.1f}%)",
            f"검증 결과       : {overall}",
            f"저장 경로       : {OUT_DIR}",
            "=" * 52,
        ]
        for ln in lines:
            log.info(ln)
        print("\n" + "\n".join(lines) + "\n")


def run() -> bool:
    return KoshaNormalizer().run()


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
