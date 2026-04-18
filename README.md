# 위험성평가표 자동생성기

KRAS 표준 양식 기반 위험성평가표 웹 자동생성 서비스

- 도메인: https://kras.haehan-ai.kr
- 저장소: risk-assessment-generator

## 서비스 구성

| 컨테이너 | 역할 |
|----------|------|
| kras-api | FastAPI 백엔드 |
| kras-web | React 프론트엔드 |
| kras-db  | PostgreSQL |

## 배포 절차

```bash
# 1. 로컬 수정 후 GitHub push
git add .
git commit -m "변경내용"
git push origin master

# 2. 서버 접속
ssh -i ~/.ssh/haehan-ai.pem ubuntu@1.201.176.236

# 3. 서버에서 배포 실행
cd /home/ubuntu/app/risk-assessment-generator
bash infra/deploy.sh
```

## 초기 서버 설정 (최초 1회)

```bash
git clone https://github.com/JAY-1979-SJW/risk-assessment-generator.git \
  /home/ubuntu/app/risk-assessment-generator
cd /home/ubuntu/app/risk-assessment-generator/infra
cp .env.example .env
# .env 파일에서 비밀번호 변경 후 저장
docker compose --env-file .env up -d --build
```
