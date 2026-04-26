#!/bin/bash
set -euo pipefail

DRY_RUN=true
COMMIT_MESSAGE=""
PUSH_CHANGES=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

print_usage() {
  cat <<EOF
usage: git_publish_local_changes.sh [OPTIONS]

옵션:
  --dry-run              검증만 수행, git add/commit/push 없음 (기본값)
  --commit-message MSG   커밋 메시지 지정 (필수: --push와 함께 사용)
  --push                 검증 후 push까지 수행 (--commit-message 필수)
  --help                 이 메시지 출력

예시:
  # 검증만 수행 (dry-run)
  ./scripts/ops/git_publish_local_changes.sh

  # 검증 후 실제 커밋/푸시 (--commit-message 필수)
  ./scripts/ops/git_publish_local_changes.sh --commit-message "feat: add DL-005 work safety checklist" --push

EOF
}

log_status() {
  echo "[STATUS] $1"
}

log_section() {
  echo ""
  echo "===================================================================="
  echo "[$1]"
  echo "===================================================================="
}

log_pass() {
  echo "  ✓ $1"
}

log_fail() {
  echo "  ✗ $1"
  exit 1
}

log_warn() {
  echo "  ⚠ $1"
}

log_info() {
  echo "  ℹ $1"
}

# 옵션 파싱
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --commit-message)
      COMMIT_MESSAGE="$2"
      DRY_RUN=false
      shift 2
      ;;
    --push)
      PUSH_CHANGES=true
      shift
      ;;
    --help)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      print_usage
      exit 1
      ;;
  esac
done

# git 환경 검증
log_section "STATUS"

cd "$SCRIPT_DIR" || log_fail "작업 디렉토리로 이동 실패"
log_pass "작업 디렉토리: $SCRIPT_DIR"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "UNKNOWN")
[[ "$CURRENT_BRANCH" == "UNKNOWN" ]] && log_fail "현재 브랜치 조회 실패"
log_pass "현재 브랜치: $CURRENT_BRANCH"

[[ "$CURRENT_BRANCH" == "HEAD" ]] && log_fail "detached HEAD 상태 — 정상 브랜치로 전환 필요"

git remote get-url origin >/dev/null 2>&1 || log_fail "git remote 'origin' 없음"
log_pass "git remote origin 존재"

# 검증: --push일 때 --commit-message 필수
if [[ "$PUSH_CHANGES" == "true" ]] && [[ -z "$COMMIT_MESSAGE" ]]; then
  log_fail "--push 옵션 사용 시 --commit-message 필수"
fi

if [[ "$DRY_RUN" == "false" ]] && [[ -z "$COMMIT_MESSAGE" ]]; then
  log_fail "커밋 메시지 없음"
fi

# working tree 상태 확인
log_section "CHANGED FILES"

CHANGED_FILES=$(git status --short | wc -l)
if [[ $CHANGED_FILES -eq 0 ]]; then
  log_info "변경된 파일 없음 — 배포할 내용 없음"
  exit 0
fi

git status --short
log_pass "변경 파일 수: $CHANGED_FILES"

if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  git diff --stat
fi

# 금지 파일 차단
log_section "FORBIDDEN FILE CHECK"

FORBIDDEN_PATTERNS=("\.env" "\.pem" "id_rsa" "secret" "token" "credential" "credentials" "key" "p12" "pfx" "crt" "cert")
FORBIDDEN_FOUND=false

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  if git status --short | grep -iE "$pattern" >/dev/null 2>&1; then
    log_fail "금지된 파일 패턴 감지: $pattern"
  fi
  if git ls-files --others --exclude-standard | grep -iE "$pattern" >/dev/null 2>&1; then
    log_fail "금지된 untracked 파일 패턴 감지: $pattern"
  fi
done

log_pass "금지 파일 패턴 없음"

# 검증 스크립트 실행
log_section "VALIDATION"

VALIDATION_FAILED=false

# lint_safety_naming.py
if [[ -f "scripts/lint_safety_naming.py" ]]; then
  log_info "실행: python scripts/lint_safety_naming.py"
  if python scripts/lint_safety_naming.py >/dev/null 2>&1; then
    log_pass "lint_safety_naming.py PASS"
  else
    log_fail "lint_safety_naming.py FAIL"
  fi
else
  log_warn "lint_safety_naming.py 미존재"
fi

# validate_form_registry.py
if [[ -f "scripts/validate_form_registry.py" ]]; then
  log_info "실행: python scripts/validate_form_registry.py"
  if python scripts/validate_form_registry.py >/dev/null 2>&1; then
    log_pass "validate_form_registry.py PASS"
  else
    log_fail "validate_form_registry.py FAIL"
  fi
else
  log_warn "validate_form_registry.py 미존재"
fi

# smoke_test_p1_forms.py
if [[ -f "scripts/smoke_test_p1_forms.py" ]]; then
  log_info "실행: python scripts/smoke_test_p1_forms.py"
  if python scripts/smoke_test_p1_forms.py >/dev/null 2>&1; then
    log_pass "smoke_test_p1_forms.py PASS"
  else
    log_fail "smoke_test_p1_forms.py FAIL"
  fi
else
  log_warn "smoke_test_p1_forms.py 미존재"
fi

# validate_legal_source_registry.py (선택)
if [[ -f "scripts/validate_legal_source_registry.py" ]]; then
  log_info "실행: python scripts/validate_legal_source_registry.py"
  if python scripts/validate_legal_source_registry.py >/dev/null 2>&1; then
    log_pass "validate_legal_source_registry.py PASS"
  else
    log_fail "validate_legal_source_registry.py FAIL"
  fi
else
  log_info "validate_legal_source_registry.py 미존재 (SKIP)"
fi

log_pass "모든 검증 통과"

# Dry-run 종료
if [[ "$DRY_RUN" == "true" ]]; then
  log_section "FINAL"
  log_pass "dry-run 검증 완료"
  log_info "실제 git add/commit/push를 실행하려면:"
  log_info "  ./scripts/ops/git_publish_local_changes.sh --commit-message \"<메시지>\" --push"
  exit 0
fi

# 실제 git 처리
log_section "COMMIT"

if [[ -z "$COMMIT_MESSAGE" ]]; then
  log_fail "커밋 메시지 필수"
fi

log_info "실행: git add -A"
git add -A
log_pass "git add -A 완료"

log_info "실행: git commit -m \"$COMMIT_MESSAGE\""
git commit -m "$COMMIT_MESSAGE"
log_pass "git commit 완료"

# push 처리
if [[ "$PUSH_CHANGES" == "true" ]]; then
  log_section "PUSH"

  log_info "실행: git push origin $CURRENT_BRANCH"
  git push origin "$CURRENT_BRANCH"
  log_pass "git push 완료"

  # push 후 working tree 확인
  TREE_AFTER_PUSH=$(git status --short | wc -l)
  if [[ $TREE_AFTER_PUSH -eq 0 ]]; then
    log_pass "working tree clean 확인"
  else
    log_warn "push 후에도 변경사항 존재 (local branch 선행 상태)"
  fi
fi

log_section "FINAL"
log_pass "배포 완료"
log_info "브랜치: $CURRENT_BRANCH"
log_info "커밋 메시지: $COMMIT_MESSAGE"
if [[ "$PUSH_CHANGES" == "true" ]]; then
  log_info "push 완료"
else
  log_info "push 미실행 (--push 옵션 미사용)"
fi

exit 0
