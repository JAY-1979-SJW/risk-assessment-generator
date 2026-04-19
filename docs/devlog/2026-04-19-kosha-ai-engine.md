# OpenAI 기반 위험성평가 자동생성 엔진 구현

- 작업일시: 2026-04-19
- 작업자: JAY-1979-SJW
- 관련 브랜치: master
- 관련 커밋: (진행중)

## 목표

KOSHA 지식DB의 raw_text를 OpenAI API로 구조화하여
업종/공종 입력만으로 위험성평가 항목을 자동 생성한다.

## 수정 파일

- core/db_connector.py (신규)
- core/openai_engine.py (신규)
- gui/risk_assessment_tab.py (AI 자동생성 섹션 추가)
- backend/main.py (API 엔드포인트 추가)
- backend/requirements.txt (openai 패키지 추가)
- infra/docker-compose.yml (OPENAI_API_KEY env 추가)

## 변경 이유

기존 risk_data.py는 소방시설공사 한정 하드코딩 데이터로
타 업종 확장이 불가능했다. KOSHA DB에 수집된 raw_text를
활용하면 어떤 업종/공종도 AI 기반으로 위험항목을 생성할 수 있다.

## 시도/실패 내용

- control_measure 필드 활용 검토 → 전부 "대책", "예방" 단어 1개뿐이라 폐기
- raw_text 전체 전달 시도 → 토큰 초과, MAX_CONTEXT_CHARS=12000 제한 적용

## 최종 적용 내용

1. `core/db_connector.py`: kosha_chunk_tags JOIN kosha_material_chunks로
   trade_type 기준 청크 최대 30건 조회
2. `core/openai_engine.py`: gpt-4o-mini, JSON mode, 최대 15개 항목 추출
3. `gui/risk_assessment_tab.py`: AIGenerateWorker(QThread) + "③ AI 자동생성" 섹션
4. `backend/main.py`:
   - GET /trades: 공종 목록
   - GET /kosha/search: 청크 검색
   - POST /generate: AI 위험성평가 생성

## 검증 결과

- `python -m py_compile` 문법 오류 없음
- `from core.openai_engine import generate_risk_items` import 성공
- `from core.db_connector import fetch_chunks_for_work` import 성공
- 실제 API 호출은 OPENAI_API_KEY + SSH 터널 필요 (미완료)

## 영향 범위

- 기존 하드코딩 위험요소 검색 기능 유지 (덮어쓰지 않음)
- 신규 "③ AI 자동생성" 섹션만 추가됨

## 다음 단계

1. .env에 OPENAI_API_KEY 실제 키 입력
2. SSH 터널(5435) 연결 후 실제 생성 테스트
3. 결과 품질 검토 → 프롬프트 튜닝
4. 프론트엔드 웹 페이지에 /generate 연동
