-- ======================================================================
-- Migration 0007 : law_meta 오염 분리 (원본 보존, 보정 필드만 추가)
-- normalized_type, corrected_law_name 계산
-- ======================================================================

BEGIN;

-- 1) law_meta.normalized_type = 실제 documents.source_type 기반으로 1차 할당
UPDATE law_meta lm
   SET normalized_type = d.source_type
FROM documents d
WHERE d.id = lm.document_id
  AND (lm.normalized_type IS NULL OR lm.normalized_type <> d.source_type);

-- 2) documents.source_type='law' 이면서 law_name 패턴이 서식/별표/기술기준일 경우 세분 분류
-- 2a) 서식류
UPDATE law_meta lm
   SET normalized_type = 'form'
FROM documents d
WHERE d.id = lm.document_id
  AND d.source_type='law'
  AND (
       lm.law_name ~ '(신청서|계약서|보고서|결과서|증명서|계획서|장부|통보서|성적서|기록부|명령서)$'
    OR lm.law_name LIKE '(안전관리전문기관%'
    OR lm.law_name LIKE '변경신청서%'
    OR lm.law_name LIKE '지정신청서%'
    OR lm.law_name LIKE '지정서(%'
    OR lm.law_name LIKE '%업무계약서'
  );

-- 2b) 별표류 (세부내용/구성해야.../두어야.../작성해야...)
UPDATE law_meta lm
   SET normalized_type = 'table'
FROM documents d
WHERE d.id = lm.document_id
  AND d.source_type='law'
  AND (
       lm.law_name ~ '의 세부 내용\(제\d+'
    OR lm.law_name ~ '(구성해야|두어야|작성해야).*\(.*관련\)'
    OR lm.law_name LIKE '%관련)%'
  )
  AND lm.normalized_type <> 'form';

-- 2c) 실제론 admrul인데 law_meta(law)에 섞여 들어온 기술기준류
UPDATE law_meta lm
   SET normalized_type = 'admrul'
FROM documents d
WHERE d.id = lm.document_id
  AND d.source_type='law'
  AND (
       lm.law_name LIKE '%NFTC%'
    OR lm.law_name LIKE '%화재안전기술기준%'
    OR lm.law_name IN (
         '전기설비기술기준','전기설비기술기준 운영요령',
         '전기통신사업용 무선설비의 기술기준',
         '방송통신설비의 기술기준에 관한 표준시험방법',
         '화학물질의 분류·표시 및 물질안전보건자료에 관한 기준',
         '불활성화비 계산방법 및 정수처리 인증 등에 관한 규정',
         '건설업 산업안전보건관리비 계상 및 사용기준',
         '사업장 위험성평가에 관한 지침',
         '산업안전보건관리비 사용계획서'
       )
  );

-- 3) documents.corrected_source_type = 실제론 admrul 등이어야 하는 오분류 표시
UPDATE documents d
   SET corrected_source_type = lm.normalized_type
FROM law_meta lm
WHERE d.id = lm.document_id
  AND d.source_type='law'
  AND lm.normalized_type IN ('admrul','form','table');

-- 4) corrected_law_name 보정: 서식의 불필요한 접두 제거
UPDATE law_meta lm
   SET corrected_law_name = regexp_replace(lm.law_name,
        '^\(안전관리전문기관, 보건관리전문기관, 건설재해예방전문지도기관\)',
        '',
        'g')
WHERE lm.normalized_type='form'
  AND lm.law_name LIKE '(안전관리전문기관%';

COMMIT;

-- 검증
SELECT normalized_type, COUNT(*) AS rows,
       COUNT(DISTINCT law_name) AS unique_names,
       COUNT(*) FILTER (WHERE corrected_law_name IS NOT NULL) AS corrected
FROM law_meta
GROUP BY normalized_type
ORDER BY 2 DESC;

SELECT 'documents corrected_source_type'::text, corrected_source_type, COUNT(*)
FROM documents WHERE corrected_source_type IS NOT NULL
GROUP BY 2 ORDER BY 3 DESC;
