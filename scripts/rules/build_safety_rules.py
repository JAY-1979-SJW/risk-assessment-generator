"""
safety_rules.json 빌드 스크립트.
raw_sources/*.json 에서 데이터를 읽어 규칙 통계를 출력하고,
중복 rule_id 및 필수 필드 누락을 검사한다.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES_FILE = ROOT / "data/risk_db/rules/safety_rules.json"
RAW_DIR = ROOT / "data/risk_db/raw_sources"


def load_rules() -> dict:
    with open(RULES_FILE, encoding="utf-8") as f:
        return json.load(f)


def check_required_fields(rules: list[dict]) -> list[str]:
    required = [
        "rule_id", "rule_type", "subject_type", "subject_code",
        "condition_expr", "obligation", "obligation_type",
        "source_type", "source_ref", "priority", "needs_review",
    ]
    errors = []
    for r in rules:
        for field in required:
            if field not in r:
                errors.append(f"[{r.get('rule_id', '?')}] 필드 누락: {field}")
    return errors


def check_duplicate_ids(rules: list[dict]) -> list[str]:
    ids = [r["rule_id"] for r in rules]
    counts = Counter(ids)
    return [f"중복 rule_id: {rid} ({cnt}회)" for rid, cnt in counts.items() if cnt > 1]


def print_stats(rules: list[dict]) -> None:
    print(f"\n총 rule 수: {len(rules)}")

    type_dist = Counter(r["rule_type"] for r in rules)
    print("\n[rule_type 분포]")
    for k, v in sorted(type_dist.items()):
        print(f"  {k}: {v}")

    subject_dist = Counter(r["subject_code"] for r in rules)
    print("\n[subject_code 분포 (상위 15)]")
    for k, v in subject_dist.most_common(15):
        print(f"  {k}: {v}")

    needs_review = sum(1 for r in rules if r.get("needs_review"))
    pct = needs_review / len(rules) * 100 if rules else 0
    print(f"\nneeds_review: {needs_review}건 ({pct:.1f}%)")

    priority_dist = Counter(r["priority"] for r in rules)
    print("\n[priority 분포]")
    labels = {1: "law", 2: "admrul", 3: "kosha", 4: "manual"}
    for p in sorted(priority_dist):
        print(f"  {p} ({labels.get(p,'?')}): {priority_dist[p]}")

    source_dist = Counter(r["source_type"] for r in rules)
    print("\n[source_type 분포]")
    for k, v in sorted(source_dist.items()):
        print(f"  {k}: {v}")


def check_raw_sources() -> None:
    files = list(RAW_DIR.glob("*.json"))
    print(f"\n[raw_sources] {len(files)}개 파일")
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        entry_count = len(data.get("entries", []))
        print(f"  {f.name}: {entry_count}건")


def main() -> int:
    print("=" * 50)
    print("safety_rules.json 빌드 검사")
    print("=" * 50)

    data = load_rules()
    rules = data.get("rules", [])

    errors: list[str] = []
    errors += check_required_fields(rules)
    errors += check_duplicate_ids(rules)

    if errors:
        print("\n[오류]")
        for e in errors:
            print(f"  [X] {e}")
    else:
        print("\n[검증] 필수 필드 및 중복 ID 이상 없음 OK")

    print_stats(rules)
    check_raw_sources()

    print("\n" + "=" * 50)
    if errors:
        print(f"FAIL — {len(errors)}건 오류")
        return 1
    print("PASS — 규칙 DB 정상")
    return 0


if __name__ == "__main__":
    sys.exit(main())
