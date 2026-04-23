# 서식 저장 구조 v1

**작성일**: 2026-04-23
**근거**: `docs/standards/form_collection_inventory.md` §5 (공통 컬럼 스키마), §2 (출처별 인벤토리)
**적용 대상**: 프로젝트 전체의 hwp / hwpx / pdf / docx / xlsx / xls 서식 원본.

---

## 1. 설계 원칙

1. **원본 보존 우선**: 기존 수집본(`data/raw/law_api/`, `data/raw/moel_forms/`, `scraper/kosha_files/`, `참조자료/`, `export/`)은 그대로 둔다 — 수집 출처 단위 보존이 최우선.
2. **권위 뷰는 별도 계층**: `data/forms/A_official/`, `B_semi_official/`, `C_field_practice/`를 **권위 기반 뷰**로 별도 구축.
3. **중복 저장 최소화**: OneDrive 경로에서 수백~수천 파일의 물리 복사는 공간·동기화 부담이 크므로, **정본은 `data/raw` 또는 `참조자료` 유지**, 권위 뷰는 **복사 또는 하드링크**.
   - 본 프로젝트는 Windows + OneDrive 환경. 심볼릭 링크는 관리자 권한 필요 → **복사(copy)** 방식 채택. 단, **권위 뷰 진입 대상은 "편집형 서식 템플릿"으로 한정**하여 전체 2,778건 전량 복사를 피함.
4. **파일명 규칙 단일화**: 저장 시 `source__doc_type__title__date.ext` 형식으로 **리네임한 사본**을 둔다. 원본 파일명은 `source_map.csv`에 보존.
5. **hwp/hwpx 쌍**: 공공기관은 통상 hwp + hwpx를 함께 배포. 권위 뷰에서는 **두 형식 모두 포함**한다(편집 환경 호환성).

---

## 2. 디렉토리 구조

```
data/
├── raw/                                # 출처별 원본 수집본 (기존 보존)
│   ├── law_api/
│   │   ├── licbyl/                      # 법령 별지/별표 hwp·hwpx
│   │   ├── law/
│   │   ├── admrul/
│   │   └── expc/
│   ├── moel_forms/
│   │   └── policy_data/files/
│   ├── kosha/                           # OPL 메타 JSON
│   └── kosha_forms/                     # KOSHA 서식 API 메타 JSON
├── forms/                              # 권위 기반 뷰 (본 레이아웃 신설)
│   ├── A_official/                      # 법정 원본·공단 공식
│   │   ├── licbyl/                       # 법령 별지·별표 서식
│   │   │   ├── [별지_제2호서식]_안전관리자_보건관리자_산업보건의.hwp
│   │   │   └── …
│   │   ├── kras/                         # KOSHA KRAS 표준안
│   │   │   └── KOSHA__표준안__위험성평가_경비업__2015.xls
│   │   └── regulation/                   # 실시규정·고시·매뉴얼 표준문서
│   │       └── INTERNAL__규정__위험성평가_표준실시규정__v1.docx
│   ├── B_semi_official/                 # MOEL·KOSHA 배포 가이드·표준모델·점검표
│   │   ├── moel_guide/                   # MOEL 업종별 안내서·가이드
│   │   │   └── MOEL__안내서__소규모_사업장_위험성평가__20230918.hwp
│   │   ├── moel_checklist/               # 업종별 자율점검표
│   │   │   └── MOEL__자율점검표__건설업_중대재해_예방__20211221.hwp
│   │   ├── moel_model/                   # 표준 모델 (실험실·단체급식 등)
│   │   │   └── MOEL__표준모델__교육서비스_위험성평가_실험실.hwp
│   │   ├── kosha_form/                   # KOSHA 배포 서식 (hwp)
│   │   └── ref_template/                 # 준공식 xlsx (공문기반 본표)
│   │       └── INTERNAL__본표__위험성평가표_공문기반__v2_20250114.xlsx
│   ├── C_field_practice/                # 현장 실무·내부 변형·테스트
│   │   ├── internal_draft/               # 사내 초기 드래프트
│   │   │   └── INTERNAL__본표__위험성평가표_공문기반__v1_20250114.xlsx
│   │   ├── internal_test/                # 개발 테스트
│   │   │   └── INTERNAL__테스트__test_output.xlsx
│   │   └── compact/                      # 축약형 파생
│   │       └── INTERNAL__본표_축약__표준양식_테스트.xlsx
│   ├── source_map.csv                    # 권위 뷰 ↔ 원본 위치 매핑
│   └── README.md                         # 본 레이아웃의 간단 사용 가이드
└── normalized/                         # 정규화된 파싱 산출물 (기존)
```

---

## 3. 파일명 규칙

### 3.1 포맷

```
{source_code}__{doc_type}__{title_slug}__{date}.{ext}
```

### 3.2 필드 정의

| 필드 | 허용값 | 설명 |
|------|--------|------|
| `source_code` | `LAW` · `MOEL` · `KOSHA` · `INTERNAL` | `LAW`는 국가법령정보센터 licbyl 등 법령 원본 |
| `doc_type` | `별지` · `별표` · `본표` · `점검표` · `자율점검표` · `계획서` · `안내서` · `가이드` · `표준모델` · `표준안` · `규정` · `고시` · `매뉴얼` · `일지` · `회의록` · `TBM` · `교육` · `테스트` · `기타` | 문서 용도 |
| `title_slug` | 공백 → `_`, 한글·영문·숫자만 유지 (특수문자 `ㆍ／() 등` 제거 또는 `_` 치환) | 원 제목의 주요 단어 3~8개 |
| `date` | `YYYYMMDD` 또는 `YYYY`(월·일 없음) 또는 `N/A` | 원본 게시일/발간일. 미상이면 `N/A` |
| `ext` | `hwp` · `hwpx` · `pdf` · `docx` · `xlsx` · `xls` | 원 확장자 유지 |

