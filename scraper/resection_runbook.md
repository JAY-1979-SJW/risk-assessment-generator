# section_type 재분류 실행 절차

## 실행 전제 조건
- `python3 kosha_parser.py --pending` 프로세스 완전 종료 확인
- `git pull --ff-only` 로 최신 코드 반영 확인

## 실행 순서

### Step 1: success/foreign 정리 (DB 직접)
```sql
BEGIN;
DELETE FROM kosha_material_chunks c
USING kosha_material_files f
WHERE c.file_id = f.id
  AND f.parse_status = 'success' AND f.lang_verdict = 'foreign';
UPDATE kosha_material_files
SET parse_status = 'excluded_foreign'
WHERE parse_status = 'success' AND lang_verdict = 'foreign';
COMMIT;
```
검증: `SELECT COUNT(*) FROM kosha_material_files WHERE parse_status='success' AND lang_verdict='foreign';` → 0건

### Step 2: success/NULL 언어 재판정
```bash
cd /home/ubuntu/app/risk-assessment-generator/scraper
python3 kosha_parser.py --reclassify
```
검증: `SELECT lang_verdict, COUNT(*) FROM kosha_material_files WHERE parse_status='success' GROUP BY lang_verdict;`
- keep: 전체 success
- NULL: 0건

### Step 3: pending 재처리 (새로 추가된 korean_doc 342건)
```bash
python3 kosha_parser.py --pending
```
검증: `SELECT COUNT(*) FROM kosha_material_files WHERE parse_status='pending';` → 0건

### Step 4: section_type 전체 재분류
```bash
python3 kosha_parser.py --resection
```
예상 완료 시간: 청크 약 8,000~10,000건 기준 1~3분

### 실행 후 검증 쿼리
```sql
-- 분포 확인 (예상: hazard 50%+, general 25%, law/control/ppe 각 5~10%)
SELECT section_type, COUNT(*) as cnt,
       ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 1) as pct
FROM kosha_material_chunks
GROUP BY section_type ORDER BY cnt DESC;

-- 건설업 핵심 청크 샘플
SELECT m.title, c.section_type, left(c.normalized_text, 80) as text
FROM kosha_material_chunks c
JOIN kosha_material_files f ON c.file_id = f.id
JOIN kosha_materials m ON f.material_id = m.id
WHERE m.industry = '건설업' AND m.title LIKE '%공종별%'
ORDER BY m.title, c.chunk_index
LIMIT 10;

-- hazard 청크에 실제 위험요인 내용 있는지 확인
SELECT COUNT(*) as hazard_with_keywords
FROM kosha_material_chunks
WHERE section_type = 'hazard'
  AND (normalized_text LIKE '%위험요인%' OR normalized_text LIKE '%추락%'
    OR normalized_text LIKE '%협착%' OR normalized_text LIKE '%위험성평가%');
```

## 기대 결과 (시뮬레이션 기준)
| section_type | 수정 전 | 수정 후 예상 |
|---|---|---|
| hazard | 450 (6%) | ~4,300 (55~58%) |
| general | 674 (9%) | ~2,000 (25~27%) |
| control | 378 (5%) | ~460 (6%) |
| law | 2,850 (39%) | ~458 (6%) |
| ppe | 2,943 (40%) | ~229 (3%) |
