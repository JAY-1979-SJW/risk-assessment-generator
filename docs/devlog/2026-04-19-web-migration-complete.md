# 2026-04-19 | PyQt6 데스크탑 앱 → 웹 서버 완전 이관

## 작업 요약
데스크탑 앱(PyQt6)을 완전히 웹 서버(FastAPI + React)로 이관하고 서버 배포 완료.

## 작업 내용

### 1. React 프론트엔드 탭 컴포넌트 완성
- `AssessmentTab.jsx` — 위험성평가 항목 테이블
  - AI 자동생성 섹션 (공정명/업종/작업유형 입력 → KOSHA DB + OpenAI)
  - 인라인 편집/삭제, 행 추가
  - 가능성×중대성 → 위험도 자동 계산 (높음/보통/낮음)
- `MeetingTab.jsx` — 회의/교육/협의체 3섹션
  - 각 섹션별 날짜, 장소, 안건, 결과, 후속조치
  - 참석자 인라인 테이블 (부서/직위/성명)
- `CriteriaTab.jsx` — 위험성 기준 참조 (읽기 전용)
  - 위험도 결정 기준표, 가능성/중대성 기준, 3×3 매트릭스

### 2. App.jsx 교체
- 기존: API health 모니터 페이지
- 변경: ProjectList / ProjectDetail 상태 기반 라우팅

### 3. 프론트엔드 빌드 검증
- `npm run build` — 42 modules, 빌드 성공
- 멀티페이지 (index.html + devlog.html) 정상 생성

### 4. 서버 배포
- `git push origin master`
- 앱서버 `git pull --ff-only` + `docker compose up -d`
- kras-db / kras-api / kras-web 3컨테이너 정상 기동

### 5. 서버 .env 생성
- `infra/.env` 없어 kras-db Unhealthy 오류 발생
- `/home/ubuntu/app/secret/openai/ops.env` 에서 OPENAI_API_KEY 확인 후 적용
- DB 비밀번호, INTERNAL_API_KEY 설정 후 재기동 → 정상

### 6. 로컬 backend/.env 생성
- KRAS 전용 로컬 개발 환경변수 파일 신설
- SSH 터널(127.0.0.1:5435) 기준 DATABASE_URL
- .gitignore 패턴(.env)으로 자동 제외 확인

## 완성된 파일 목록
| 파일 | 상태 |
|------|------|
| `frontend/src/pages/tabs/AssessmentTab.jsx` | 신규 |
| `frontend/src/pages/tabs/MeetingTab.jsx` | 신규 |
| `frontend/src/pages/tabs/CriteriaTab.jsx` | 신규 |
| `frontend/src/App.jsx` | 교체 |
| `backend/.env` | 신규 (로컬 전용, git 제외) |
| `infra/.env` (서버) | 서버에 직접 생성 |

## 이슈 및 해결
| 이슈 | 원인 | 해결 |
|------|------|------|
| kras-db Unhealthy | infra/.env 없음 → POSTGRES_PASSWORD 미설정 | 서버에 .env 직접 생성 |
| OPENAI_API_KEY 위치 | 로컬 .env는 G2B 앱용 | `/app/secret/openai/ops.env` 확인 |

## 현재 상태
- **서버**: http://kras.haehan-ai.kr — 정상 서비스 중
- **API**: `GET /api/projects` 응답 확인
- **DB**: kras DB 초기화 완료 (init.sql 적용)
- **데스크탑 앱**: 미사용 (웹으로 완전 대체)

## 남은 작업
- [ ] end-to-end 테스트 (프로젝트 생성 → AI 생성 → 엑셀 내보내기)
- [ ] KOSHA DB SSH 터널 연결 확인 (AI 생성 실제 동작)
- [ ] git hook → change_history.jsonl 자동 기록
