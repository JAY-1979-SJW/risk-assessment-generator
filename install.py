# -*- coding: utf-8 -*-
"""
위험성평가표 자동생성기 설치 스크립트
- 바탕화면 바로가기 생성
- 시작 메뉴 바로가기 생성
"""
import os
import sys
import winreg
import shutil

def get_desktop_path():
    """바탕화면 경로 가져오기"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            return winreg.QueryValueEx(key, "Desktop")[0]
    except:
        return os.path.join(os.path.expanduser("~"), "Desktop")

def get_start_menu_path():
    """시작 메뉴 프로그램 경로 가져오기"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
            return winreg.QueryValueEx(key, "Programs")[0]
    except:
        return os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs")

def create_shortcut(target_path, shortcut_path, icon_path=None, description=""):
    """Windows 바로가기 생성 (PowerShell 사용)"""
    # PowerShell 스크립트로 바로가기 생성
    ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.WorkingDirectory = "{os.path.dirname(target_path)}"
$Shortcut.Description = "{description}"
'''
    if icon_path:
        ps_script += f'$Shortcut.IconLocation = "{icon_path}"\n'
    ps_script += '$Shortcut.Save()'

    # PowerShell 실행
    import subprocess
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    return result.returncode == 0

def main():
    print("=" * 50)
    print("위험성평가표 자동생성기 설치")
    print("=" * 50)

    # 현재 스크립트 위치
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # exe 파일 경로
    exe_path = os.path.join(script_dir, "dist", "위험성평가표 자동생성기.exe")
    icon_path = os.path.join(script_dir, "app_icon.ico")

    if not os.path.exists(exe_path):
        print(f"오류: exe 파일을 찾을 수 없습니다: {exe_path}")
        return False

    print(f"exe 파일 위치: {exe_path}")

    # 프로그램 설치 폴더 생성
    install_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "위험성평가표 자동생성기")
    os.makedirs(install_dir, exist_ok=True)

    # exe 파일 복사
    installed_exe = os.path.join(install_dir, "위험성평가표 자동생성기.exe")
    installed_icon = os.path.join(install_dir, "app_icon.ico")

    print(f"\n프로그램 설치 중: {install_dir}")
    shutil.copy2(exe_path, installed_exe)
    if os.path.exists(icon_path):
        shutil.copy2(icon_path, installed_icon)

    print("프로그램 파일 복사 완료!")

    # 바탕화면 바로가기 생성
    desktop_path = get_desktop_path()
    desktop_shortcut = os.path.join(desktop_path, "위험성평가표 자동생성기.lnk")

    print(f"\n바탕화면 바로가기 생성 중...")
    if create_shortcut(installed_exe, desktop_shortcut, installed_icon, "KRAS 표준 위험성평가표 자동생성기"):
        print(f"바탕화면 바로가기 생성 완료: {desktop_shortcut}")
    else:
        print("바탕화면 바로가기 생성 실패")

    # 시작 메뉴 바로가기 생성
    start_menu_path = get_start_menu_path()
    program_folder = os.path.join(start_menu_path, "위험성평가표 자동생성기")
    os.makedirs(program_folder, exist_ok=True)

    start_shortcut = os.path.join(program_folder, "위험성평가표 자동생성기.lnk")

    print(f"\n시작 메뉴 바로가기 생성 중...")
    if create_shortcut(installed_exe, start_shortcut, installed_icon, "KRAS 표준 위험성평가표 자동생성기"):
        print(f"시작 메뉴 바로가기 생성 완료: {start_shortcut}")
    else:
        print("시작 메뉴 바로가기 생성 실패")

    print("\n" + "=" * 50)
    print("설치 완료!")
    print("=" * 50)
    print(f"\n설치 위치: {install_dir}")
    print("\n사용 방법:")
    print("1. 바탕화면의 '위험성평가표 자동생성기' 아이콘을 더블클릭")
    print("2. 또는 시작 메뉴에서 '위험성평가표 자동생성기' 검색")
    print("\n작업 표시줄에 고정하려면:")
    print("바탕화면 아이콘을 우클릭 → '작업 표시줄에 고정' 선택")

    return True

if __name__ == "__main__":
    try:
        success = main()
        input("\n아무 키나 눌러 종료...")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        input("\n아무 키나 눌러 종료...")
