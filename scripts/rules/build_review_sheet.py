"""72 hit 매핑에 대한 reviewer 정답셋 시트를 생성한다.
- 입력: data/risk_db/master/sentence_control_mapping_sample.csv
- 출력: data/risk_db/master/sentence_control_review_sheet.csv
- reviewer 필드: reviewer_decision / reviewer_control_code / reviewer_note
- confidence 분포 요약 stdout
"""
from __future__ import annotations
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/risk_db/master/sentence_control_mapping_sample.csv"
OUT = ROOT / "data/risk_db/master/sentence_control_review_sheet.csv"

REVIEW_FIELDS = [
    "sample_id",
    "source_type",
    "sentence_type",
    "sentence_text",
    "current_control_code",
    "current_control_name",
    "current_category",
    "current_confidence",
    "reviewer_decision",
    "reviewer_control_code",
    "reviewer_note",
]


def main() -> None:
    rows = []
    with SRC.open("r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    hits = [r for r in rows if r.get("control_type_candidate")]
    dist = Counter(r["confidence"] for r in hits)
    per_cat = Counter(r["control_category_candidate"] for r in hits)
    per_type = Counter(r["control_type_candidate"] for r in hits)

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        w.writeheader()
        for r in hits:
            w.writerow({
                "sample_id": r["sample_id"],
                "source_type": r["source_type"],
                "sentence_type": r["sentence_type"],
                "sentence_text": r["sentence_text"],
                "current_control_code": r["control_type_candidate"],
                "current_control_name": r["control_name_candidate"],
                "current_category": r["control_category_candidate"],
                "current_confidence": r["confidence"],
                "reviewer_decision": "",
                "reviewer_control_code": "",
                "reviewer_note": "",
            })

    print(f"wrote {OUT} · {len(hits)} rows")
    print("confidence:", dict(dist))
    print("category :", dict(per_cat))
    print("type     :", dict(per_type))


if __name__ == "__main__":
    main()
