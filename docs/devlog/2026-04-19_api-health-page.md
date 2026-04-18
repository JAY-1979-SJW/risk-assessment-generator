# 작업일지: API health 체크 페이지 신설

- **날짜**: 2026-04-19
- **작업자**: JAY-1979-SJW
- **커밋**: `1a6f821`

---

## 작업명
KRAS API health 체크 페이지 신설

## 목표
`GET /health`가 `{"status":"ok"}` 단순 응답만 반환하는 문제 개선.
프론트엔드에서 API/DB 상태 및 KOSHA 수집 현황을 실시간으로 확인 가능하게 함.

## 수정 파일
- `backend/main.py` — /health 엔드포인트 강화, CORS 추가
- `backend/requirements.txt` — psycopg2-binary 추가
- `frontend/src/App.jsx` — 헬스 대시보드 페이지
- `frontend/nginx.conf` — /api/ 프록시 설정 (신규)
- `frontend/Dockerfile` — nginx.conf 적용

## 변경 이유
- 헬스체크 알림에서 attendance 컨테이너 FAIL 수신 → 즉각 상태 확인할 UI 필요
- 기존 `/health`는 DB 연결 여부조차 반환하지 않아 장애 원인 파악 불가
- KOSHA 수집 진행률을 외부에서 확인할 수 있는 화면 없음

## 시도 / 실패 내용
- 프론트엔드 fetch URL: CORS 문제 예상 → nginx `/api/` 프록시로 해결
- psycopg2 미설치로 서버 임포트 에러 → requirements.txt에 추가

## 최종 적용 내용

```
GET /health 반환값:
{
  "status": "ok" | "degraded",
  "api": "up",
  "db": "connected" | "error" | "not_configured",
  "kosha": {
    "materials": 7878,
    "files": {"success": 3544, "pending": 4183, ...},
    "chunks": 7142,
    "tags": 7142
  }
}
```

프론트엔드: 30초 자동 갱신 대시보드

## 검증 결과
- `git pull --ff-only` 배포 완료
- 엔드포인트 응답 확인 (로컬 테스트)
- attendance 헬스체크 재확인: 401 정상 반환 (500은 일시적 오류였음)

## 다음 단계
- kras-api/kras-web 컨테이너 실제 구동 후 통합 테스트
- `/api/generate` 위험성평가표 생성 엔드포인트 개발
