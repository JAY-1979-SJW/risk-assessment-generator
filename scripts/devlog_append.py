"""
단계 완료 시 _index.jsonl에 1줄 append하는 보조 스크립트.

사용법:
    python scripts/devlog_append.py

입력 프롬프트에 값을 입력하면 docs/devlog/_index.jsonl에 append.
commit_hash는 커밋 직후 실행하면 자동으로 HEAD에서 읽음.
"""
import json
import subprocess
from datetime import date
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parents[1] / "docs" / "devlog" / "_index.jsonl"


def _git_head_short() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return "pending"


def _prompt(label: str, default: str = "") -> str:
    val = input(f"  {label} [{default}]: ").strip()
    return val if val else default


def main():
    print("=== devlog index append ===")
    print(f"→ {INDEX_PATH}\n")

    today = date.today().isoformat()
    head = _git_head_short()

    entry = {
        "date": _prompt("date", today),
        "step": int(_prompt("step", "0")),
        "title": _prompt("title"),
        "result": _prompt("result (PASS/WARN/FAIL)", "PASS"),
        "devlog_path": _prompt("devlog_path", f"docs/devlog/{today}_<slug>.md"),
        "commit_hash": _prompt("commit_hash", head),
        "tests_summary": _prompt("tests_summary", "N passed, M skipped"),
        "files_changed_count": int(_prompt("files_changed_count", "0")),
        "protected_files_changed": _prompt("protected_files_changed (true/false)", "false").lower() == "true",
        "notes": _prompt("notes", ""),
    }

    line = json.dumps(entry, ensure_ascii=False)
    with open(INDEX_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    print(f"\n✓ appended to {INDEX_PATH}")
    print(f"  {line}")


if __name__ == "__main__":
    main()
