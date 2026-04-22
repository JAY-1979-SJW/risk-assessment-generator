"""
expc raw JSONL → normalized JSON 변환기

입력: data/raw/law_content/expc/*/expc_content.jsonl  (expc_content.py 출력)
출력: data/normalized/expc/expc_{id}.json
매핑: data/risk_db/mapping/*.json

각 JSONL 레코드는 expc_content.py의 _make_record() 출력 스키마를 따른다.
content_raw = "[질의요지]\n...\n\n[회답]\n...\n\n[이유]\n..." 형식.
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
        logging.FileHandler(LOG_DIR / "expc_normalizer.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

RAW_DIR = ROOT / "data" / "raw" / "law_content" / "expc"
OUT_DIR = ROOT / "data" / "normalized" / "expc"
MAP_DIR = ROOT / "data" / "risk_db" / "mapping"

_TITLE_STRIP = re.compile(
    r"^[^-]+-\s*"          # "고용노동부 - " 형식 기관명 접두어
    r"|「[^」]*」\s*"        # 「법령명」 인용 제거 (선택적)
    r"|◆|▶|■|▷|●|○|※"
)
_WHITESPACE = re.compile(r"\s+")
_SECTION_RE = re.compile(
    r"\[질의요지\](.*?)(?=\[회답\]|\[이유\]|$)",
    re.DOTALL,
)
_ANSWER_RE  = re.compile(r"\[회답\](.*?)(?=\[이유\]|$)", re.DOTALL)
_REASON_RE  = re.compile(r"\[이유\](.*?)$", re.DOTALL)


class ExpcNormalizer:
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
        t = _TITLE_STRIP.sub("", title).strip()
        t = _WHITESPACE.sub(" ", t).strip()
        return t

    # ── 본문 정제 ────────────────────────────────────────────────────────────

    def normalize_body(self, text: str) -> str:
        if not text:
            return ""
        t = re.sub(r"\n{3,}", "\n\n", text)
        return t.strip()[:8000]

    # ── 질의/회답/이유 분리 ──────────────────────────────────────────────────

    def extract_question_answer_reason(self, content_raw: str) -> tuple[str, str, str]:
        q_m = _SECTION_RE.search(content_raw)
        a_m = _ANSWER_RE.search(content_raw)
        r_m = _REASON_RE.search(content_raw)
        question = q_m.group(1).strip() if q_m else ""
        answer   = a_m.group(1).strip() if a_m else ""
        reason   = r_m.group(1).strip() if r_m else ""
        return question, answer, reason

    # ── expc 메타 추출 ───────────────────────────────────────────────────────

    def extract_expc_meta(self, record: dict, question: str, answer: str, reason: str) -> dict:
        title = record.get("title", "")
        agenda_no = record.get("raw_id", "")

        # 안건번호는 인덱스에서 case_no 또는 raw_id로 넘어옴
        # 질의요지 요약: 첫 100자
        q_summary = question[:100].replace("\n", " ") if question else ""
        a_summary = answer[:100].replace("\n", " ")   if answer   else ""

        return {
            "agenda_no":        agenda_no,
            "agency_question":  record.get("ministry", ""),
            "agency_answer":    "법제처",
            "reply_date":       record.get("published_at", ""),
            "question_summary": q_summary,
            "answer_summary":   a_summary,
            "reason_text":      reason[:500] if reason else "",
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
        title       = record.get("title", "")
        content_raw = record.get("content_raw") or ""
        body_text   = self.normalize_body(content_raw)

        question, answer, reason = self.extract_question_answer_reason(content_raw)
        expc_meta = self.extract_expc_meta(record, question, answer, reason)

        analysis_text = title + " " + body_text
        hazards    = self.map_hazards(analysis_text)
        work_types = self.map_work_types(analysis_text)

        return {
            "source":           "expc",
            "doc_category":     "law_expc",
            "source_id":        record.get("doc_id", ""),
            "title":            title,
            "title_normalized": self.normalize_title(title),
            "body_text":        body_text,
            "has_text":         bool(body_text),
            "content_length":   len(body_text),
            "hazards":          hazards,
            "work_types":       work_types,
            "equipment":        self.map_equipment(analysis_text),
            "tags":             [],
            "collected_at":     record.get("collected_at", ""),
            "extra":            expc_meta,
            "status":           "mapped" if (hazards or work_types) else "normalized",
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
        jsonl_files = sorted(RAW_DIR.glob("*/expc_content.jsonl"))
        if not jsonl_files:
            log.warning(f"JSONL 파일 없음: {RAW_DIR}")
            return False

        log.info(f"=== expc 정규화 시작 | JSONL 파일: {len(jsonl_files)}개 ===")

        total = h_cnt = wt_cnt = eq_cnt = fail_cnt = 0

        for path in jsonl_files:
            log.info(f"처리 중: {path}")
            records = self.process_file(path)
            for r in records:
                total += 1
                if r["hazards"]:    h_cnt  += 1
                if r["work_types"]: wt_cnt += 1
                if r["equipment"]:  eq_cnt += 1
            if not records:
                fail_cnt += 1

        self._report(total, h_cnt, wt_cnt, eq_cnt, fail_cnt)
        return total > 0

    def _report(self, total: int, h: int, wt: int, eq: int, fail: int) -> None:
        h_r  = h  / total * 100 if total else 0
        wt_r = wt / total * 100 if total else 0
        eq_r = eq / total * 100 if total else 0
        h_v  = "PASS" if h_r  >= 70 else "WARN"
        wt_v = "PASS" if wt_r >= 50 else "WARN"
        overall = "PASS" if h_v == "PASS" and wt_v == "PASS" else "WARN"

        lines = [
            "=" * 52,
            f"총 처리 건수    : {total} (실패 파일: {fail})",
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


def _sample_test() -> None:
    """expc 인덱스 3건으로 process_record() 단위 검증."""
    index_path = ROOT / "data" / "raw" / "law_api" / "expc" / "2026-04-21" / "expc_index.json"
    if not index_path.exists():
        print("[WARN] 인덱스 파일 없음, 샘플 테스트 생략")
        return

    items = json.loads(index_path.read_text(encoding="utf-8")).get("items", [])[:3]
    if not items:
        print("[WARN] 인덱스 항목 없음")
        return

    norm = ExpcNormalizer()
    print("\n" + "=" * 52)
    print("expc_normalizer 샘플 테스트 (3건)")
    print("=" * 52)

    pass_cnt = 0
    for i, item in enumerate(items, 1):
        expc_id = item.get("법령해석례일련번호", "")
        title   = item.get("안건명", "")
        # 인덱스 기반 mock — 실제 본문 없이 제목 키워드로 매핑 테스트
        mock_content = (
            "[질의요지]\n"
            "산업안전보건법에 따라 비계 조립 작업 시 추락 방지를 위한 안전대 설치 의무가 있는지 여부.\n\n"
            "[회답]\n"
            "고소작업 중 추락, 낙하물에 의한 위험이 있으므로 안전대와 낙하물방지망을 설치하여야 한다.\n\n"
            "[이유]\n"
            "산업안전보건기준에 관한 규칙 제43조에 따라 비계 작업 시 추락 방지 조치를 하여야 한다."
        )
        mock = {
            "doc_id":       f"expc_{expc_id}",
            "source_type":  "expc",
            "title":        title,
            "content_raw":  mock_content,
            "has_text":     True,
            "raw_id":       expc_id,
            "law_type":     "expc",
            "ministry":     item.get("질의기관명", ""),
            "published_at": item.get("회신일자", ""),
            "collected_at": "2026-04-21",
        }
        result = norm.process_record(mock)
        q, a, r = norm.extract_question_answer_reason(mock_content)

        ok = bool(result["hazards"] or result["work_types"])
        status = "PASS" if ok else "WARN"
        if ok:
            pass_cnt += 1

        print(f"\n[{i}] {title[:60]}")
        print(f"  title_normalized  : {result['title_normalized'][:55]}")
        print(f"  hazards           : {result['hazards']}")
        print(f"  work_types        : {result['work_types']}")
        print(f"  equipment         : {result['equipment']}")
        print(f"  extra.agenda_no   : {result['extra']['agenda_no']}")
        print(f"  extra.reply_date  : {result['extra']['reply_date']}")
        print(f"  extra.q_summary   : {result['extra']['question_summary'][:50]}")
        print(f"  → {status}")

    overall = "PASS" if pass_cnt >= 2 else "WARN"
    print(f"\n샘플 결과: {pass_cnt}/3 매핑 성공 → 전체 {overall}")
    print("=" * 52 + "\n")


def run() -> bool:
    return ExpcNormalizer().run()


if __name__ == "__main__":
    if "--sample" in sys.argv:
        _sample_test()
        sys.exit(0)
    sys.exit(0 if run() else 1)
