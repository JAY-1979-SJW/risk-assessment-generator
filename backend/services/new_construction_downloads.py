# V1.1 Stage 2B-5D — 패키지 ZIP 다운로드 path safety helper.
#
# DB 에 저장된 zip_file_path 를 그대로 신뢰하지 않고
# GENERATED_DOCUMENTS_DIR 하위인지·`.zip` 인지·실제 파일인지 검증한다.
# ZIP 생성/Excel builder 실행/status 변경 금지.

from __future__ import annotations

import os
import re
from pathlib import Path

_DEFAULT_BASE_DIR = "/tmp/risk_assessment_generated_documents"
_FILENAME_SAFE_RE = re.compile(r"[^0-9A-Za-z가-힣._-]+")


def base_dir() -> Path:
    raw = os.getenv("GENERATED_DOCUMENTS_DIR") or _DEFAULT_BASE_DIR
    return Path(raw).resolve()


def safe_download_filename(package_id: int, package_name: str | None) -> str:
    raw = (package_name or "").strip()
    if raw:
        cleaned = raw.replace("\\", "_").replace("/", "_").replace("..", "_")
        cleaned = _FILENAME_SAFE_RE.sub("_", cleaned)
        cleaned = re.sub(r"_+", "_", cleaned).strip("._-")
        if cleaned:
            if len(cleaned) > 80:
                cleaned = cleaned[:80]
            return f"{cleaned}.zip"
    return f"package_{int(package_id)}.zip"


def resolve_zip_path(zip_file_path: str | None) -> tuple[Path | None, str | None]:
    """returns (resolved_path, err).

    err in {None, 'zip_not_built', 'unsafe_path', 'zip_file_missing'}.
    - zip_not_built: DB 에 zip_file_path 없음
    - unsafe_path: base_dir 외부, `..` 포함, .zip 아님 등
    - zip_file_missing: 경로는 안전하지만 디스크에 파일 없음
    """
    if not zip_file_path:
        return None, "zip_not_built"
    raw_str = str(zip_file_path)
    if ".." in raw_str.replace("\\", "/").split("/"):
        return None, "unsafe_path"
    try:
        candidate = Path(raw_str).resolve()
    except (OSError, RuntimeError):
        return None, "unsafe_path"
    base = base_dir()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None, "unsafe_path"
    if candidate.suffix.lower() != ".zip":
        return None, "unsafe_path"
    if not candidate.is_file():
        return None, "zip_file_missing"
    return candidate, None
