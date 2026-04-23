# Form Risk Mapping Rule (v1)

**대상**: `engine/kras_connector/form_builder.py` 의 `current_risk`/`residual_risk` → 본표 2축 역산
**기준 서식**: 공식 본표 (3×3 곱셈식)
**원칙**: 결정론적 변환. 임의 보정 금지. 다른 수치 체계 혼합 금지.

---

## 1. current_risk 역산 (입력 → 가능성 × 중대성)

`table_builder` 출력의 `current_risk` 는 3단계 label(High/Medium/Low). 본표는 `probability × severity` 2축 (각 1~3 정수)을 요구.

### 매핑 (v1 고정)

| 입력 `current_risk` | `probability` (빈도) | `severity` (강도) | `risk_level` = p × s | `risk_band` |
|-------------------|-------------------|-----------------|----------------------|-------------|
| `High`   | **3** (상) | **3** (대) | **9** | `critical` |
| `Medium` | **2** (중) | **3** (대) | **6** | `high` |
| `Low`    | **2** (중) | **2** (중) | **4** | `medium` |

### 근거

- **severity 를 High 에서 3 으로 고정**: `High` level 은 엔진 DB에서 `confidence_score ≥ 0.9` 에 해당하며, 이는 산안기준규칙에 **직접 명시된** 중대성 큰 hazard 임을 뜻함. severity=3 (대) 가 보수적 정위치.
- **Medium 이 severity=3 인 이유**: 실무상 Medium 도 중대성이 작지 않은 사고(휴업/중상)로 이어지는 경우가 더 많아 severity=3 이 적합. probability 만 1 단계 낮춘 2×3=6 으로 배치.
- **Low 는 2×2**: 평가 대상이 된 시점에서 severity=1 (단순 응급처치 수준)은 드물다. Low 조차 최소 2×2=4 (medium band) 로 설정해 과소평가 방지.

### 주의 (감사 대응)

- 이 매핑은 **정보 손실 역산**이다. 감독관이 각 축의 근거를 요청하면 v1.1 에서 추가될 `probability_hint`/`severity_hint` DB 컬럼으로 뒷받침해야 함.
- 매핑 자체는 `form_risk_mapping_rule.md` (이 문서) 로 정당화. 현장 제출 시 이 문서를 첨부 가능.

---

## 2. residual_risk 역산 (조치 후 2축)

`table_builder` 출력 `residual_risk` 는 level 1단계 감소 결과(High→Medium, Medium→Low, Low→Low).

### 매핑 (v1 고정)

| 입력 `current_risk` / `residual_risk` | `residual_probability` | `residual_severity` | `residual_risk_level` | `residual_risk_band` |
|-----------------------------------|---------------------|-------------------|----------------------|----------------------|
| High / Medium | **2** | **3** | **6** | `high` |
| Medium / Low  | **1** | **3** | **3** | `medium` |
| Low / Low     | **2** | **2** | **4** | `medium` |

### 근거

- **severity 는 조치로 감소하지 않는다**: 사고가 일어났을 때 부상·질병의 중대성은 hazard 고유의 물리적 속성. 개선대책(안전보호구·표지·교육)은 주로 **발생 가능성(probability)** 을 낮춘다.
  - 예외: 대체 공법·공정 변경 등 hazard 자체를 제거하는 조치는 severity 도 낮출 수 있으나, v1 에서는 다루지 않음 (정보 부족).
- **Low / Low 케이스**: probability 감소 여지가 없다고 판단 (이미 2=중 으로 낮음). 변화 없이 유지.
- **residual band**: 계산된 `residual_risk_level` 로 `scale_definition.risk_bands` 기준 재부여.

---

## 3. 구현 의사코드

```python
LEVEL_TO_PS = {"High": (3, 3), "Medium": (2, 3), "Low": (2, 2)}

def current(level_label):
    p, s = LEVEL_TO_PS[level_label]
    return p, s, p * s, _band(p * s)

def residual(current_label, residual_label):
    p, s = LEVEL_TO_PS[current_label]
    if current_label == "Low":
        rp, rs = p, s          # 변화 없음
    else:
        rp, rs = max(1, p - 1), s
    return rp, rs, rp * rs, _band(rp * rs)

def _band(level):
    if level >= 9: return "critical"
    if level >= 6: return "high"
    if level >= 3: return "medium"
    return "low"
```

---

## 4. 금지 사항

- 위 표 외 임의 수치 매핑 금지.
- severity 를 조치 기반으로 낮추는 경우 금지 (v1).
- 가중치·스무딩·보간 계산 추가 금지.
- 4×4 또는 다른 척도 혼합 금지.

---

## 5. 변경 계획

| 버전 | 계획 |
|------|------|
| v1 (현재) | 3단계 역산 표 고정 |
| v1.1 | DB `probability_hint`/`severity_hint` 컬럼 기반 분해 근거 보강 |
| v2   | 4×4·체크리스트 방식 지원 |
