COPY (
  WITH ranked AS (
    SELECT km.id AS material_id,
           km.title, km.category, km.list_type, km.industry, km.reg_date,
           km.download_url, km.conts_atcfl_no, km.doc_category,
           km.source, km.keyword,
           kmf.file_path, kmf.file_hash, kmf.parse_status, kmf.raw_text,
           length(COALESCE(kmf.raw_text,'')) AS rt_len,
           row_number() OVER (PARTITION BY km.id
                              ORDER BY length(COALESCE(kmf.raw_text,'')) DESC NULLS LAST) AS rn
    FROM kosha_materials km
    JOIN kosha_material_files kmf ON kmf.material_id = km.id
    WHERE kmf.raw_text IS NOT NULL
      AND length(kmf.raw_text) >= 100
      AND kmf.parse_status IN ('success','extracted')
      AND (km.doc_category IS NULL
           OR km.doc_category NOT IN ('foreign_worker','sign_sticker','poster','vr_content','infographic'))
  )
  SELECT material_id, title, category, list_type, industry, reg_date, download_url,
         conts_atcfl_no, doc_category, source, keyword,
         file_path, file_hash, rt_len, raw_text
  FROM ranked
  WHERE rn = 1
) TO '/tmp/kosha_incremental.csv'
  WITH (FORMAT csv, DELIMITER ',', HEADER true, QUOTE '"', NULL '');
