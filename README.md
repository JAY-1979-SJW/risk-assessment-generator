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

## 개발 로그 관리 규칙

코드 수정 시 아래 3가지를 함께 관리한다.

| 축 | 위치 | 목적 |
|----|------|------|
| 작업일지 | `docs/devlog/YYYY-MM-DD_작업명.md` | 변경 이유·시도·검증 기록 |
| 변경 이력 | `logs/change_history.jsonl` | 커밋과 작업일지 연결 |
| 실행 로그 | 서버 `~/kosha_scraper/logs/` | 스크립트 실행 결과 |

**작업 절차**

```
1. 기능 수정 전 → docs/devlog/ 에 작업일지 초안 작성
2. 코드 수정 → git commit (커밋 메시지에 목적 명시)
3. 커밋 후 → logs/change_history.jsonl 에 1줄 append
4. 데이터 변환 작업 → 서버 실행 로그 별도 보관 (kosha_scraper/logs/)
```

**change_history.jsonl 항목 형식**

```json
{
  "timestamp": "YYYY-MM-DDTHH:MM:SS+09:00",
  "task_name": "작업명",
  "changed_files": ["경로1", "경로2"],
  "summary": "한 줄 요약",
  "result": "검증 결과",
  "commit_hash": "git short hash",
  "devlog": "docs/devlog/파일명.md"
}
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
