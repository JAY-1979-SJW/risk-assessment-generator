# V1.1 Stage 2B-5C — 패키지 ZIP 생성 서비스.
#
# 명시 실행 only. 다운로드 endpoint / StreamingResponse / FileResponse 미사용.
# generated_document_files 의 file_path 들을 zip 으로 묶어
# generated_document_packages.zip_file_path 에 저장한다.

from __future__ import annotations

import logging
import os
import re
import zipfile
from collections import Counter
from pathlib import Path

from repositories import new_construction_repository as repo

_logger = logging.getLogger(__name__)

_DEFAULT_BASE_DIR = "/tmp/risk_assessment_generated_documents"
_FILENAME_SAFE_RE = re.compile(r"[^0-9A-Za-z가-힣._-]+")


def _base_dir() -> Path:
    raw = os.getenv("GENERATED_DOCUMENTS_DIR") or _DEFAULT_BASE_DIR
    return Path(raw).resolve()


def _safe_name(name: str) -> str:
    name = (name or "document").strip()
    name = name.replace("\\", "_").replace("/", "_").replace("..", "_")
    name = _FILENAME_SAFE_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("._-") or "document"
    if len(name) > 80:
        name = name[:80]
    return name


def _resolve_zip_path(project_id: int, package_id: int) -> Path:
    base = _base_dir()
    out_dir = (base / f"project_{int(project_id)}" / f"package_{int(package_id)}").resolve()
    try:
        out_dir.relative_to(base)
    except ValueError:
        raise RuntimeError("invalid zip output directory")
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"package_{int(package_id)}.zip"


def _entry_name(display_name: str | None, file_id: int, used: Counter[str]) -> str:
    base = _safe_name(display_name or f"file_{file_id}")
    candidate = f"{base}.xlsx"
    if used[candidate] == 0:
        used[candidate] += 1
        return candidate
    used[candidate] += 1
    return f"{int(file_id)}_{base}.xlsx"


def build_zip(package_id: int) -> tuple[dict | None, str | None]:
    """returns (response_dict, err).

    err in {None, 'package_not_found', 'invalid_status', 'no_files',
            'files_not_ready', 'file_missing'}.
    invalid_status / files_not_ready / file_missing 시 response_dict 에 상세를 담는다.
    실패 시 package.status 는 변경하지 않는다 (호출자/운영 판단으로 분리).
    """
    pkg = repo.get_document_package(package_id)
    if pkg is None:
        return None, "package_not_found"
    if pkg["status"] not in ("ready", "created"):
        return {"package_id": package_id, "status": pkg["status"]}, "invalid_status"

    files = repo.list_files_for_package(package_id)
    if not files:
        return None, "no_files"

    not_ready = [f["id"] for f in files if f.get("status") != "ready"]
    if not_ready:
        return {
            "package_id": package_id,
            "status": pkg["status"],
            "not_ready_file_ids": not_ready,
        }, "files_not_ready"

    missing: list[dict] = []
    resolved: list[tuple[Path, str, dict]] = []
    used: Counter[str] = Counter()
    for f in files:
        path_s = f.get("file_path")
        if not path_s:
            missing.append({"file_id": f["id"], "reason": "no_file_path"})
            continue
        p = Path(path_s)
        if not p.is_file():
            missing.append({"file_id": f["id"], "reason": "file_not_found", "file_path": path_s})
            continue
        arc = _entry_name(f.get("display_name"), f["id"], used)
        resolved.append((p, arc, f))

    if missing:
        return {
            "package_id": package_id,
            "status": pkg["status"],
            "missing": missing,
        }, "file_missing"

    zip_path = _resolve_zip_path(pkg["project_id"], package_id)
    tmp_path = zip_path.with_suffix(zip_path.suffix + ".tmp")
    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for src, arc, _f in resolved:
                zf.write(src, arcname=arc)
        os.replace(tmp_path, zip_path)
    except Exception:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:  # noqa: BLE001
            pass
        raise

    zip_size = zip_path.stat().st_size

    repo.update_document_package_zip_ready(
        package_id=package_id,
        zip_file_path=str(zip_path),
        storage_key=None,
    )

    return {
        "package_id": package_id,
        "project_id": pkg["project_id"],
        "status": "ready",
        "file_count": len(resolved),
        "zip_file_path": str(zip_path),
        "zip_file_size": zip_size,
    }, None
