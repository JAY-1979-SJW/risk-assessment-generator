# 운영규칙

## 작업규칙
- 단계별 1개씩 실행 → 검증 → 보고 → 자동 다음 단계 (매번 사용자 확인 불필요)
- 파일 여러 개 동시 생성 금지
- 기존 파일 수정 전 Read 확인
- 코드에 비밀번호·키 하드코딩 금지

## 배포규칙
- 서버: git pull --ff-only 방식만 사용
- scp, docker cp, 컨테이너 내부 직접 수정 금지

## 고정값
- 저장소: risk-assessment-generator
- 서버경로: /home/ubuntu/app/risk-assessment-generator
- 도메인: kras.haehan-ai.kr
- 컨테이너: kras-web / kras-api / kras-db
- Volume: kras_pgdata / Network: kras-net
