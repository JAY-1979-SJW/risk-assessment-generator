"""
통합 인덱스 생성기

입력: data/normalized/{kosha,law,expc}/*.json
출력: data/index/unified_index.jsonl

각 레코드:
  source / title / body_text / hazards / work_types / equipment / score_weight
"""
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

LOG_DIR = ROOT / "logs" / "search"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "build_index.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

NORM_DIR = ROOT / "data" / "normalized"
INDEX_DIR = ROOT / "data" / "index"

# source별 score_weight
WEIGHTS: dict[str, float] = {
    "kosha": 1.0,
    "expc":  1.2,
    "law":   0.8,
}


def _make_record(doc: dict, source: str) -> dict:
    return {
        "source":       source,
        "source_id":    doc.get("source_id", ""),
        "doc_category": doc.get("doc_category", ""),
        "title":        doc.get("title_normalized") or doc.get("title", ""),
        "body_text":    (doc.get("body_text") or "")[:2000],  # 검색용 truncate
        "has_text":     doc.get("has_text", False),
        "hazards":      doc.get("hazards", []),
        "work_types":   doc.get("work_types", []),
        "equipment":    doc.get("equipment", []),
        "score_weight": WEIGHTS.get(source, 1.0),
        "status":       doc.get("status", ""),
    }


def build(sources: list[str] | None = None) -> int:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    out_path = INDEX_DIR / "unified_index.jsonl"

    targets = sources or ["kosha", "law", "expc"]
    total = 0
    skipped = 0

    log.info(f"=== 통합 인덱스 생성 시작 | 대상: {targets} ===")

    with out_path.open("w", encoding="utf-8") as fout:
        for source in targets:
            src_dir = NORM_DIR / source
            files = sorted(src_dir.glob("*.json"))
            cnt = 0
            for path in files:
                try:
                    doc = json.loads(path.read_text(encoding="utf-8"))
                except Exception as e:
                    log.warning(f"읽기 실패 [{path.name}]: {e}")
                    skipped += 1
                    continue

                # body_text 없는 문서는 제외 (검색 가치 없음)
                if not doc.get("has_text") and not doc.get("hazards") and not doc.get("work_types"):
                    skipped += 1
                    continue

                record = _make_record(doc, source)
                fout.write(json.dumps(record, ensure_ascii=False) + "\n")
                cnt += 1

            log.info(f"  {source:6s}: {cnt}건 추가 (weight={WEIGHTS.get(source, 1.0)})")
            total += cnt

    log.info(f"=== 완료 | 총 {total}건 저장 | 제외 {skipped}건 | {out_path} ===")
    print(f"\n총 {total}건 → {out_path}\n제외(본문無+미매핑): {skipped}건")
    return total


def run() -> bool:
    return build() > 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
