"""
HWP → HWPX MCP 서버.

로컬 Windows + 한컴오피스(한/글) 설치 환경에서 .hwp 파일을 .hwpx 로 변환.
한/글의 COM 자동화 서버(HWPFrame.HwpObject)를 pywin32 로 호출한다.

제공 도구:
    - get_hancom_status()
        한/글 COM 서버 가용 여부 + 버전 문자열 반환.
    - convert_hwp_to_hwpx(src_path, dst_path=None, overwrite=False)
        단일 파일 변환. dst 생략 시 src 와 같은 디렉토리에 확장자만 .hwpx 로.
    - batch_convert_directory(src_dir, dst_dir=None, recursive=False,
                              overwrite=False, limit=0)
        디렉토리 배치 변환. 한 번 실행한 한/글 프로세스를 재사용해 효율화.
    - convert_hwp_from_url(url, dst_path, overwrite=False)
        URL 에서 HWP 를 내려받아 즉시 HWPX 로 변환.

요구사항:
    - Windows (한/글 COM 은 Windows 전용)
    - 한컴오피스 설치 (한/글 2014 이후 권장, HWPX 저장 지원 버전)
    - pip install "mcp>=1.0" pywin32

Claude Desktop / Claude Code 등록 예시 (settings.json 의 mcpServers):
    {
      "mcpServers": {
        "hwp-converter": {
          "command": "python",
          "args": [
            "C:/Users/skyjw/OneDrive/03. PYTHON/15. 위험성평가표 자동생성기/scripts/mcp/hwp_to_hwpx_server.py"
          ]
        }
      }
    }

로컬 수동 테스트(stdio 모드 아님):
    python scripts/mcp/hwp_to_hwpx_server.py --status
    python scripts/mcp/hwp_to_hwpx_server.py --convert "a.hwp"
    python scripts/mcp/hwp_to_hwpx_server.py --batch "data/raw/law_api/licbyl/files" --recursive
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# MCP 프로토콜 로그는 stdout 을 점유하므로, 모든 로그는 stderr 로 보낸다.
logging.basicConfig(
    level=os.environ.get("HWP_MCP_LOGLEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("hwp-to-hwpx")

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    print(
        "ERROR: 'mcp' 패키지가 필요합니다. 설치: pip install \"mcp>=1.0\"",
        file=sys.stderr,
    )
    # CLI 테스트 모드는 mcp 없어도 동작하도록 이후 분기 처리.
    FastMCP = None  # type: ignore

# pywin32 는 Windows 에서만 사용 가능. 다른 OS 에서는 런타임 체크로 안내.
if sys.platform == "win32":
    try:
        import pythoncom  # type: ignore
        import win32com.client  # type: ignore
    except ImportError:
        pythoncom = None  # type: ignore
        win32com = None  # type: ignore
else:
    pythoncom = None  # type: ignore
    win32com = None  # type: ignore


# ---------------------------------------------------------------------------
# 한/글 COM 래퍼
# ---------------------------------------------------------------------------

# 한/글 버전별로 보안 모듈 등록 문자열이 다르다. 가능한 조합을 모두 시도.
_SECURITY_MODULE_PAIRS = [
    ("FilePathCheckDLL", "AutomationModule"),
    ("FilePathCheckDLL", "FilePathCheckerModule"),
    ("FilePathCheckerModule", "FilePathCheckerModule"),
]


def _require_windows() -> str | None:
    if sys.platform != "win32":
        return "이 MCP 는 Windows 전용입니다 (한/글 COM 은 Windows 에서만 제공)."
    if win32com is None or pythoncom is None:
        return "pywin32 가 설치되어 있지 않습니다. `pip install pywin32`"
    return None


class HwpCom:
    """한/글 COM 객체 래퍼. with 블록 또는 명시적 close() 로 종료."""

    def __init__(self, visible: bool = False) -> None:
        err = _require_windows()
        if err:
            raise RuntimeError(err)
        pythoncom.CoInitialize()  # type: ignore
        self._hwp = win32com.client.Dispatch("HWPFrame.HwpObject")  # type: ignore
        # 보안 모듈 등록 — 파일 경로 접근 경고 대화창 우회.
        registered = False
        last_err = None
        for a, b in _SECURITY_MODULE_PAIRS:
            try:
                self._hwp.RegisterModule(a, b)
                registered = True
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                continue
        if not registered:
            log.warning(
                "보안 모듈 등록 실패(파일 경로 대화창이 뜰 수 있음): %r", last_err
            )
        try:
            self._hwp.XHwpWindows.Item(0).Visible = visible  # type: ignore[attr-defined]
        except Exception:
            pass

    # --- 프로퍼티 ----------------------------------------------------------
    @property
    def hwp(self):
        return self._hwp

    @property
    def version(self) -> str:
        try:
            return str(self._hwp.Version)
        except Exception:
            return "unknown"

    # --- 핵심 동작 ---------------------------------------------------------
    def open_document(self, src: Path) -> bool:
        """한/글로 문서 열기. 읽기 쓰기 모두 가능."""
        return bool(
            self._hwp.Open(
                str(src),
                "HWP",
                "forceopen:true;versionwarning:false",
            )
        )

    def save_as_hwpx(self, dst: Path) -> bool:
        """현재 열린 문서를 HWPX 포맷으로 다른 이름으로 저장."""
        # 일부 버전에서는 "HWPX" 문자열 대신 "HWPML2X" 등을 쓰기도 한다.
        for fmt in ("HWPX", "HWPML2X"):
            try:
                if self._hwp.SaveAs(str(dst), fmt, ""):
                    return True
            except Exception as e:
                log.debug("SaveAs(%s) 실패: %r", fmt, e)
                continue
        return False

    def clear(self) -> None:
        try:
            self._hwp.Clear(1)  # 1 = 저장하지 않고 버림
        except Exception:
            pass

    def close(self) -> None:
        try:
            self.clear()
        except Exception:
            pass
        try:
            self._hwp.Quit()
        except Exception:
            pass
        try:
            pythoncom.CoUninitialize()  # type: ignore
        except Exception:
            pass

    def __enter__(self) -> "HwpCom":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()


# ---------------------------------------------------------------------------
# 변환 로직
# ---------------------------------------------------------------------------

_SUPPORTED_SRC_EXT = {".hwp", ".hwpml"}


def _convert_one(hwp: HwpCom, src: Path, dst: Path, *, overwrite: bool) -> dict:
    if not src.exists():
        return {"ok": False, "src": str(src), "error": "source not found"}
    if src.suffix.lower() not in _SUPPORTED_SRC_EXT:
        return {
            "ok": False,
            "src": str(src),
            "error": f"unsupported source extension: {src.suffix}",
        }
    if dst.exists() and not overwrite:
        return {
            "ok": False,
            "src": str(src),
            "dst": str(dst),
            "error": "destination exists; pass overwrite=true",
        }
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not hwp.open_document(src):
        return {"ok": False, "src": str(src), "error": "Open returned False"}

    if not hwp.save_as_hwpx(dst):
        hwp.clear()
        return {"ok": False, "src": str(src), "error": "SaveAs(HWPX) 실패"}

    hwp.clear()
    size = dst.stat().st_size if dst.exists() else 0
    return {
        "ok": True,
        "src": str(src),
        "dst": str(dst),
        "size": size,
    }


def convert_hwp_to_hwpx_impl(
    src_path: str, dst_path: str | None = None, overwrite: bool = False
) -> dict:
    err = _require_windows()
    if err:
        return {"ok": False, "error": err}

    src = Path(src_path).resolve()
    if dst_path is None:
        dst = src.with_suffix(".hwpx")
    else:
        dst = Path(dst_path).resolve()

    with HwpCom() as hwp:
        return _convert_one(hwp, src, dst, overwrite=overwrite)


def batch_convert_directory_impl(
    src_dir: str,
    dst_dir: str | None = None,
    recursive: bool = False,
    overwrite: bool = False,
    limit: int = 0,
) -> dict:
    err = _require_windows()
    if err:
        return {"ok": False, "error": err}

    base = Path(src_dir).resolve()
    if not base.is_dir():
        return {"ok": False, "error": f"not a directory: {base}"}

    pattern = "**/*.hwp" if recursive else "*.hwp"
    src_files = sorted(base.glob(pattern))
    # .hwpml 도 포함
    pattern_ml = "**/*.hwpml" if recursive else "*.hwpml"
    src_files += sorted(base.glob(pattern_ml))
    if limit and limit > 0:
        src_files = src_files[:limit]

    target_base = Path(dst_dir).resolve() if dst_dir else None
    results: list[dict] = []

    with HwpCom() as hwp:
        for src in src_files:
            if target_base is None:
                dst = src.with_suffix(".hwpx")
            else:
                rel = src.relative_to(base)
                dst = target_base / rel.with_suffix(".hwpx")
            results.append(_convert_one(hwp, src, dst, overwrite=overwrite))

    ok_cnt = sum(1 for r in results if r.get("ok"))
    fail_cnt = len(results) - ok_cnt
    return {
        "total": len(results),
        "ok": ok_cnt,
        "fail": fail_cnt,
        "src_dir": str(base),
        "dst_dir": str(target_base) if target_base else None,
        "results": results,
    }


def convert_hwp_from_url_impl(
    url: str, dst_path: str, overwrite: bool = False
) -> dict:
    err = _require_windows()
    if err:
        return {"ok": False, "error": err}
    try:
        import requests  # type: ignore
        import urllib3  # type: ignore
        urllib3.disable_warnings()
    except ImportError:
        return {
            "ok": False,
            "error": "requests 패키지가 필요합니다. `pip install requests`",
        }

    dst = Path(dst_path).resolve()
    if dst.exists() and not overwrite:
        return {
            "ok": False,
            "error": "destination exists; pass overwrite=true",
            "dst": str(dst),
        }

    tmp_dir = Path(tempfile.mkdtemp(prefix="hwp_mcp_"))
    tmp_src = tmp_dir / "input.hwp"
    try:
        r = requests.get(url, timeout=60, verify=False)
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}", "url": url}
        tmp_src.write_bytes(r.content)
        with HwpCom() as hwp:
            return _convert_one(hwp, tmp_src, dst, overwrite=overwrite)
    finally:
        try:
            tmp_src.unlink(missing_ok=True)
            tmp_dir.rmdir()
        except Exception:
            pass


def get_hancom_status_impl() -> dict:
    err = _require_windows()
    if err:
        return {"available": False, "error": err}
    try:
        with HwpCom() as hwp:
            return {"available": True, "version": hwp.version}
    except Exception as e:  # noqa: BLE001
        return {"available": False, "error": repr(e)}


# ---------------------------------------------------------------------------
# MCP 서버
# ---------------------------------------------------------------------------

if FastMCP is not None:
    mcp = FastMCP("hwp-converter")

    @mcp.tool()
    def get_hancom_status() -> dict:
        """Return availability & version of local Hancom 한/글 COM server."""
        return get_hancom_status_impl()

    @mcp.tool()
    def convert_hwp_to_hwpx(
        src_path: str,
        dst_path: str | None = None,
        overwrite: bool = False,
    ) -> dict:
        """Convert a single .hwp file to .hwpx via local Hancom 한/글.

        Args:
            src_path: Absolute path to source .hwp file.
            dst_path: Optional destination .hwpx path. Defaults to src with
                .hwpx suffix in the same directory.
            overwrite: If False and dst exists, returns error. Default False.
        """
        return convert_hwp_to_hwpx_impl(src_path, dst_path, overwrite)

    @mcp.tool()
    def batch_convert_directory(
        src_dir: str,
        dst_dir: str | None = None,
        recursive: bool = False,
        overwrite: bool = False,
        limit: int = 0,
    ) -> dict:
        """Convert every .hwp in a directory to .hwpx.

        Args:
            src_dir: Source directory path.
            dst_dir: Optional destination root; preserves relative subpaths.
                If omitted, each .hwpx is written alongside its source.
            recursive: Recurse into subdirectories. Default False.
            overwrite: Overwrite existing .hwpx files. Default False.
            limit: If > 0, cap number of files processed.
        """
        return batch_convert_directory_impl(
            src_dir, dst_dir, recursive, overwrite, limit
        )

    @mcp.tool()
    def convert_hwp_from_url(
        url: str, dst_path: str, overwrite: bool = False
    ) -> dict:
        """Download an .hwp from a URL and convert to .hwpx locally."""
        return convert_hwp_from_url_impl(url, dst_path, overwrite)


# ---------------------------------------------------------------------------
# CLI (수동 테스트용)
# ---------------------------------------------------------------------------

def _cli(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="HWP → HWPX 로컬 변환 (수동 테스트)",
    )
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="한/글 가용성 확인")
    group.add_argument("--convert", metavar="SRC", help="단일 HWP 변환")
    group.add_argument("--batch", metavar="DIR", help="디렉토리 배치 변환")
    ap.add_argument("--dst", default=None, help="대상 경로 (선택)")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    import json as _json

    if args.status:
        print(_json.dumps(get_hancom_status_impl(), ensure_ascii=False, indent=2))
        return 0
    if args.convert:
        result = convert_hwp_to_hwpx_impl(args.convert, args.dst, args.overwrite)
        print(_json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    if args.batch:
        result = batch_convert_directory_impl(
            args.batch, args.dst, args.recursive, args.overwrite, args.limit
        )
        print(_json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("fail", 0) == 0 else 1
    return 2


def main() -> None:
    # stdio 모드(MCP 프로토콜)가 기본. --status/--convert/--batch 플래그면 CLI 모드.
    if len(sys.argv) > 1 and any(
        a in sys.argv for a in ("--status", "--convert", "--batch", "-h", "--help")
    ):
        sys.exit(_cli(sys.argv[1:]))
    if FastMCP is None:
        print(
            "ERROR: MCP SDK(`mcp`) 미설치 — `pip install \"mcp>=1.0\"`. "
            "또는 --status / --convert / --batch CLI 모드를 사용하세요.",
            file=sys.stderr,
        )
        sys.exit(1)
    log.info("HWP → HWPX MCP 서버 시작 (stdio)")
    mcp.run()


if __name__ == "__main__":
    main()
