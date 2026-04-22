"""
HWP 파일명을 Windows MAX_PATH(260) 이하로 단축 rename.

동기:
    - 일부 파일은 URL 인코딩(%XX)된 채로 저장되어 매우 김 (~200+자).
    - 한글 전체경로가 200자 이상이면 한/글 COM Open()에서 실패.
전략:
    - 대상 디렉토리를 재귀 탐색
    - %XX 가 있으면 먼저 URL 디코딩
    - 여전히 길면 앞 60자 + 해시 8자 + ext 로 단축
    - 원본 → 새 이름 매핑을 JSON 으로 기록
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote


def _safe_print(s: str) -> None:
    """Windows cp949 콘솔에서 인코딩 불가 문자 치환 후 출력."""
    try:
        print(s)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(s.encode(enc, errors="replace").decode(enc, errors="replace"))


def long_path(p: str) -> str:
    r"""Windows MAX_PATH 우회 — \\?\ prefix."""
    if sys.platform != "win32":
        return p
    p = os.path.abspath(p)
    if p.startswith("\\\\?\\"):
        return p
    if p.startswith("\\\\"):
        return "\\\\?\\UNC\\" + p.lstrip("\\")
    return "\\\\?\\" + p


def shorten_name(name: str, *, max_name_bytes: int = 120) -> str:
    # 1) URL 디코딩
    if "%" in name:
        try:
            name = unquote(name)
        except Exception:
            pass
    # 2) 금지문자 치환
    name = re.sub(r"[\\/:*?\"<>|\n\r\t]", "_", name).strip() or "file"
    # 3) 길이 확인 — 바이트 기준
    enc = name.encode("utf-8", errors="ignore")
    if len(enc) <= max_name_bytes:
        return name
    # 4) 단축: stem 앞 60바이트 + "_" + sha8 + ext
    if "." in name:
        stem, ext = name.rsplit(".", 1)
        ext = "." + ext.lower()
    else:
        stem, ext = name, ""
    ext_b = ext.encode("utf-8", errors="ignore")
    head_budget = max_name_bytes - len(ext_b) - 10  # sha 8 + underscore
    head = stem.encode("utf-8", errors="ignore")[:head_budget].decode("utf-8", errors="ignore").rstrip()
    sha = hashlib.sha1(name.encode("utf-8", errors="ignore")).hexdigest()[:8]
    return f"{head}_{sha}{ext}"


def run(target_dir: Path, report_path: Path | None, dry_run: bool) -> int:
    if not target_dir.is_dir():
        print(f"not a directory: {target_dir}", file=sys.stderr)
        return 2

    records: list[dict] = []
    # os.walk 로 long-path rglob 우회 (pathlib rglob 는 내부 stat 이 실패)
    for root, dirs, files in os.walk(long_path(str(target_dir))):
        for name in files:
            if not name.lower().endswith(".hwp"):
                continue
            src_str = os.path.join(root, name)
            parent = os.path.dirname(src_str)
            new_name = shorten_name(name)
            if new_name == name:
                continue
            dst_str = os.path.join(parent, new_name)
            # 충돌 방지
            i = 1
            while os.path.exists(dst_str) and dst_str != src_str:
                if "." in new_name:
                    stem, ext = new_name.rsplit(".", 1)
                    cand = f"{stem}_{i}.{ext}"
                else:
                    cand = f"{new_name}_{i}"
                dst_str = os.path.join(parent, cand)
                i += 1
            rec = {"src": src_str, "dst": dst_str}
            if dry_run:
                _safe_print(f"[DRY] {name[:60]}...\n  -> {new_name}")
            else:
                try:
                    os.rename(src_str, dst_str)
                    _safe_print(f"[OK ] {new_name[:70]}")
                except Exception as e:
                    rec["error"] = repr(e)
                    _safe_print(f"[ERR] {name[:60]}...: {e!r}")
            records.append(rec)

    if report_path and not dry_run:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump({"count": len(records), "entries": records},
                      f, ensure_ascii=False, indent=2)
        print(f"[REPORT] {report_path}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="재귀 처리할 최상위 디렉토리")
    ap.add_argument("--report", default=None, help="매핑 JSON 경로 (선택)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.exit(run(Path(args.target).resolve(), Path(args.report).resolve() if args.report else None, args.dry_run))


if __name__ == "__main__":
    main()
