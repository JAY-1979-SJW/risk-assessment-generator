# 신축공사 안전서류 자동생성 웹 연동 설계

**버전**: V1.0 설계 문서  
**작성일**: 2026-04-29  
**범위**: 신축공사 기준 (착공~준공)  
**기준**: 핵심서류 90종 + 부대서류 10종 + 신축공사 일정 매트릭스  
**최종 목표**: 공사 등록 → 일정/공종 선택 → 필요서류 자동 추천 → 문서 패키지 생성

> **제외 범위**: 리모델링, 개보수, 외국인용 다국어 서류, 소방감리 전용, 석면해체

---

## 목차

1. [설계 범위 및 기본 원칙](#1-설계-범위-및-기본-원칙)
2. [사용자 흐름 (User Flow)](#2-사용자-흐름-user-flow)
3. [데이터 모델 (Data Model)](#3-데이터-모델-data-model)
4. [자동생성 규칙 (Generation Rules)](#4-자동생성-규칙-generation-rules)
5. [문서 패키지 구조](#5-문서-패키지-구조)
6. [화면 구성 (UI Mockup)](#6-화면-구성-ui-mockup)
7. [API 설계](#7-api-설계)
8. [V1.1 구현 범위](#8-v11-구현-범위)
9. [V2.0 이후 로드맵](#9-v20-이후-로드맵)

---

## 1. 설계 범위 및 기본 원칙

### 1-1. 설계 목표

신축공사의 안전서류 자동생성을 웹으로 제공하여:
- **착공 전**: 기본 안전체계 수립에 필요한 서류 일괄 생성
- **근로자 투입 전**: 교육·서약·보호구 관련 서류 자동 제안
- **공종 착수 전**: 작업계획서·허가서·특별교육 서류 맞춤 생성
- **매일**: TBM·안전점검 등 반복 서류 생성 지원
- **사고 발생 시**: 긴급 서류 생성 및 제출 가능

### 1-2. 설계 제약 조건

| 항목 | 제약 사항 |
|-----|----------|
| **신규 builder** | 절대 생성 금지 (기존 90종 활용만) |
| **기존 builder 수정** | 절대 금지 (layout/style 완료 상태 유지) |
| **문서 카탈로그** | document_catalog.yml 수정 금지 |
| **등록부** | form_registry.py, supplementary_registry.py 수정 금지 |
| **범위** | 신축공사만 (리모델링, 외국인용, 소방감리 제외) |
| **구현 시기** | 이번 단계는 설계만 (코드 구현 X) |

### 1-3. 기존 산출물 기준

- **핵심서류**: 90종 (form_registry.py 등록)
  - Phase별 서류 (계약~준공, 13단계)
  - PTW 및 특별작업계획서 (10+가지)
  - 정기/반복 서류 (교육, 순찰, 점검)
  - 사고 대응 서류 (재해, 아차사고, 원인분석)
  
- **부대서류**: 10종 (supplementary_registry.py 등록)
  - 참석자 명단 (attendance_roster)
  - 사진 첨부 (photo_attachment_sheet)
  - 문서 목록 (document_attachment_list)
  - 측정기록 (confined_space_gas_measurement)
  - 작업 종료 확인 (work_completion_confirmation)
  - 개선조치 확인 (improvement_completion_check)
  - 장비 운전원 자격 (equipment_operator_qualification_check)
  - 감시인 배치 (watchman_assignment_confirmation)
  - 보수교육 확인 (education_makeup_confirmation)
  - 보호구 수령 (ppe_receipt_confirmation)

- **신축공사 일정 매트릭스**: 12 Phase × 자동생성 트리거 규칙

---

## 2. 사용자 흐름 (User Flow)

### Flow 1: 공사 신규 등록

```
사용자: 시공사 관리자
진입점: 웹 대시보드 > [신규 공사] 버튼

1. 공사 기본정보 입력
   - 공사명
   - 발주자 (원청)
   - 시공사 (도급사)
   - 공사 위치 (주소)
   - 공사 성격 (신축 건축, 신축 토목, 신축 기타)
   - 예정 착공일
   - 예정 준공일
   - 공사 금액 (참고용)
   - 안전관리자 지정 여부

2. 공사 생성 → 자동생성 제안
   ├─ Phase 0: 안전관리자 선임 보고서
   ├─ Phase 0: 산업안전보건관리비 사용계획서
   └─ [다음 단계] 버튼 활성화

3. 출력: 공사 ID 생성, 상세 페이지 이동
```

### Flow 2: 공사 기본정보 입력 (계약~착공 전)

```
사용자: 현장소장
진입점: [공사 상세] > [기본정보] 탭

1. 근로자 기본정보 입력
   - 정규근로자 예정 수
   - 협력업체 예정 수
   - 총 근로자 수 통계

2. 공종 정보 입력
   - 공종명 (흙깎기, 파일, 거푸집, 비계, 크레인, 전기, 화기, 밀폐공간 등)
   - 예정 시작일
   - 예정 종료일
   - 담당자 (협력업체)
   - 위험도 (높음/중간/낮음, 자동 추천 가능)

3. 착공 전 필수서류 자동 생성 제안
   ├─ Phase 1: 안전보건 방침·목표 게시문
   ├─ Phase 1: 위험성평가 실시 규정
   ├─ Phase 1: 연간 교육계획서
   ├─ Phase 1: 비상 연락망·대피 계획서
   ├─ Phase 1: 협력업체 안전서류 확인서
   ├─ Phase 1: 도급·용역 안전보건 협의서
   └─ Phase 1: 협력업체 안전보건 수준 평가표

4. 출력: 공사 진행률 표시 (예: "착공 전 준비 30%"), [착공] 버튼 활성화
```

### Flow 3: 공종별 작업 일정 입력

```
사용자: 현장소장
진입점: [공사 상세] > [공종 일정] 탭

1. 공종 선택 (다중 선택 가능)
   □ 토공·굴착
   □ 기초·파일
   □ 골조·거푸집·동바리
   □ 비계·고소작업
   □ 양중·크레인·중량물
   □ 전기·화기·MSDS
   □ 설비·소방설비

2. 각 공종별 착수일 입력
   굴착: 2026-05-15
   파일: 2026-05-20
   ...

3. 착수 3일 전 자동생성 제안 (각 공종별 PTW 세트)
   예시 (굴착):
   ├─ 굴착 작업계획서
   ├─ 굴착 작업 허가서
   ├─ 위험성평가표 (굴착용)
   ├─ 특별 안전보건교육 (굴착)
   ├─ 추락 방호 설비 점검표
   └─ 부대: 참석자 명단, 사진 첨부, 작업 허가 확인 등

4. 출력: 공종별 준비도 대시보드 표시
```

### Flow 4: 장비 반입 등록

```
사용자: 협력업체 / 안전관리자
진입점: [공사 상세] > [장비 관리] > [장비 반입]

1. 장비 정보 입력
   - 장비 종류 (타워크레인, 이동식크레인, 덤프트럭, 하역기계, 고소작업대 등)
   - 장비 제조사·형식
   - 시리얼 번호
   - 예정 반입일
   - 운전원 정보 (사원번호, 자격증 번호)

2. 반입 자동생성 제안
   ├─ 건설 장비 반입 신청서
   ├─ 건설 장비 보험·정기검사증 확인서
   ├─ 건설장비 일일 사전점검표 (반복)
   └─ 타워크레인의 경우 추가:
      ├─ 타워크레인 작업계획서
      └─ 타워크레인 자체 점검표

3. 출력: 장비 관리 카드 생성, 반입일부터 일일 점검표 매일 생성 가능
```

### Flow 5: 근로자 투입 등록

```
사용자: 안전관리자
진입점: [공사 상세] > [근로자 관리] > [신규 근로자 등록]

1. 근로자 정보 입력
   - 근로자명
   - 사원번호
   - 근로자 유형 (정규/협력/외국인)
   - 투입 예정일
   - 역할 (관리감독자, 작업원, 운전원, 안전담당 등)
   - 보유 자격증

2. 투입 전 필수서류 자동생성 제안
   ├─ 안전보건교육 교육일지 (채용 시 8시간+)
   ├─ 신규 근로자 안전보건 서약서
   ├─ 보호구 지급 대장
   ├─ 보호구 지급 및 관리 점검표
   ├─ 위험성평가 결과 근로자 공지문
   └─ 부대: 참석자 명단, 보호구 수령 확인

3. 근로자 투입 완료 → 매일 반복 서류 생성 가능
   ├─ TBM 안전점검 일지
   ├─ 작업 전 안전 확인서
   ├─ 안전관리 일지
   ├─ 관리감독자 안전보건 업무 일지
   └─ [오늘 할 일] 대시보드에 자동 표시

4. 출력: 근로자 프로필 카드, 교육 이력 관리
```

### Flow 6: 매일 아침 TBM 및 일상 점검

```
사용자: 관리감독자 / 안전관리자
진입점: [오늘 할 일] 대시보드 또는 [공사 상세] > [일상 점검]

1. 매일 생성 제안 서류 (자동으로 오늘 날짜로)
   ├─ TBM 안전점검 일지
   ├─ 작업 전 안전 확인서
   ├─ 기상 조건 기록 일지 (강풍·강우 시)
   ├─ 안전관리 일지
   └─ 관리감독자 안전보건 업무 일지

2. 사용자가 [작성 시작] 클릭
   → 기존 데이터 미리 채우기 (근로자 목록, 공종, 날씨)
   → Excel 열기

3. 작성 후 [업로드]
   → 서버에 저장
   → 다음날 자동 제안

4. 출력: 작성 이력 보관, 누적 데이터 통계
```

### Flow 7: 사고/사건 발생 시

```
사용자: 현장소장 / 안전관리자
진입점: [긴급 보고] 버튼 또는 [사건 기록] 메뉴

사례 1) 산업재해 발생
  1. 재해 유형 선택 (중상, 경상, 사망)
  2. 자동생성 제안:
     ├─ 응급조치 실시 기록서 (즉시)
     ├─ 중대재해 즉시 보고서 (중대 시, 고용부 제출용)
     ├─ 산업재해조사표 (1개월 이내)
     ├─ 재해 원인 분석·재발 방지 보고서 (30일 이내)
     └─ 산업재해 발생 현황 관리 대장 (자동 업데이트)
  3. 출력: 재해 기록 카드, 타임라인 표시

사례 2) 아차사고 / 불안전 행동 발견
  1. [아차사고 보고] 메뉴 클릭
  2. 자동생성 제안:
     ├─ 아차사고 보고서
     └─ 개선조치 완료 확인
  3. 출력: 아차사고 일지, 개선조치 추적

사례 3) 위험성평가 개선조치 완료
  1. [개선 완료] 버튼 클릭
  2. 자동생성 제안:
     ├─ 위험성평가 관리 등록부 (업데이트)
     └─ 위험성평가 결과 근로자 공지문 (재공지)
  3. 출력: 개선 히스토리, 위험도 감소율 표시
```

### Flow 8: 준공 전 최종 점검 및 문서 패키지 생성

```
사용자: 현장소장 / 안전관리자
진입점: [준공 전 준비] 또는 자동 알림 (준공 D-30)

1. 자동 알림 발송 (준공 예정일 D-30)
   "준공이 30일 남았습니다. 최종 점검을 시작하세요."

2. 준공 전 최종 점검 서류 자동 제안
   ├─ 안전순찰 점검 일지 (전수 점검)
   ├─ 위험성평가표 (마감 공종 재평가)
   ├─ 협력업체 안전서류 최종 확인
   └─ 개선조치 미완료 잔여 항목 확인

3. 전체 서류 패키지 생성 요청
   [공사 상세] > [서류 패키지 생성]
   
   생성 옵션:
   ├─ 형식 선택: Excel / PDF / ZIP (다중 선택)
   ├─ 서류 범위 선택:
   │  □ 모든 서류 (90종 핵심 + 10종 부대)
   │  □ 핵심서류만
   │  □ 커스텀 (선택한 서류만)
   └─ 정렬 순서:
      ┌ Phase별 (권장)
      └ 서류 유형별

4. 생성 처리
   → 백그라운드 작업 시작
   → 상태 알림 (생성 중... → 완료)
   → 다운로드 링크 제공

5. 출력: 최종 서류 패키지 (ZIP/PDF/Excel)
      → 클라우드 저장 또는 로컬 다운로드
      → 이메일로 자동 전송 (선택)
```

---

## 3. 데이터 모델 (Data Model)

### 3-1. 엔티티 정의

#### Entity 1: Project (공사 기본정보)

```yaml
project:
  project_id: UUID
  project_name: string (공사명)
  project_type: enum [신축건축, 신축토목, 신축기타]
  location: string (공사 위치)
  contract_amount: decimal (공사 금액)
  client_name: string (발주자)
  contractor_name: string (시공사)
  safety_manager_id: string (안전관리자 ID, FK)
  
  # 일정 정보
  planned_start_date: date (예정 착공일)
  planned_end_date: date (예정 준공일)
  actual_start_date: date (실제 착공일, nullable)
  actual_end_date: date (실제 준공일, nullable)
  
  # 단계 정보
  phase: enum [등록, 착공전준비, 착공, 진행중, 준공]
  phase_updated_at: timestamp
  
  # 메타
  created_at: timestamp
  updated_at: timestamp
  created_by: string (사용자 ID)
```

#### Entity 2: Site (현장 정보)

```yaml
site:
  site_id: UUID
  project_id: UUID (FK)
  site_name: string (현장명, 보통 공사명과 동일)
  site_address: string (주소)
  site_manager_id: string (현장소장 ID, FK)
  safety_manager_id: string (안전관리자 ID, FK)
  
  # 연락처
  phone_number: string
  emergency_contact: string (긴급연락처)
  
  # 현장 상태
  status: enum [준비중, 개설, 운영중, 준공]
  total_workers: int (근로자 총수)
  total_subcontractors: int (협력업체 수)
  
  created_at: timestamp
  updated_at: timestamp
```

#### Entity 3: Contractor (협력업체)

```yaml
contractor:
  contractor_id: UUID
  project_id: UUID (FK)
  company_name: string (협력업체명)
  company_registration_no: string (사업자등록번호)
  representative_name: string (대표자명)
  
  # 담당자
  supervisor_id: string (담당 관리감독자 ID, FK)
  safety_contact_id: string (안전담당자 ID, FK)
  
  # 안전정보
  safety_level: enum [높음, 중간, 낮음] (안전보건 수준)
  has_safety_manager: bool (안전관리자 배치 여부)
  
  # 계약정보
  contract_date: date
  contract_amount: decimal
  
  status: enum [신청, 승인, 진행, 완료]
  created_at: timestamp
```

#### Entity 4: Worker (근로자)

```yaml
worker:
  worker_id: UUID
  project_id: UUID (FK)
  contractor_id: UUID (FK, nullable - 정규근로자는 null)
  
  # 기본정보
  worker_name: string
  worker_type: enum [정규, 협력, 외국인]
  role: enum [관리감독자, 작업원, 운전원, 안전담당자, 기타]
  employee_id: string (사원번호)
  
  # 자격정보
  certifications: list[string] (자격증 번호/종류)
  
  # 근무정보
  entry_date: date (투입일)
  exit_date: date (퇴장일, nullable)
  status: enum [예정, 투입, 휴직, 종료]
  
  # 교육 추적
  initial_training_completed: bool (채용 시 교육 완료)
  initial_training_date: date
  monthly_training_count: int (월간 교육 횟수)
  
  created_at: timestamp
  updated_at: timestamp
```

#### Entity 5: Equipment (건설장비)

```yaml
equipment:
  equipment_id: UUID
  project_id: UUID (FK)
  contractor_id: UUID (FK)
  
  # 장비정보
  equipment_type: enum [타워크레인, 이동식크레인, 덤프, 하역기, 고소작업대, ...]
  manufacturer: string
  model: string
  serial_number: string
  
  # 운전원
  operator_id: string (운전원 ID, FK to Worker)
  operator_qualification: string (자격증 번호)
  
  # 보험·검사
  insurance_expiry_date: date (보험만료일)
  inspection_expiry_date: date (정기검사만료일)
  
  # 입반출
  entry_date: date (반입예정일)
  actual_entry_date: date (실제 반입일)
  exit_date: date (반출예정일)
  actual_exit_date: date (실제 반출일)
  
  status: enum [등록, 반입준비, 운영중, 반출, 완료]
  created_at: timestamp
```

#### Entity 6: WorkSchedule (공종 일정)

```yaml
work_schedule:
  work_schedule_id: UUID
  project_id: UUID (FK)
  
  # 공종정보
  work_type: enum [토공굴착, 기초파일, 골조거푸집, 비계고소, 양중크레인, 전기화기, 설비소방]
  work_description: string (상세 공종 설명)
  
  # 일정
  planned_start_date: date
  planned_end_date: date
  actual_start_date: date (nullable)
  actual_end_date: date (nullable)
  
  # 담당자
  supervisor_id: string (현장 관리감독자 ID)
  contractor_id: UUID (FK, 협력업체)
  
  # 위험도
  risk_level: enum [높음, 중간, 낮음]
  hazard_description: string (주요 위험요인)
  
  status: enum [예정, 진행중, 완료, 취소]
  created_at: timestamp
```

#### Entity 7: SafetyEvent (안전 사건/사고)

```yaml
safety_event:
  event_id: UUID
  project_id: UUID (FK)
  
  # 사건 분류
  event_type: enum [산업재해, 아차사고, 불안전행동, 위험상황, 기타]
  severity: enum [사망, 중상, 경상, 미발생] (재해인 경우만)
  
  # 기본정보
  event_date: date
  event_time: time
  location: string (발생 위치)
  description: string (상황 설명)
  involved_worker_id: string (FK to Worker)
  
  # 담당 처리
  reported_by: string (보고자 ID)
  assigned_to: string (담당자 ID)
  
  # 추적정보
  investigation_completed: bool
  investigation_date: date (조사완료일)
  improvement_completed: bool
  improvement_date: date (개선완료일)
  
  status: enum [신고, 조사중, 완료, 종료]
  created_at: timestamp
```

#### Entity 8: DocumentGenerationJob (문서 생성 작업)

```yaml
document_generation_job:
  job_id: UUID
  project_id: UUID (FK)
  
  # 작업정보
  trigger_type: enum [manual, auto_phase, auto_worker, auto_equipment, auto_schedule, auto_event]
  trigger_detail: string (트리거 상세, 예: "worker_id=123" 또는 "work_schedule_id=456")
  
  # 문서목록
  form_ids: list[string] (생성할 form_type 목록)
  supplementary_ids: list[string] (부대서류 목록)
  
  # 메타정보
  requested_by: string (요청자 ID)
  requested_at: timestamp
  
  # 처리 상태
  status: enum [대기, 진행중, 완료, 실패]
  completed_at: timestamp (nullable)
  error_message: string (nullable)
  
  # 생성된 문서
  document_package_id: UUID (FK, 완료 시)
```

#### Entity 9: GeneratedDocumentPackage (생성된 문서 패키지)

```yaml
generated_document_package:
  package_id: UUID
  project_id: UUID (FK)
  job_id: UUID (FK to DocumentGenerationJob)
  
  # 패키지정보
  package_name: string (예: "신축공사_착공전준비_2026-04-29")
  package_type: enum [초안, 검토중, 승인됨, 제출됨, 보관됨]
  
  # 포함된 문서
  documents: list[GeneratedDocument] {
    form_type: string
    document_id: UUID
    created_at: timestamp
    file_path: string (Excel 파일 경로)
    file_size: int
    status: enum [작성중, 완료, 서명대기, 서명완료]
  }
  
  # 출력정보
  formats: list[enum] ([Excel, PDF, ZIP])
  download_links: dict {
    'excel': string (URL),
    'pdf': string (URL),
    'zip': string (URL)
  }
  
  # 통계
  total_documents: int
  completed_documents: int
  pending_signature: int
  
  # 메타
  created_at: timestamp
  updated_at: timestamp
  created_by: string
  shared_with: list[string] (이메일로 공유 받은 사용자)
```

### 3-2. 관계도 (Relationship Diagram)

```
Project (1) ──┬── (M) Site
              ├── (M) Contractor
              ├── (M) Worker
              ├── (M) Equipment
              ├── (M) WorkSchedule
              ├── (M) SafetyEvent
              └── (M) DocumentGenerationJob
                       └── (1) GeneratedDocumentPackage
                                └── (M) GeneratedDocument

Site (1) ──┬── (M) Contractor
           ├── (M) Worker
           └── (M) Equipment

Contractor (1) ──┬── (M) Worker
                 └── (M) Equipment

Worker (1) ──┬── (1) Equipment (운전원 관계)
             └── (M) SafetyEvent

WorkSchedule (1) ──┬── (M) SafetyEvent
                   └── (M) Worker (투입)

SafetyEvent (1) ──── (1) DocumentGenerationJob (자동생성 트리거)
```

---

## 4. 자동생성 규칙 (Generation Rules)

### 4-1. 트리거별 자동생성 규칙

#### Rule-01: 공사 등록 시 (Phase 0)

```yaml
trigger: project.created
timing: 즉시
generated_forms:
  - form_id: safety_manager_appointment_report
    description: 안전관리자 선임 보고서
    priority: high
    deadline: phase_1_start - 7days
    
  - form_id: safety_cost_use_plan
    description: 산업안전보건관리비 사용계획서
    priority: high
    deadline: phase_2_start

supplementary_docs:
  - (없음)
```

#### Rule-02: 착공 전 기본체계 수립 (Phase 1)

```yaml
trigger: project.phase == "착공전준비" && planned_start_date 입력
timing: project.planned_start_date - 14days에 자동 알림
         사용자 [착공전준비] 버튼 클릭 시 즉시

generated_forms:
  - form_id: safety_policy_goal_notice
    description: 안전보건 방침 및 목표 게시문
    priority: high
    
  - form_id: risk_assessment_procedure
    description: 위험성평가 실시 규정
    priority: high
    
  - form_id: annual_safety_education_plan
    description: 연간 안전보건교육 계획서
    priority: high
    
  - form_id: emergency_contact_evacuation_plan
    description: 비상 연락망 및 대피 계획서
    priority: high
    
  - form_id: contractor_safety_document_checklist
    description: 협력업체 안전보건 관련 서류 확인서
    priority: medium
    
  - form_id: contractor_safety_consultation
    description: 도급·용역 안전보건 협의서
    priority: medium
    
  - form_id: subcontractor_safety_evaluation
    description: 협력업체 안전보건 수준 평가표
    priority: medium

supplementary_docs:
  - attendance_roster
  - photo_attachment_sheet
  - document_attachment_list
```

#### Rule-03: 근로자 등록 시 (Phase 3)

```yaml
trigger: worker.created && worker.entry_date >= today
timing: 근로자 등록 즉시 또는
        worker.entry_date - 7days에 자동 알림

generated_forms:
  - form_id: education_log
    description: 안전보건교육 교육일지 (채용 시 8시간)
    priority: high
    deadline: worker.entry_date
    
  - form_id: new_worker_safety_pledge
    description: 신규 근로자 안전보건 서약서
    priority: high
    deadline: worker.entry_date
    
  - form_id: ppe_issue_register
    description: 보호구 지급 대장
    priority: high
    
  - form_id: ppe_management_checklist
    description: 보호구 지급 및 관리 점검표
    priority: high
    
  - form_id: risk_assessment_result_notice
    description: 위험성평가 결과 근로자 공지문
    priority: medium

supplementary_docs:
  - attendance_roster
  - ppe_receipt_confirmation
  - education_makeup_confirmation (미참석자 발생 시)
```

#### Rule-04: 공종 착수 전 (Phase 5)

```yaml
trigger: work_schedule.planned_start_date 입력 && 
          work_schedule.work_type 선택

timing: work_schedule.planned_start_date - 3days
        또는 사용자가 [공종 착수 준비] 클릭

generated_forms (공종별 조건부):
  # 모든 공종
  - form_id: risk_assessment
    description: 위험성평가표 (공종별)
    condition: work_type in [모든 공종]
    
  - form_id: special_education_log
    description: 특별 안전보건교육
    condition: risk_level == "높음" or work_type in [굴착, 밀폐공간, 고소]

  # 토공·굴착
  - form_id: excavation_workplan
    condition: work_type == "토공굴착"
    
  - form_id: excavation_work_permit
    condition: work_type == "토공굴착"
    
  # 파일·항타
  - form_id: piling_workplan
    condition: work_type == "기초파일"
    
  - form_id: piling_use_workplan
    condition: work_type == "기초파일"
    
  # 거푸집·동바리
  - form_id: formwork_shoring_workplan
    condition: work_type == "골조거푸집"
    
  - form_id: formwork_shoring_installation_checklist
    condition: work_type == "골조거푸집"
    
  # 비계·고소
  - form_id: scaffold_installation_checklist
    condition: work_type == "비계고소"
    
  - form_id: aerial_work_platform_use_plan
    condition: "고소작업대" in work_description
    
  - form_id: fall_protection_checklist
    condition: work_type in [비계고소, 토공굴착]
    
  # 양중·크레인
  - form_id: heavy_lifting_workplan
    condition: "중량물" in work_description
    
  - form_id: lifting_equipment_workplan
    condition: "양중기" in work_description or "호이스트" in work_description
    
  - form_id: tower_crane_workplan
    condition: "타워크레인" in work_description
    
  # 전기·화기
  - form_id: electrical_workplan
    condition: "전기" in work_description
    
  - form_id: hot_work_workplan
    condition: "용접" in work_description or "화기" in work_description
    
  # 밀폐공간
  - form_id: confined_space_workplan
    condition: "밀폐공간" in work_description
    
  - form_id: confined_space_permit
    condition: "밀폐공간" in work_description

supplementary_docs:
  - attendance_roster
  - equipment_operator_qualification_check
  - work_completion_confirmation
  - photo_attachment_sheet
  - improvement_completion_check
```

#### Rule-05: 장비 반입 등록 (Phase 4)

```yaml
trigger: equipment.created && equipment.entry_date >= today

timing: equipment.entry_date - 7days에 자동 알림
        장비 등록 즉시

generated_forms:
  - form_id: equipment_entry_application
    description: 건설 장비 반입 신청서
    priority: high
    
  - form_id: equipment_insurance_inspection_check
    description: 건설 장비 보험·정기검사증 확인서
    priority: high
    deadline: equipment.entry_date
    
  - form_id: construction_equipment_daily_checklist
    description: 건설장비 일일 사전점검표
    priority: high
    repeat: daily
    repeat_start: equipment.actual_entry_date
    repeat_end: equipment.exit_date

supplementary_docs:
  - equipment_operator_qualification_check
  - document_attachment_list
  - photo_attachment_sheet
```

#### Rule-06: 매일 작업 시 (Phase 6)

```yaml
trigger: project.status == "진행중" && 
          worker.status == "투입"

timing: 매일 오전 자동 생성 제안
        (사용자가 [오늘 작업 시작] 클릭)

generated_forms:
  - form_id: tbm_log
    description: TBM 안전점검 일지
    priority: high
    repeat: daily
    
  - form_id: pre_work_safety_check
    description: 작업 전 안전 확인서
    priority: high
    repeat: daily
    
  - form_id: weather_condition_log
    description: 기상 조건 기록 일지
    priority: medium
    repeat: daily
    
  - form_id: safety_management_log
    description: 안전관리 일지
    priority: high
    repeat: daily
    
  - form_id: supervisor_safety_log
    description: 관리감독자 안전보건 업무 일지
    priority: high
    repeat: daily

supplementary_docs:
  - attendance_roster
  - photo_attachment_sheet
```

#### Rule-07: 사고 발생 시 (Phase 10)

```yaml
trigger: safety_event.created && 
          safety_event.event_type == "산업재해"

timing: 즉시

generated_forms:
  - form_id: emergency_first_aid_record
    description: 응급조치 실시 기록서
    priority: critical
    deadline: 즉시
    
  - form_id: serious_accident_immediate_report
    condition: safety_event.severity in [사망, 중상]
    description: 중대재해 발생 즉시 보고서
    priority: critical
    deadline: 1시간 (고용부 보고)
    
  - form_id: industrial_accident_report
    description: 산업재해조사표
    priority: high
    deadline: safety_event.event_date + 30days
    
  - form_id: accident_root_cause_prevention_report
    description: 재해 원인 분석 및 재발 방지 보고서
    priority: high
    deadline: safety_event.event_date + 30days
    
  - form_id: industrial_accident_status_ledger
    description: 산업재해 발생 현황 관리 대장 (자동 업데이트)
    priority: high

supplementary_docs:
  - photo_attachment_sheet
  - improvement_completion_check
  - document_attachment_list
```

#### Rule-08: 아차사고 등록 시

```yaml
trigger: safety_event.created && 
          safety_event.event_type == "아차사고"

timing: 즉시

generated_forms:
  - form_id: near_miss_report
    description: 아차사고 보고서
    priority: high
    
  - form_id: risk_assessment
    description: 위험성평가표 (재평가)
    priority: high
    deadline: 7days (개선대책 수립)

supplementary_docs:
  - photo_attachment_sheet
  - improvement_completion_check
```

#### Rule-09: 월간 정기 서류 (Phase 9)

```yaml
trigger: project.status == "진행중" && 
          today가 매월 1일 또는 지정된 교육일

timing: 매월 자동 알림 + 사용자 수동 생성

generated_forms:
  - form_id: education_log
    description: 정기 안전보건교육 일지 (월 2시간)
    priority: high
    repeat: monthly
    deadline: 매월 마지막 근무일
    
  - form_id: risk_assessment_meeting_minutes
    description: 위험성평가 참여 회의록
    priority: high
    repeat: monthly
    
  - form_id: safety_committee_minutes
    description: 안전보건협의체 회의록
    priority: medium
    repeat: monthly (필요 시)
    
  - form_id: ppe_management_checklist
    description: 보호구 지급 및 관리 점검표
    priority: high
    repeat: monthly
    
  - form_id: subcontractor_safety_evaluation
    description: 협력업체 안전보건 수준 평가표
    priority: medium
    repeat: monthly

supplementary_docs:
  - attendance_roster
  - ppe_receipt_confirmation
  - education_makeup_confirmation
```

#### Rule-10: 준공 전 최종 점검 (Phase 11~12)

```yaml
trigger: project.planned_end_date - 30days <= today <= 
          project.planned_end_date

timing: planned_end_date - 30days에 자동 알림

generated_forms:
  - form_id: safety_patrol_inspection_log
    description: 안전순찰 점검 일지 (전수 점검)
    priority: high
    deadline: planned_end_date - 14days
    
  - form_id: risk_assessment
    description: 위험성평가표 (마감 공종 재평가)
    priority: high
    deadline: planned_end_date - 7days
    
  - form_id: contractor_safety_document_checklist
    description: 협력업체 안전서류 최종 확인
    priority: high
    deadline: planned_end_date - 3days
    
  - form_id: risk_assessment_best_practice_report
    description: 위험성평가 우수 사례 보고서 (선택)
    priority: low
    deadline: planned_end_date

supplementary_docs:
  - improvement_completion_check
  - document_attachment_list
  - photo_attachment_sheet
```

### 4-2. 조건부 생성 로직

```yaml
# 공종별 작업계획서 자동 선택
work_type_to_forms:
  "토공굴착":
    - excavation_workplan
    - excavation_work_permit
    - fall_protection_checklist
  "기초파일":
    - piling_workplan
    - piling_use_workplan
  "골조거푸집":
    - formwork_shoring_workplan
    - formwork_shoring_installation_checklist
  "비계고소":
    - scaffold_installation_checklist
    - aerial_work_platform_use_plan
    - fall_protection_checklist
  "양중크레인":
    - heavy_lifting_workplan
    - lifting_equipment_workplan
    - tower_crane_workplan
    - tower_crane_self_inspection_checklist
  "전기화기":
    - electrical_workplan
    - electrical_work_permit
    - hot_work_workplan
    - hot_work_permit
  "설비소방":
    - confined_space_workplan
    - confined_space_permit
    - confined_space_checklist
    - special_health_examination

# 장비 종류별 자동 선택
equipment_type_to_forms:
  "타워크레인":
    - tower_crane_workplan
    - tower_crane_self_inspection_checklist
    - equipment_entry_application
    - equipment_insurance_inspection_check
    - construction_equipment_daily_checklist
  "이동식크레인":
    - mobile_crane_workplan
    - equipment_entry_application
    - equipment_insurance_inspection_check
    - construction_equipment_daily_checklist
  "덤프트럭":
    - vehicle_construction_workplan
    - construction_equipment_daily_checklist
  "하역기계":
    - material_handling_workplan
    - construction_equipment_daily_checklist
  "고소작업대":
    - aerial_work_platform_use_plan
    - construction_equipment_daily_checklist
```

---

## 5. 문서 패키지 구조

### 5-1. 패키지 구성

```
신축공사명_문서패키지_2026-04-29.zip
├── 📋 README.txt (패키지 설명 및 구성)
├── 📊 01_핵심서류 (90종)
│   ├── Phase_0_계약등록
│   │   ├── 안전관리자_선임_보고서.xlsx
│   │   └── 산업안전보건관리비_사용계획서.xlsx
│   ├── Phase_1_착공전_기본체계
│   │   ├── 안전보건_방침및목표_게시문.xlsx
│   │   ├── 위험성평가_실시규정.xlsx
│   │   ├── 연간_안전보건교육_계획서.xlsx
│   │   ├── 비상_연락망및대피_계획서.xlsx
│   │   ├── 협력업체_안전보건_관련서류_확인서.xlsx
│   │   ├── 도급용역_안전보건_협의서.xlsx
│   │   └── 협력업체_안전보건_수준_평가표.xlsx
│   ├── Phase_2_착공계제출
│   │   ├── 위험성평가표.xlsx
│   │   ├── 위험성평가_관리등록부.xlsx
│   │   └── 산업재해_발생현황_관리대장.xlsx
│   ├── Phase_3_근로자투입전
│   │   ├── 안전보건교육_교육일지_20260515.xlsx
│   │   ├── 신규근로자_안전보건_서약서.xlsx
│   │   ├── 보호구_지급대장.xlsx
│   │   ├── 보호구_지급및관리_점검표.xlsx
│   │   ├── 위험성평가_결과_근로자공지문.xlsx
│   │   ├── 근로자_건강진단_결과확인서.xlsx
│   │   └── MSDS_비치및교육_확인서.xlsx
│   ├── Phase_4_장비반입전
│   │   ├── 건설_장비_반입신청서.xlsx
│   │   ├── 건설_장비_보험정기검사증_확인서.xlsx
│   │   ├── 타워크레인_작업계획서.xlsx
│   │   ├── 이동식크레인_작업계획서.xlsx
│   │   ├── 차량계_건설기계_작업계획서.xlsx
│   │   ├── 건설장비_일일_사전점검표_20260515.xlsx
│   │   └── ... (반복 점검표)
│   ├── Phase_5_공종별착수전
│   │   ├── 5-1_토공굴착
│   │   │   ├── 굴착_작업계획서.xlsx
│   │   │   ├── 굴착_작업_허가서.xlsx
│   │   │   ├── 위험성평가표_굴착.xlsx
│   │   │   ├── 특별_안전보건교육_굴착.xlsx
│   │   │   └── 추락_방호설비_점검표.xlsx
│   │   ├── 5-2_기초파일
│   │   │   ├── 항타기항발기_사용계획서.xlsx
│   │   │   └── 항타기항발기_사용_작업계획서.xlsx
│   │   ├── ... (5-3 ~ 5-7 동일 구조)
│   ├── Phase_6_매일작업전
│   │   ├── TBM_안전점검_일지_20260515.xlsx
│   │   ├── 작업전_안전_확인서_20260515.xlsx
│   │   ├── 기상_조건기록_일지_20260515.xlsx
│   │   ├── 안전관리_일지_20260515.xlsx
│   │   └── 관리감독자_안전보건_업무일지_20260515.xlsx
│   ├── Phase_7_작업중종료
│   │   ├── 화기작업_허가서_20260517.xlsx
│   │   ├── 화기작업_감시인배치_확인서_20260517.xlsx
│   │   └── 화기작업_종료확인서_20260517.xlsx
│   ├── Phase_8_주간반복
│   │   ├── 위험성평가표_재평가_W1.xlsx
│   │   ├── 안전순찰_점검일지_W1.xlsx
│   │   └── ... (주차별 반복)
│   ├── Phase_9_월간반복
│   │   ├── 정기_안전보건교육_일지_M1.xlsx
│   │   ├── 위험성평가_참여회의록_M1.xlsx
│   │   ├── 보호구_지급및관리_점검표_M1.xlsx
│   │   └── ... (월차별 반복)
│   ├── Phase_10_사고발생
│   │   ├── [사고 미발생 시 생성 안 함]
│   │   ├── 응급조치_실시기록서_20260520.xlsx (사고 발생 시)
│   │   ├── 중대재해_발생_즉시보고서_20260520.xlsx (중대 재해 시)
│   │   └── 산업재해조사표_20260520.xlsx
│   ├── Phase_11_준공전30일
│   │   ├── 안전순찰_점검일지_최종.xlsx
│   │   ├── 위험성평가표_마감공종.xlsx
│   │   └── 협력업체_안전서류_최종확인.xlsx
│   └── Phase_12_준공보존
│       └── [준공 후 별도 보관]
│
├── 📑 02_부대서류 (10종)
│   ├── 참석자_명단_템플릿.xlsx (attendance_roster)
│   ├── 사진_첨부_탈지.xlsx (photo_attachment_sheet)
│   ├── 문서_목록_체크리스트.xlsx (document_attachment_list)
│   ├── 밀폐공간_가스측정_기록표.xlsx (confined_space_gas_measurement)
│   ├── 작업_종료_확인서_템플릿.xlsx (work_completion_confirmation)
│   ├── 개선조치_완료_확인서_템플릿.xlsx (improvement_completion_check)
│   ├── 장비_운전원자격_확인서_템플릿.xlsx (equipment_operator_qualification_check)
│   ├── 감시인_배치_확인서_템플릿.xlsx (watchman_assignment_confirmation)
│   ├── 보수교육_참석_확인서_템플릿.xlsx (education_makeup_confirmation)
│   └── 보호구_수령_확인서_템플릿.xlsx (ppe_receipt_confirmation)
│
├── 📜 03_첨부문서
│   ├── 법령_근거.txt (생성된 모든 서류의 법령 기준)
│   ├── 신축공사_일정_매트릭스.md (참고용)
│   ├── 생성_메타정보.json {
│   │   "project_id": "PRJ-2026-001",
│   │   "project_name": "신축공사명",
│   │   "generated_at": "2026-04-29T15:30:00+09:00",
│   │   "generated_by": "사용자이름",
│   │   "total_documents": 145,
│   │   "total_supplementary": 10,
│   │   "phase_coverage": "Phase 0 ~ Phase 12",
│   │   "document_manifest": [...]
│   │ }
│   └── 누락_서류_점검표.xlsx (생성되지 않은 옵션 서류 목록)
│
└── 📸 04_사진_첨부 (선택)
    ├── 착공전_현장사진_20260512.jpg
    ├── 근로자_교육_20260515.jpg
    └── ... (사진 대지)

```

### 5-2. 출력 포맷별 전략

#### Format 1: Excel (V1.1 필수)

```
- 각 Phase별 폴더 구조 유지
- 모든 서류는 .xlsx (openpyxl로 생성)
- 각 서류는 독립적인 파일
- ZIP으로 압축 제공
- 다운로드: ZIP 파일 또는 개별 파일
```

#### Format 2: PDF (V2.0 예정)

```
- 각 서류를 PDF로 변환 (openpyxl + pdf 라이브러리)
- 폴더 구조 유지하여 PDF 조직화
- 또는 단일 PDF로 모든 문서 바인딩 + 목차
- 서명란 PDF 폼 필드 지원 (후순위)
```

#### Format 3: ZIP (V1.1 필수)

```
- Excel + PDF 혼합 패키지
- 폴더 구조 그대로 압축
- 메타정보 JSON 포함
- 구성 파일 포함 (README.txt, 법령근거)
```

---

## 6. 화면 구성 (UI Mockup)

### 6-1. 대시보드 (Dashboard)

```
┌─────────────────────────────────────────────────────────────┐
│  🏢 신축공사 안전서류 자동생성 웹시스템                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ 진행 중인 공사 (3개)                                    │
│  │                                                          │
│  │  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │  │ 신축 A 빌딩          │  │ 신축 B 오피스        │    │
│  │  │ 진행 중: Phase 6     │  │ 진행 중: Phase 3     │    │
│  │  │ 진도: 45%            │  │ 진도: 25%            │    │
│  │  │ [상세] [서류생성]    │  │ [상세] [서류생성]    │    │
│  │  └──────────────────────┘  └──────────────────────┘    │
│  │                                                          │
│  ├─ 오늘 할 일 (5개)                                       │
│  │  ☐ TBM 안전점검 일지 (신축 A, 관리감독자)              │
│  │  ☐ 작업 전 안전 확인서 (신축 A)                        │
│  │  ☐ 근로자 2명 안전보건 교육 (신축 B)                   │
│  │  ⚠️  공종 '거푸집' 착수 D-3 (신축 A, 준비 필요)       │
│  │  ⚠️  건강진단 결과 확인 대기                           │
│  │                                                          │
│  ├─ 최근 생성 서류                                         │
│  │  • 안전보건교육 교육일지 (신축 B, 2026-04-28)         │
│  │  • 위험성평가표 (신축 A, 2026-04-27)                  │
│  │                                                          │
│  └─ [신규 공사 등록] 버튼                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6-2. 공사 상세 페이지 (Project Detail)

```
┌─────────────────────────────────────────────────────────────┐
│  📋 신축 A 빌딩 공사 (PRJ-2026-001)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [기본정보] [공종일정] [근로자] [장비] [서류] [통계]        │
│                                                              │
│  ┌─ 기본정보 탭                                            │
│  │                                                          │
│  │  공사명: 신축 A 빌딩                                    │
│  │  공사 위치: 서울시 강남구 테헤란로                     │
│  │  발주자: OO 개발                                       │
│  │  시공사: OO 건설                                       │
│  │  공사금액: ₩100,000,000,000                            │
│  │                                                          │
│  │  예정 착공: 2026-05-01                                 │
│  │  실제 착공: 2026-04-28 ✓                              │
│  │  예정 준공: 2026-11-30                                 │
│  │                                                          │
│  │  현황: Phase 6 (진행 중) / 진도 45%                   │
│  │                                                          │
│  │  근로자 현황:
│  │  • 총 근로자: 120명
│  │  • 정규: 30명, 협력: 90명
│  │  • 투입 완료: 87명 (72%)
│  │                                                          │
│  │  ┌──────────────────────────────────────────┐          │
│  │  │ [기본정보 수정] [Phase 변경] [서류생성]    │          │
│  │  └──────────────────────────────────────────┘          │
│  │                                                          │
│  └─ 공종일정 탭                                            │
│     공종별 착수일 입력 → 자동 서류 생성 제안               │
│     - 토공굴착: 2026-05-15 (D-5)                           │
│     - 기초파일: 2026-05-20                                 │
│     - 거푸집: 2026-06-05 (D-3, ⚠️ 서류 준비 필요)       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6-3. 오늘 할 일 (Today's Tasks)

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ 오늘 할 일 (2026-04-29)                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📌 필수 작성                                               │
│  ☐ TBM 안전점검 일지                                      │
│    프로젝트: 신축 A 빌딩                                   │
│    [작성시작] [최근 작성 불러오기]                        │
│                                                              │
│  ☐ 작업 전 안전 확인서                                    │
│    프로젝트: 신축 A 빌딩                                   │
│    [작성시작]                                             │
│                                                              │
│  ☐ 안전관리 일지                                         │
│    프로젝트: 신축 A 빌딩                                   │
│    [작성시작]                                             │
│                                                              │
│  ──────────────────────────────────────────────────────────│
│                                                              │
│  ⚠️  주의 사항                                              │
│  • 공종 '거푸집' 착수 D-3: 작업계획서 등 준비 필요        │
│    [거푸집 서류 생성]                                     │
│                                                              │
│  • 협력업체 '새로운 팀' 안전교육 미완료                   │
│    [교육 일지 작성]                                       │
│                                                              │
│  ──────────────────────────────────────────────────────────│
│                                                              │
│  📋 참고: 준공이 215일 남았습니다.                          │
│           위험성평가 재실시 예정일: 2026-05-10            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6-4. 서류 생성 마법사 (Document Generation Wizard)

```
┌─────────────────────────────────────────────────────────────┐
│  📄 서류 생성 마법사 (신축 A 빌딩)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 생성 유형 선택                                    │
│  ┌──────────────────────────────────────────┐             │
│  │ ◉ 자동 제안 서류 (Phase 기반)            │             │
│  │ ○ 특정 Phase 선택                         │             │
│  │ ○ 특정 공종 선택                         │             │
│  │ ○ 특정 근로자/장비 선택                  │             │
│  │ ○ 사고 발생 보고                         │             │
│  │ ○ 커스텀 선택                           │             │
│  └──────────────────────────────────────────┘             │
│                                                              │
│  Step 2: 자동 제안 서류 확인                               │
│  ┌──────────────────────────────────────────┐             │
│  │ 현재 진행 Phase: 6 (매일 작업 전)         │             │
│  │                                          │             │
│  │ ☑ TBM 안전점검 일지                     │             │
│  │ ☑ 작업 전 안전 확인서                   │             │
│  │ ☑ 기상 조건 기록 일지                   │             │
│  │ ☑ 안전관리 일지                        │             │
│  │ ☑ 관리감독자 안전보건 업무 일지         │             │
│  │                                          │             │
│  │ 부대서류:                                │             │
│  │ ☑ 참석자 명단                          │             │
│  │ ☑ 사진 첨부 대지                       │             │
│  │                                          │             │
│  │ 총 7개 서류 생성 예정                   │             │
│  └──────────────────────────────────────────┘             │
│                                                              │
│  Step 3: 출력 형식 선택                                    │
│  ┌──────────────────────────────────────────┐             │
│  │ ☑ Excel (.xlsx)                         │             │
│  │ ☐ PDF (.pdf)                           │             │
│  │ ☑ ZIP (모두 압축)                       │             │
│  │                                          │             │
│  │ ☐ 생성 후 이메일로 전송                │             │
│  │ ☑ 클라우드에 자동 저장                 │             │
│  └──────────────────────────────────────────┘             │
│                                                              │
│  [이전] [생성 시작]                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6-5. 서류 생성 결과 및 다운로드 (Download)

```
┌─────────────────────────────────────────────────────────────┐
│  ✓ 서류 생성 완료!                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  생성 완료: 2026-04-29 15:35 (45초 소요)                   │
│  생성된 서류: 7개                                          │
│                                                              │
│  ┌─ 다운로드 옵션                                         │
│  │                                                          │
│  │  📦 패키지 다운로드                                    │
│  │  ┌──────────────────────────────────────┐             │
│  │  │ 신축A_서류패키지_20260429.zip (15MB)  │             │
│  │  │ [다운로드]                           │             │
│  │  │ 또는 [클라우드 링크 복사]             │             │
│  │  └──────────────────────────────────────┘             │
│  │                                                          │
│  │  📄 개별 다운로드                                      │
│  │  ✓ TBM_안전점검_일지_20260429.xlsx (250KB)            │
│  │    [다운로드] [미리보기]                              │
│  │  ✓ 작업전_안전_확인서_20260429.xlsx (180KB)          │
│  │    [다운로드] [미리보기]                              │
│  │  ✓ ... (5개 더)                                       │
│  │                                                          │
│  │  [모두 선택] [선택 다운로드]                           │
│  │                                                          │
│  └─ 공유 옵션                                            │
│     [이메일로 전송] (수신자: __________@_____)          │
│     [카톡 공유] [링크 복사]                              │
│                                                              │
│  ┌─ 생성된 서류 목록                                      │
│  │                                                          │
│  │  서류명                        | 파일크기 | 상태      │
│  │  ─────────────────────────────┼──────────┼─────────  │
│  │  TBM 안전점검 일지            │ 250KB   │ ✓ 완료   │
│  │  작업 전 안전 확인서           │ 180KB   │ ✓ 완료   │
│  │  기상 조건 기록 일지           │ 150KB   │ ✓ 완료   │
│  │  안전관리 일지                │ 200KB   │ ✓ 완료   │
│  │  관리감독자 안전보건 업무일지 │ 220KB   │ ✓ 완료   │
│  │  참석자 명단                   │ 80KB    │ ✓ 완료   │
│  │  사진 첨부 대지                │ 100KB   │ ✓ 완료   │
│  │                                                        │
│  └─ 추가 작업                                            │
│     [기존 서류 편집] [서류 추가 생성] [패키지 재생성]  │
│     [보관함에 저장] [인쇄]                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6-6. 누락 서류 점검 (Missing Documents Checker)

```
┌─────────────────────────────────────────────────────────────┐
│  🔍 누락 서류 점검표 (신축 A 빌딩)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  현재 Phase: 6 (진행 중)                                   │
│  점검 기준: 1 Phase 뒤처지면 경고 / 2 Phase 이상 = 경고  │
│                                                              │
│  ┌─ Phase별 필수 서류 완성도                              │
│  │                                                          │
│  │  ✓ Phase 0 (계약 등록) — 100% (2/2)                  │
│  │    ☑ 안전관리자 선임 보고서 (2026-04-20)            │
│  │    ☑ 산업안전보건관리비 사용계획서 (2026-04-20)     │
│  │                                                          │
│  │  ✓ Phase 1 (착공 전) — 100% (7/7)                   │
│  │    ☑ 안전보건 방침 및 목표 (2026-04-22)            │
│  │    ☑ 위험성평가 실시규정 (2026-04-22)              │
│  │    ☑ ... (5개 더)                                    │
│  │                                                          │
│  │  ✓ Phase 2 (착공계) — 100% (3/3)                    │
│  │    ☑ 위험성평가표 (2026-04-28)                      │
│  │    ☑ 위험성평가 관리등록부 (2026-04-28)            │
│  │    ☑ 산업재해 발생현황 관리대장 (2026-04-28)       │
│  │                                                          │
│  │  ✓ Phase 3 (근로자 투입 전) — 85% (6/7)            │
│  │    ☑ 안전보건교육 교육일지 (2026-04-28)            │
│  │    ☑ 신규근로자 안전보건 서약서 (2026-04-28)       │
│  │    ☑ 보호구 지급대장 (2026-04-28)                  │
│  │    ☐ 보호구 지급 및 관리 점검표 (⚠️  미작성)       │
│  │      [작성하기] [7일 유예 요청]                      │
│  │    ☑ ... (3개 더)                                    │
│  │                                                          │
│  │  ✓ Phase 4 (장비 반입 전) — 100% (N/A, 장비 미반입) │
│  │                                                          │
│  │  ✓ Phase 5 (공종별 착수) — 0% (아직 진행 전)        │
│  │    예정: 2026-05-15 (거푸집 착수)                   │
│  │                                                          │
│  │  ✓ Phase 6 (매일 작업) — 100% (5/5)                │
│  │    ☑ TBM 안전점검 일지 (2026-04-29)               │
│  │    ☑ 작업 전 안전 확인서 (2026-04-29)              │
│  │    ☑ ... (3개 더)                                   │
│  │                                                          │
│  │  ✓ Phase 7~12 (작업 중 ~ 준공) — 0% (미해당)       │
│  │                                                          │
│  └─ 종합 평가                                            │
│     ✅ 현재까지 누락 서류 0건                             │
│     ⚠️  주의 필요: Phase 3 보호구 점검표 (D-2)          │
│     📅 향후 주의: Phase 5 공종별 서류 (D-3부터)         │
│                                                              │
│     [누락 서류 자동 생성] [상세 보고서 다운로드]         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. API 설계

### 7-1. REST API 엔드포인트

```
[공사 관리]
POST   /api/v1/projects
GET    /api/v1/projects
GET    /api/v1/projects/{project_id}
PUT    /api/v1/projects/{project_id}
PATCH  /api/v1/projects/{project_id}/phase

[공종 일정]
GET    /api/v1/projects/{project_id}/work-schedules
POST   /api/v1/projects/{project_id}/work-schedules
PUT    /api/v1/projects/{project_id}/work-schedules/{schedule_id}

[근로자 관리]
GET    /api/v1/projects/{project_id}/workers
POST   /api/v1/projects/{project_id}/workers
GET    /api/v1/projects/{project_id}/workers/{worker_id}

[장비 관리]
GET    /api/v1/projects/{project_id}/equipment
POST   /api/v1/projects/{project_id}/equipment
PUT    /api/v1/projects/{project_id}/equipment/{equipment_id}

[서류 생성]
POST   /api/v1/projects/{project_id}/documents/generate
GET    /api/v1/projects/{project_id}/documents/pending
GET    /api/v1/projects/{project_id}/documents/generated
GET    /api/v1/documents/{document_id}/download

[패키지 생성]
POST   /api/v1/projects/{project_id}/packages/generate
GET    /api/v1/projects/{project_id}/packages/{package_id}
GET    /api/v1/packages/{package_id}/download

[대시보드]
GET    /api/v1/projects/{project_id}/dashboard
GET    /api/v1/projects/{project_id}/today-tasks
GET    /api/v1/projects/{project_id}/missing-documents
```

### 7-2. 자동생성 엔진 API (내부)

```
[트리거 감지]
POST   /api/internal/triggers/detect
  입력: trigger_type, trigger_detail, project_id
  출력: recommended_forms, supplementary_docs

[문서 생성 파이프라인]
POST   /api/internal/documents/batch-generate
  입력: form_ids, supplementary_ids, project_id, metadata
  출력: job_id, status, progress

[패키지 생성 파이프라인]
POST   /api/internal/packages/generate
  입력: document_ids, format, project_id
  출력: package_id, download_url
```

---

## 8. V1.1 구현 범위

### 8-1. V1.1 목표

신축공사 기준 **공사 등록 → 일정 선택 → 서류 생성 → Excel 다운로드** 까지 구현 완료

### 8-2. V1.1 범위

| 항목 | 포함 | 비포함 | 사유 |
|-----|------|--------|------|
| **공사 등록** | ✅ | — | 기본 필수 |
| **공종 일정 입력** | ✅ | — | 자동생성 트리거의 핵심 |
| **근로자 등록** | ✅ | — | 자동생성 트리거의 핵심 |
| **장비 등록** | ✅ | — | 자동생성 트리거의 핵심 |
| **자동 서류 제안** | ✅ | — | 핵심 기능 |
| **서류 생성** | ✅ | — | 핵심 기능 |
| **Excel 출력** | ✅ | — | V1.1 우선 |
| **ZIP 패키지** | ✅ | — | 다운로드 편의 |
| **PDF 출력** | — | ✅ | V2.0 이후 |
| **모바일** | — | ✅ | V2.0 이후 (조회/서명만) |
| **서명 기능** | — | ✅ | V3.0 (디지털 서명) |
| **클라우드 협업** | — | ✅ | V2.0 이후 |
| **AI 자동 추천** | — | ✅ | V3.0 이후 |

### 8-3. V1.1 핵심 기능

```yaml
1_공사_관리:
  - 공사 기본정보 입력 (공사명, 위치, 발주자, 시공사)
  - 예정 착공/준공 일정 입력
  - 안전관리자 지정
  - 공사 Phase 관리 (자동 또는 수동)

2_공종_일정:
  - 공종 목록 (토공, 파일, 거푸집, 비계, 양중, 전기, 설비)
  - 공종별 착수 예정일 입력
  - 위험도 입력
  - 자동 서류 제안 (공종 선택 시)

3_근로자_관리:
  - 근로자 기본정보 입력 (이름, 유형, 역할)
  - 투입 예정일 입력
  - 자격증 정보 입력
  - 자동 서류 제안 (투입 전)

4_장비_관리:
  - 장비 종류 선택
  - 운전원 정보 입력
  - 반입 예정일 입력
  - 보험·검사 정보 입력
  - 자동 서류 제안 (반입 전)

5_서류_생성:
  - 자동 제안 서류 목록 표시
  - 서류 선택 (필수/선택 분류)
  - Excel 형식 생성 (openpyxl 활용)
  - ZIP 패키지 생성
  - 다운로드 또는 이메일 전송

6_대시보드:
  - 공사 진행도 표시
  - 오늘 할 일 (TBM, 작업 전 안전)
  - 마감 임박 서류 경고
  - 누락 서류 체크리스트

7_API:
  - REST API (공사, 공종, 근로자, 장비, 서류, 패키지)
  - 내부 자동생성 엔진
```

### 8-4. V1.1 기술 스택

```yaml
백엔드:
  - Python 3.10+
  - FastAPI (REST API)
  - PostgreSQL (데이터베이스)
  - openpyxl (Excel 생성, 기존 완성)
  - APScheduler (자동 알림 스케줄링)
  - Celery (백그라운드 작업)

프론트엔드:
  - React 18+
  - TypeScript
  - Tailwind CSS
  - SWR 또는 React Query (데이터 페칭)
  - Zustand (상태관리)

인프라:
  - Docker + Docker Compose
  - AWS S3 (파일 저장)
  - Redis (캐싱 & 작업 큐)
  - GitHub Actions (CI/CD)
```

---

## 9. V2.0 이후 로드맵

### 9-1. V2.0 (6~12개월 후)

```yaml
새로운_기능:
  - PDF 출력 지원 (pypdf2, reportlab)
  - 반복 서류 자동화 (매일 TBM, 월간 교육)
  - 사고 발생 시 긴급 문서 생성 (자동 알림 포함)
  - 문서 온라인 편집 (web-based form)
  - 디지털 서명 (기본 구현)
  - 모바일 앱 (조회/조인)

UI_개선:
  - 반응형 웹 디자인 (모바일 최적화)
  - 타임라인 뷰 (공사 진행도 시각화)
  - 문서 미리보기 (PDF/Excel 즉시 표시)
  - 다국어 지원 (영어 기본, 중국어/베트남어 후속)

데이터_연동:
  - HAEHAN 중앙 DB 연동 (회사별 근로자, 협력업체 정보)
  - 정부 신청 자동화 (근로자 신청 DB 연동)
  - 건설사 ERP 연동 (공정 정보 자동 동기화)

분석:
  - 안전 통계 대시보드 (재해율, 위험요소 분포)
  - AI 기반 위험요소 자동 추천
  - 보고서 자동 생성 (월간/분기)
```

### 9-2. V3.0 (12~24개월 후)

```yaml
혁신_기능:
  - AI 자동 서류 검수 (OCR + 머신러닝)
  - 클라우드 협업 (실시간 공동편집, 댓글)
  - IoT 센서 연동 (현장 온도, 소음, 진동 자동 기록)
  - 실시간 알림 (위험 상황 감지 시 즉시 알림)
  - 비디오 회의 통합 (TBM을 온라인으로 진행)

확장_범위:
  - 리모델링 프로젝트 지원
  - 철거·해체 프로젝트 지원
  - 설비 보수 및 유지보수 지원
  - 외국인 근로자 다국어 서류
  - 소방감리 전용 서류

통합:
  - 정부 포털 자동 제출 (고용부, 지자체)
  - SNS 공유 (현장 뉴스, 안전 정보 자동 게시)
  - 보험사 청구 자동화 (재해 정보 기반)
  - 건설사 협력사 평가 자동화
```

---

## 마무리

본 설계 문서는 신축공사 안전서류 자동생성 웹 시스템의 **기능 설계안**이며, 구현 코드는 포함하지 않습니다.

설계 원칙:
- ✅ 기존 90종 핵심서류 + 10종 부대서류만 활용
- ✅ 신규 builder 생성 금지 (기존 완성도 유지)
- ✅ 신축공사 범위만 다룸 (리모델링, 외국인용 제외)
- ✅ V1.1은 Excel 출력 중심 (PDF는 V2.0 이후)

**다음 단계**: 본 설계안을 바탕으로 백엔드 API 및 프론트엔드 구현 시작

---

**설계 완성일**: 2026-04-29  
**설계자**: Claude Code (Sonnet 4.6)  
**검수**: 신축공사 안전서류 자동생성 프로젝트팀
