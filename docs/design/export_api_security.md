# Export API 보안/권한 정의

**작성일**: 2026-04-24  
**범위**: v1 최소 기본안

---

## 1. v1 보안 수준 결정

| 운영 환경 | 권한 처리 |
|---------|---------|
| 내부 전용 (인트라넷, VPN 내부) | 인증 **생략 가능** |
| 외부 접근 가능 환경 | API Key 헤더 필수 |

> v1은 내부 API 우선으로 설계. 외부 공개 시 API Key 방식 즉시 적용 가능하도록 헤더 규격만 확정.

---

## 2. API Key 방식 (v1 표준)

### 요청 헤더

```
Authorization: Bearer <token>
```

| 항목 | 결정 |
|------|------|
| 헤더명 | `Authorization` |
| 스킴 | `Bearer` |
| 토큰 형식 | 불투명 랜덤 문자열 (UUID v4 권장, 최소 32자) |
| 전달 방식 | HTTP 헤더만 허용 (쿼리 파라미터 금지 — 로그 노출 위험) |
| 토큰 저장 | 서버 측 환경변수 또는 secrets manager (평문 DB 저장 금지) |

### 토큰 예시

```
Authorization: Bearer 4f3a1d9e-7b2c-4e8a-92f1-d6c0e3a5b710
```

---

## 3. 인증 실패 응답

```
HTTP 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer realm="forms-api"
```

```json
{
  "success": false,
  "error_code": "UNAUTHORIZED",
  "message": "유효한 인증 토큰이 필요합니다.",
  "details": {}
}
```

---

## 4. 인가 (Authorization)

v1 범위:

- **단일 토큰 = 전체 접근 허용** (role 구분 없음)
- 특정 form_type만 허용하는 토큰 구분: **v2 예정**

---

## 5. 요청 제한 (Rate Limiting)

| 항목 | v1 기본값 | 비고 |
|------|--------|------|
| 분당 최대 요청 | 60회/토큰 | 웹 프레임워크 미들웨어 수준 |
| 파일 크기 제한 | 응답 크기 ≤ 10MB | xlsx 단일 시트 특성상 초과 불가 |
| 요청 body 크기 제한 | ≤ 1MB | form_data JSON |

---

## 6. 전송 보안

| 항목 | 결정 |
|------|------|
| 프로토콜 | HTTPS 필수 (외부 접근 시) / 내부망은 HTTP 허용 |
| HSTS | 외부 공개 시 적용 |
| CORS | 허용 Origin 화이트리스트 (내부 도메인만 허용) |

---

## 7. 로그 정책

| 항목 | 로그 여부 |
|------|---------|
| 요청 form_type | ✓ 기록 |
| 요청 시각 | ✓ 기록 (KST) |
| 클라이언트 IP | ✓ 기록 |
| form_data 원문 | ✗ **기록 금지** (개인정보 포함 가능) |
| 토큰 값 | ✗ **기록 금지** |
| builder 성공/실패 | ✓ 기록 |
| 오류 traceback | ✓ 서버 로그 (클라이언트 미노출) |

---

## 8. v2 확장 포인트

| 항목 | 계획 |
|------|------|
| OAuth 2.0 / JWT | 사용자별 토큰, 만료 시간, refresh |
| Role-based 접근 | form_type별 허용 role 제한 |
| Audit log | 생성 이력 DB 기록 (누가, 언제, 어떤 서식) |
| IP 화이트리스트 | 특정 IP 대역만 허용 |
