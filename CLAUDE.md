# 운영규칙

## 작업규칙
- 단계별 1개씩 실행 → 검증 → 보고 → 자동 다음 단계 (매번 사용자 확인 불필요)
- 파일 여러 개 동시 생성 금지
- 기존 파일 수정 전 Read 확인
- 코드에 비밀번호·키 하드코딩 금지

## 세션 시작 시 우선 확인 (매 접속 시 자동 수행)
1. 작업 로그 확인: `cat /tmp/kosha_migration.log 2>/dev/null` (DB서버), 진행 중인 작업 이어받기
2. 서버 수집 프로세스 확인: `ps aux | grep kosha | grep -v grep`
3. 최신 로그 확인: `tail -20 ~/kosha_scraper/kosha_dl*.log | tail -20`
4. 로그 파일 정상 기록 여부: `ls -lh ~/kosha_scraper/logs/`
5. DB 수집 현황: kosha_material_files COUNT, 잔여 건수
6. 이상 발견 시 사용자에게 즉시 보고

## 배포규칙
- 서버: git pull --ff-only 방식만 사용
- scp, docker cp, 컨테이너 내부 직접 수정 금지

## 고정값
- 저장소: risk-assessment-generator
- 서버경로: /home/ubuntu/app/risk-assessment-app
- 데이터경로: /home/ubuntu/data/risk-assessment-app
- 로그경로: /home/ubuntu/logs/risk-assessment-app
- 도메인: kras.haehan-ai.kr
- 컨테이너: risk-assessment-web / risk-assessment-api / risk-assessment-db
- Volume: risk-assessment-pgdata / Network: risk-assessment-net

## 수집 범위 (KOSHA 지식DB)
- 대상 list_type: OPS, 기타 (한국어 안전보건 자료만)
- 제외 list_type: 외국어교재, 외국어교안, 동영상
- 대상 doc_type: text_pdf, hwp, zip (image_pdf 제외 — 포스터류, 텍스트 없음)
- 제외 doc_type: excluded (DB 마킹) — 픽토그램/스티커, VR/동영상, 외국어 OPL, 단순안내/홍보/포스터
- 이 앱(위험성평가표 자동생성기) 전용 수집만 수행, 타 폴더·앱 데이터 수집 금지

## 서버 접속
- SSH 키: ~/.ssh/haehan-ai.pem
- 앱서버: ubuntu@1.201.176.236  (kras 컨테이너 운영)
- DB서버: ubuntu@1.201.177.67   (haehan-webdb, common_data DB)
- DB 터널: ssh -i ~/.ssh/haehan-ai.pem -L 5435:localhost:5432 ubuntu@1.201.177.67 -N -f
- 앱서버 접속: ssh -i ~/.ssh/haehan-ai.pem ubuntu@1.201.176.236
