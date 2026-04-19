# devlog 독립 페이지 구현 및 internal 인증 추가

- 작업일시: 2026-04-19
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (진행중)

## 목표

개발 변경 이력(devlog)을 앱 본 기능과 분리된 별도 페이지에서 확인.
URL 직접 접근(/devlog)으로만 열리고, 메인 앱 메뉴와 강결합 금지.
/internal/* 엔드포인트에 X-Internal-Key 헤더 기반 인증 추가.

## 수정 파일

- docs/devlog/_template.md (신규)
- docs/devlog/2026-04-19-kosha-ai-engine.md (신규 — 샘플)
- logs/change_history.jsonl (기존 항목 유지, 신규 항목 추가)
- backend/main.py (GET /internal/devlog, GET /internal/devlog/{filename}, GET /internal/change-history 추가 + 인증)
- frontend/devlog.html (신규 — 독립 진입점)
- frontend/src/devlog/main.jsx (신규)
- frontend/src/devlog/DevlogPage.jsx (신규 — 뷰어 컴포넌트)
- frontend/vite.config.js (multi-page 빌드 설정)
- frontend/nginx.conf (= /devlog 경로 추가)
- infra/docker-compose.yml (docs/logs 볼륨 마운트, INTERNAL_API_KEY env 추가)
- infra/.env.example (INTERNAL_API_KEY 추가)
- .env (INTERNAL_API_KEY 추가)

## 변경 이유

운영 중 코드 변경 이력을 팀 내부에서 브라우저로 빠르게 확인할 수단이 없었음.
git log는 개발자 전용이므로, 비개발자도 확인 가능한 읽기 전용 페이지 필요.
/internal/* 경로는 외부 노출 시 내부 정보 유출 위험이 있어 키 인증 도입.

## 시도/실패 내용

- react-router-dom 도입 검토 → 기존 App.jsx 수정 필요 → 강결합 문제로 폐기
- Vite multi-page 빌드 채택: index.html(메인) + devlog.html(독립) 분리

## 최종 적용 내용

### devlog 뷰어
- Vite multi-page: `devlog.html` → `frontend/src/devlog/main.jsx` → `DevlogPage.jsx`
- 사이드바 파일 목록 + 본문 마크다운 렌더링 (외부 라이브러리 없이 inline 변환)
- 변경 이력 탭: change_history.jsonl 최근 50건 표시

### 인증
- `_require_internal_key(Security)` 의존성 함수 추가
- `/internal/*` 3개 엔드포인트에 적용
- `INTERNAL_API_KEY` 미설정 시 인증 없이 통과(개발 편의), 설정 시 강제
- 프론트엔드: `apiFetch()` 래퍼로 X-Internal-Key 헤더 자동 전송
- 키를 localStorage에 저장 → 새로고침 후에도 유지
- 401 수신 시 → 화면에 키 입력 폼 노출

## 검증 결과

- backend/main.py 문법 오류 없음 (py_compile 통과)
- /internal/* 3개 엔드포인트에만 [auth] 적용 확인
- vite.config.js multi-page input 설정 확인
- nginx `= /devlog` 경로 추가 확인
- docker-compose INTERNAL_API_KEY, 볼륨 마운트 확인
- 실제 브라우저 동작 확인은 서버 배포 후 진행 예정

## 영향 범위

- 기존 App.jsx 및 메인 앱 기능 무수정
- /health, /trades, /kosha/search, /generate 인증 없이 기존 그대로
- /internal/* 만 인증 적용

## 다음 단계

1. infra/.env에 INTERNAL_API_KEY 실제 키 설정
2. 서버 배포 후 /devlog 직접 접근 테스트
3. 추후 관리자 메뉴에 링크 추가 시 DevlogPage 컴포넌트 재사용