### 3.3 예시

| 원본 | 재명명 |
|------|--------|
| `[별지 제19호서식] 유해위험방지계획서 산업안전….hwp` | `LAW__별지__유해위험방지계획서_산업안전_제19호__N/A.hwp` |
| `230918 소규모 사업장을 위한 위험성평가 안내서(최종).hwp` | `MOEL__안내서__소규모_사업장_위험성평가__20230918.hwp` |
| `화학업종 중소기업을 위한 안전보건관리 자율점검표.hwp` | `MOEL__자율점검표__화학업종_중소기업_안전보건__N/A.hwp` |
| `위험성평가표_공문기반_20250114_v2.xlsx` | `INTERNAL__본표__위험성평가표_공문기반_v2__20250114.xlsx` |
| `위험성평가 표준안(경비).xls` | `KOSHA__표준안__위험성평가_경비업__N/A.xls` |

### 3.4 중복 규칙

- 재명명 후 완전 동명 충돌이 생기면 말미에 `__dup1`, `__dup2` 접미사를 붙인다 (예: `…__20250114__dup1.xlsx`).
- 해시 비교(SHA-256) 결과 **완전 동일** 파일이면 **권위 뷰에는 1부만** 저장하고, `source_map.csv`에 중복 원본 경로를 모두 기록.

---

## 4. `source_map.csv` 스키마

권위 뷰에 배치된 각 파일의 원본 위치 추적용. Step 3에서 채운다.

| 컬럼 | 예 |
|------|----|
| `view_path` | `data/forms/A_official/licbyl/LAW__별지__유해위험방지계획서_제19호__N/A.hwp` |
| `source_path` | `data/raw/law_api/licbyl/files/17853697/[별지 제19호서식] 유해위험방지계획서 산업안전….hwp` |
| `source_url` | (있으면) `https://law.go.kr/DRF/…licOrdinJoSc.do?…` |
| `source_code` | `LAW` |
| `source_id` | `17853697` |
| `doc_type` | `별지` |
| `doc_title` | `유해위험방지계획서 (시행규칙 제19호서식)` |
| `date` | `N/A` |
| `ext` | `hwp` |
| `authority_grade` | `A` |
| `is_original` | `Y` |
| `checksum_sha256` | 64자 hex |
| `size_bytes` | 정수 |
| `notes` | (자유 기술) |

---

## 5. 권위 뷰 진입 범위 (무엇을 data/forms/로 옮길 것인가)

2,778건 전량 복사는 비현실적. 아래 기준으로 **권위 뷰 진입 범위**를 제한한다.

| 원본 | 권위 뷰 진입 여부 | 근거 |
|------|-------------------|------|
| `data/raw/law_api/licbyl/files/**/*.hwp/hwpx` | **전량 진입** | 법정 별지·별표 = 전수 **A** |
| `data/raw/moel_forms/**/*.hwp(x)` 중 "서식성" (위험성평가·점검표·표준모델·안내서·가이드·회의록·일지·계획서 키워드 파일) | **선별 진입** | 편집형 서식/가이드만, 법 개정문·공고문은 제외 |
| `scraper/kosha_files/**/*.pdf` | **진입 금지** (참고자료 목록만 유지) | 대부분 OPS 교재 — 편집형 서식 아님. Step 4에서 필요 시 개별 지정 |
| `scraper/kosha_files/**/*.hwp` (5건) | **선별 진입** | 편집 가능 여부 Step 3 확인 후 결정 |
| `참조자료/*.xls`, `*.docx` | **전량 진입** | 내부 보유 핵심 원본 |
| `export/위험성평가표_*.xlsx` | **전량 진입** | 본표 레이아웃 후보 |
| 루트 `test_output*.xlsx` | **C 진입** (테스트 계층) | 개발 샘플 |
| 루트 `국가법령정보공유서비스_…_활용가이드.docx` | **진입 금지** | 기술 API 가이드, 서식 아님 |

---

## 6. 실행 순서 (Step 3에서)

1. `data/forms/A_official/licbyl`, `…/kras`, `…/regulation` 폴더 생성.
2. `data/forms/B_semi_official/moel_guide`, `…/moel_checklist`, `…/moel_model`, `…/kosha_form`, `…/ref_template` 생성.
3. `data/forms/C_field_practice/internal_draft`, `…/internal_test`, `…/compact` 생성.
4. `data/raw/law_api/licbyl/files/**/*.hwp(x)` → `A_official/licbyl/` 재명명 복사.
5. MOEL 선별 파일(§5 기준) → `B_semi_official/…` 재명명 복사.
6. 내부 파일 → `B_semi_official/ref_template` 또는 `C_field_practice/…` 재명명 복사.
7. `source_map.csv`에 행 단위 기록, SHA-256 동시 계산.
8. 실패·스킵 항목은 `docs/standards/form_collection_log.md`에 사유 기록.

---

## 7. 주의사항

- **.gitignore**: `data/forms/`는 대용량(수십 MB~) + 공공 원본 재배포 이슈 가능성 때문에 **추적 제외 후보**. 결정은 Step 3 말미에 사용자 확인.
- **개인정보**: MOEL 일부 파일명에 "명단", "담당자" 등이 포함됨. Step 4에서 개별 확인 후 C 또는 배제.
- **파일명 길이**: Windows 경로 260자 한계. `source_code + doc_type + title_slug + date` 합산 시 200자 이내로 유지.
- **URL 인코딩 잔재**: 기존 `data/raw/law_api/licbyl/` 파일명에 `%E` 등 UTF-8 조각이 남은 케이스가 있음 — Step 3 복사 시 정리.
