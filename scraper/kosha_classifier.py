"""
KOSHA 공종 분류기 (규칙 기반 v2.0)
- 모든 chunk에 반드시 1개의 trade_type 부여
- 기타/미분류/unknown/null 금지
- candidate_trades: 복수 후보 점수 저장
- v2.0: equipment / location / ppe / law_ref 세부 분류 추가
"""
import re, json, psycopg2, psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from logger import get_classifier_logger, get_run_logger

load_dotenv(Path(__file__).parent / '.env')

log  = get_classifier_logger()
rlog = get_run_logger('classifier')

DB_HOST = '127.0.0.1'
DB_PORT = 5435
DB_NAME = 'common_data'
DB_USER = 'common_admin'
DB_PASS = 'XenZ5xmKw5jEf1bWQuU2LxWRZMlJ'

RULE_VERSION = 'v2.0'


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


# ── 공종 사전 ────────────────────────────────────────────────────────────────
# 각 trade: [주요 키워드, ...]
# 키워드가 많을수록 더 구체적인 공종으로 간주

TRADE_KEYWORDS: dict[str, list[str]] = {
    '가설':       ['가설', '가시설', '임시', '가설도로', '가설울타리', '가설창고', '가설전기', '가설수도'],
    '비계':       ['비계', '비계작업', '강관비계', '시스템비계', '외부비계', '달비계', '이동식비계', '틀비계', '비계해체'],
    '철골':       ['철골', '철골공사', '철골설치', '철골조립', '철골용접', '형강', 'H빔', '앵글', '철골구조'],
    '거푸집':     ['거푸집', '거푸집공사', '폼', '유로폼', '알폼', '합판거푸집', '동바리', '거푸집해체', '슬래브폼'],
    '콘크리트':   ['콘크리트', '타설', '레미콘', '양생', '콘크리트타설', '펌프카', '거푸집타설', '슬럼프', '배근', '철근배근'],
    '조적':       ['조적', '벽돌', '블록', '시멘트벽돌', 'ALC', '조적공사', '벽돌쌓기', '블록쌓기'],
    '미장':       ['미장', '미장공사', '시멘트모르타르', '레미탈', '미장작업', '바름'],
    '방수':       ['방수', '방수공사', '도막방수', '시트방수', '아스팔트방수', '우레탄방수', '방수시트', '방수제'],
    '타일':       ['타일', '타일공사', '타일붙임', '타일시공', '세라믹타일', '석재타일'],
    '석공':       ['석공', '석재', '대리석', '화강석', '석재시공', '석재설치', '석공사'],
    '금속':       ['금속', '금속공사', '스테인레스', '알루미늄', '메탈', '금속창호', '루버'],
    '창호':       ['창호', '창호공사', '창문', '문', '도어', '새시', '커튼월', '유리문', '창호설치'],
    '유리':       ['유리', '유리공사', '판유리', '강화유리', '접합유리', '복층유리', '유리설치'],
    '도장':       ['도장', '도장공사', '페인트', '도료', '스프레이도장', '롤러도장', '방청도장', '외벽도장'],
    '내장':       ['내장', '내장공사', '내부마감', '인테리어', '천정', '칸막이', '석고보드', '경량칸막이'],
    '천장':       ['천장', '천장공사', '천장마감', '천장패널', '천장재', 'T바', '암면천장'],
    '바닥':       ['바닥', '바닥공사', '바닥마감', '에폭시', '폴리싱', '온돌', '바닥재', '바닥타일'],
    '철거':       ['철거', '해체', '철거공사', '건물철거', '구조물철거', '콘크리트철거', '철거작업', '해체공사'],
    '토공':       ['토공', '토공사', '절토', '성토', '다짐', '토사', '토량', '토사운반', '성토작업'],
    '굴착':       ['굴착', '굴착공사', '굴착작업', '터파기', '지반굴착', '암반굴착', '굴삭기', '굴착기'],
    '흙막이':     ['흙막이', '흙막이공사', 'H파일', '흙막이벽', '앵커', '어스앵커', '버팀보', '띠장', '토류판'],
    '기초':       ['기초', '기초공사', '말뚝', '파일', '기초터파기', '매트기초', '독립기초', '연속기초', 'PHC파일'],
    '도로포장':   ['도로포장', '아스팔트', '포장공사', '아스콘', '도로', '포장', '보도블록', '콘크리트포장'],
    '상하수도':   ['상수도', '하수도', '상하수도', '배수관', '오수관', '우수관', '관로', '맨홀', '상수관'],
    '조경':       ['조경', '조경공사', '식재', '수목', '잔디', '수목식재', '조경시설'],
    '전기':       ['전기', '전기공사', '배선', '전선', '전력', '수변전', '케이블', '전기설비', '조명', '배전반', '분전함', '차단기'],
    '통신':       ['통신', '통신공사', '통신설비', '약전', '랜', '광케이블', '통신배선', '방송설비', 'UTP'],
    '소방기계':   ['소방기계', '소방배관', '스프링클러', '소화배관', '소화설비', '소화전', '포소화', '소화기설치'],
    '소방전기':   ['소방전기', '수신기', '감지기', '발신기', '소방배선', '비상조명', '유도등', '방재'],
    '배관':       ['배관', '배관공사', '파이프', '배관설치', '배관작업', '밸브', '플랜지', '배관용접'],
    '냉난방':     ['냉난방', '냉방', '난방', '에어컨', '보일러', '냉온수', 'FCU', '히트펌프', '냉매'],
    '공조덕트':   ['공조', '덕트', '공조덕트', '환기', '공조설비', '덕트설치', 'AHU', '팬코일', '취출구'],
    '위생설비':   ['위생', '위생설비', '위생기구', '변기', '세면대', '욕조', '급수', '급탕', '배수트랩'],
    '승강기':     ['승강기', '엘리베이터', '에스컬레이터', '리프트', '승강기설치', '곤돌라'],
    '기계설비':   ['기계설비', '기계실', '기계', '펌프', '압축기', '냉각탑', '기계장치', '설비'],
    '용접':       ['용접', '용접작업', '아크용접', '가스용접', 'CO2용접', 'TIG용접', '용접봉', '용접불꽃'],
    '절단':       ['절단', '절단작업', '가스절단', '플라즈마절단', '그라인더', '절단기', '절삭'],
    '운반':       ['운반', '운반작업', '자재운반', '수동운반', '물자운반', '운반기기'],
    '양중':       ['양중', '양중작업', '인양', '권양기', '윈치', '체인블록', '호이스트'],
    '크레인':     ['크레인', '타워크레인', '이동식크레인', '천장크레인', '크레인작업', '인양작업', '리프팅'],
    '지게차':     ['지게차', '지게차작업', '포크리프트', '지게차운전'],
    '밀폐공간작업': ['밀폐공간', '맨홀작업', '탱크내부', '밀폐구역', '산소결핍', '유해가스', '지하탱크'],
    '고소작업':   ['고소작업', '고소', '작업발판', '고소작업대', '사다리', '이동식사다리', '안전대', '추락방지'],
    '해체':       ['해체', '해체작업', '건물해체', '슬래브해체', '벽체해체', '해체장비'],
    '점검':       ['점검', '점검작업', '안전점검', '정기점검', '일상점검', '설비점검'],
    '유지보수':   ['유지보수', '보수', '수선', '유지관리', '수리', '보수작업', '유지'],
    '청소':       ['청소', '청소작업', '청소용역', '세척', '고압세척', '외벽청소'],
}

# ── 동의어 사전 ──────────────────────────────────────────────────────────────
# 실제 텍스트에 나오는 표현 → 정규 공종명
SYNONYMS: dict[str, str] = {
    # 소방
    '소화배관':     '소방기계',
    '소화전':       '소방기계',
    '스프링클러':   '소방기계',
    '소방헤드':     '소방기계',
    '수신기':       '소방전기',
    '감지기':       '소방전기',
    '발신기':       '소방전기',
    '비상방송':     '소방전기',
    '유도등':       '소방전기',
    # 공조
    '덕트설치':     '공조덕트',
    '덕트공사':     '공조덕트',
    '환기설비':     '공조덕트',
    # 전기
    '전기배선':     '전기',
    '전기배관':     '전기',
    '케이블트레이': '전기',
    '분전반':       '전기',
    '차단기':       '전기',
    # 배관
    '압력배관':     '배관',
    '소방배관':     '소방기계',
    '위생배관':     '위생설비',
    '냉온수배관':   '냉난방',
    # 고소
    '안전대':       '고소작업',
    '사다리작업':   '고소작업',
    '비계작업':     '비계',
    # 굴착/토공
    '굴삭기작업':   '굴착',
    '터파기작업':   '굴착',
    '토사작업':     '토공',
    # 크레인/양중
    '크레인인양':   '크레인',
    '타워크레인':   '크레인',
    '이동식크레인': '크레인',
    '체인블록':     '양중',
    # 기타
    '철골용접':     '철골',
    '배관용접':     '배관',
    '구조물용접':   '용접',
}

# ── 장비 사전 ────────────────────────────────────────────────────────────────
EQUIPMENT_KW: dict[str, list[str]] = {
    '타워크레인':   ['타워크레인', 'tower crane'],
    '이동식크레인': ['이동식크레인', '유압크레인', 'mobile crane', '트럭크레인'],
    '천장크레인':   ['천장크레인', '오버헤드크레인', 'overhead crane'],
    '지게차':       ['지게차', '포크리프트', 'forklift'],
    '고소작업대':   ['고소작업대', '스카이차', '시저리프트', '붐리프트', '고소차'],
    '굴삭기':       ['굴삭기', '굴착기', '포클레인', 'excavator'],
    '불도저':       ['불도저', '도저'],
    '덤프트럭':     ['덤프트럭', '덤프차'],
    '롤러':         ['롤러', '로드롤러', '진동롤러', '탬핑롤러'],
    '항타기':       ['항타기', '파일드라이버', '말뚝박기'],
    '그라인더':     ['그라인더', '앵글그라인더', '디스크그라인더'],
    '전동드릴':     ['전동드릴', '충전드릴', '임팩트드릴'],
    '용접기':       ['용접기', '아크용접기', 'TIG용접기', 'CO2용접기', '가스용접기', '인버터용접기'],
    '절단기':       ['절단기', '가스절단기', '플라즈마절단기', '전동절단기', '원형톱', '전기톱'],
    '공기압축기':   ['컴프레서', '공기압축기', '에어컴프레서'],
    '콘크리트펌프': ['콘크리트펌프', '펌프카', '붐펌프'],
    '호이스트':     ['호이스트', '체인블록', '전기호이스트', '체인호이스트'],
    '곤돌라':       ['곤돌라', '달비계곤돌라'],
    '컨베이어':     ['컨베이어', '벨트컨베이어'],
    '프레스':       ['프레스', '유압프레스', '전동프레스', '기계프레스'],
    '선반':         ['선반', 'CNC선반'],
    '밀링':         ['밀링', 'CNC밀링', '머시닝센터'],
    '리프트':       ['리프트', '건설용리프트', '화물리프트'],
}

# ── 위치 사전 ────────────────────────────────────────────────────────────────
LOCATION_KW: dict[str, list[str]] = {
    '고소':       ['고소', '상부', '고층', '고공'],
    '지붕':       ['지붕', '옥상', '지붕층'],
    '지하':       ['지하', '지하층', '지하실', '지하공간'],
    '개구부':     ['개구부', '홀', '피트'],
    '비계':       ['비계위', '비계상부', '발판위'],
    '사다리':     ['사다리', '이동식사다리', '고정사다리'],
    '밀폐공간':   ['밀폐공간', '탱크내부', '맨홀', '피트', '저장탱크내부'],
    '도로변':     ['도로', '차도', '교통구역', '도로변'],
    '터널':       ['터널', '갱도', '터널내부'],
    '외벽':       ['외벽', '외부', '외장', '외면'],
    '기계실':     ['기계실', '전기실', '펌프실'],
}

# ── 보호구 사전 ──────────────────────────────────────────────────────────────
PPE_KW: dict[str, list[str]] = {
    '안전모':     ['안전모', '헬멧', '안전헬멧'],
    '안전대':     ['안전대', '하네스', '추락방지대', '안전벨트'],
    '안전화':     ['안전화', '안전장화', '안전부츠'],
    '보안경':     ['보안경', '안전안경', '고글', '차광안경', '용접면'],
    '방진마스크': ['방진마스크', '방진', '먼지마스크', 'N95'],
    '방독마스크': ['방독마스크', '방독', '화학마스크', '방독면'],
    '귀마개':     ['귀마개', '귀덮개', '청력보호구'],
    '안전장갑':   ['안전장갑', '장갑', '용접장갑', '방열장갑'],
    '절연장갑':   ['절연장갑', '절연복', '절연화', '내전압'],
    '안전조끼':   ['안전조끼', '반사조끼', '형광조끼', '경고조끼'],
    '방열복':     ['방열복', '방화복', '내열복', '방염복'],
    '방수복':     ['방수복', '우의', '방수장화'],
}

# ── 법령 패턴 ────────────────────────────────────────────────────────────────
LAW_PATTERNS = [
    (r'산업안전보건법\s*제?\s*\d+조', '산업안전보건법'),
    (r'산업안전보건기준에\s*관한\s*규칙\s*제?\s*\d+조', '안전보건규칙'),
    (r'안전보건규칙\s*제?\s*\d+조', '안전보건규칙'),
    (r'중대재해\s*처벌\s*등에\s*관한\s*법률', '중대재해처벌법'),
    (r'건설기술\s*진흥법\s*제?\s*\d+조', '건설기술진흥법'),
    (r'위험물안전관리법\s*제?\s*\d+조', '위험물안전관리법'),
    (r'소방시설\s*설치\s*및\s*관리에\s*관한\s*법률', '소방시설법'),
    (r'건축법\s*제?\s*\d+조', '건축법'),
    (r'전기안전관리법\s*제?\s*\d+조', '전기안전관리법'),
    (r'화학물질관리법\s*제?\s*\d+조', '화학물질관리법'),
]

# ── 공종 특이성 점수 (더 구체적인 공종 우선) ────────────────────────────────
TRADE_SPECIFICITY: dict[str, int] = {
    '밀폐공간작업': 10, '크레인': 9, '지게차': 9, '고소작업': 9,
    '소방기계': 8, '소방전기': 8, '공조덕트': 8, '위생설비': 8,
    '흙막이': 8, '거푸집': 7, '비계': 7, '철골': 7,
    '전기': 6, '배관': 6, '통신': 6, '냉난방': 6,
    '굴착': 6, '기초': 6, '용접': 6, '절단': 6,
    '승강기': 7, '도로포장': 7, '상하수도': 7,
    '콘크리트': 5, '방수': 5, '도장': 5, '타일': 5,
    '창호': 5, '유리': 5, '조적': 5, '미장': 5,
    '토공': 4, '철거': 4, '해체': 4, '양중': 4, '운반': 4,
    '가설': 3, '조경': 3, '점검': 3, '유지보수': 3, '청소': 3,
    '내장': 3, '천장': 3, '바닥': 3, '석공': 3, '금속': 3,
    '기계설비': 3,
}

# ── work_type / hazard_type 사전 ─────────────────────────────────────────────

WORK_TYPE_KW: dict[str, list[str]] = {
    '설치':     ['설치', '취부', '고정'],
    '조립':     ['조립', '어셈블'],
    '절단':     ['절단', '커팅', '절삭'],
    '용접':     ['용접', '아크용접', '가스용접', 'TIG', 'CO2'],
    '운반':     ['운반', '이동', '반입'],
    '양중':     ['양중', '인양', '권양', '호이스트', '크레인'],
    '점검':     ['점검', '검사', '확인'],
    '해체':     ['해체', '철거', '분해'],
    '청소':     ['청소', '세척', '청소작업'],
    '도장':     ['도장', '페인팅', '도색'],
    '천공':     ['천공', '드릴', '코어'],
    '배선':     ['배선', '전선포설', '전선'],
    '배관연결': ['배관연결', '플랜지', '밸브연결', '관연결'],
    '기기설치': ['기기설치', '장비설치', '설비설치'],
    '시험운전': ['시운전', '시험운전', '테스트'],
    '굴착':     ['굴착', '터파기', '굴삭'],
    '타설':     ['타설', '콘크리트타설'],
    '조적':     ['쌓기', '조적'],
}

HAZARD_TYPE_KW: dict[str, list[str]] = {
    '추락':  ['추락', '떨어짐', '낙상', '고소추락'],
    '낙하':  ['낙하', '떨어지는', '낙하물', '자재낙하'],
    '협착':  ['협착', '끼임', '끼이는', '압착'],
    '감전':  ['감전', '전기감전', '전기사고', '누전'],
    '화재':  ['화재', '불꽃', '발화', '연소'],
    '폭발':  ['폭발', '가스폭발', '분진폭발'],
    '질식':  ['질식', '산소결핍', '유해가스'],
    '중독':  ['중독', '유해물질', '화학물질중독'],
    '베임':  ['베임', '절상', '날카로운'],
    '붕괴':  ['붕괴', '무너짐', '도괴', '토사붕괴'],
    '전도':  ['전도', '넘어짐', '미끄러짐'],
    '충돌':  ['충돌', '부딪힘', '접촉'],
    '끼임':  ['끼임', '말림', '회전체'],
}


# ── 분류 핵심 로직 ───────────────────────────────────────────────────────────

def _apply_synonyms(text: str) -> str:
    """동의어 사전 적용 → 정규 공종명 치환"""
    for syn, trade in SYNONYMS.items():
        if syn in text:
            text = text + ' ' + trade  # 원문 보존 + 정규명 추가
    return text


def score_trades(text: str) -> dict[str, float]:
    """공종별 매칭 점수 계산"""
    expanded = _apply_synonyms(text)
    scores: dict[str, float] = {}
    for trade, keywords in TRADE_KEYWORDS.items():
        score = 0.0
        for kw in keywords:
            if kw in expanded:
                score += 1.0
        if score > 0:
            # 특이성 보너스 (구체적인 공종 우선)
            specificity = TRADE_SPECIFICITY.get(trade, 3)
            scores[trade] = score + specificity * 0.1
    return scores


def extract_work_type(text: str) -> str | None:
    for wt, kws in WORK_TYPE_KW.items():
        for kw in kws:
            if kw in text:
                return wt
    return None


def extract_hazard_type(text: str) -> str | None:
    for ht, kws in HAZARD_TYPE_KW.items():
        for kw in kws:
            if kw in text:
                return ht
    return None


def extract_equipment(text: str) -> str | None:
    for equip, kws in EQUIPMENT_KW.items():
        for kw in kws:
            if kw in text:
                return equip
    return None


def extract_location(text: str) -> str | None:
    for loc, kws in LOCATION_KW.items():
        for kw in kws:
            if kw in text:
                return loc
    return None


def extract_ppe(text: str) -> str | None:
    found = []
    for ppe, kws in PPE_KW.items():
        for kw in kws:
            if kw in text:
                found.append(ppe)
                break
    return ', '.join(found) if found else None


def extract_law_ref(text: str) -> str | None:
    found = []
    for pattern, law_name in LAW_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            found.append(law_name)
    if found:
        return ', '.join(dict.fromkeys(found))  # 중복 제거
    return None


def _fallback_from_material(material_title: str, material_industry: str,
                             material_keyword: str, material_note: str) -> str:
    """chunk 텍스트로 분류 불가 시 상위 자료 문맥으로 결정"""
    combined = ' '.join([material_title or '', material_keyword or '', material_note or ''])
    scores = score_trades(combined)
    if scores:
        return max(scores, key=lambda t: (scores[t], TRADE_SPECIFICITY.get(t, 3)))
    # 업종별 기본 공종 (최후 수단)
    industry_defaults = {
        '건설업':  '가설',
        '제조업':  '기계설비',
        '조선업':  '용접',
        '서비스업': '점검',
        '기타산업': '유지보수',
    }
    return industry_defaults.get(material_industry or '', '유지보수')


def classify_chunk(chunk_text: str, normalized_text: str,
                   material_title: str = '', material_industry: str = '',
                   material_keyword: str = '', material_note: str = '') -> dict:
    """
    단일 chunk 분류 → {trade_type, work_type, hazard_type, confidence, candidate_trades}
    trade_type 은 반드시 1개, null 금지
    """
    # 1차: chunk 직접 매칭
    combined = ' '.join(filter(None, [normalized_text, chunk_text]))
    scores = score_trades(combined)

    # 2차: work_type/hazard_type/equipment/location/ppe/law_ref 추출
    wt  = extract_work_type(combined)
    ht  = extract_hazard_type(combined)
    eq  = extract_equipment(combined)
    loc = extract_location(combined)
    ppe = extract_ppe(combined)
    law = extract_law_ref(combined)

    if not scores:
        # 3차: 상위 자료 문맥 활용
        trade = _fallback_from_material(material_title, material_industry,
                                        material_keyword, material_note)
        return {
            'trade_type':       trade,
            'work_type':        wt,
            'hazard_type':      ht,
            'equipment':        eq,
            'location':         loc,
            'ppe':              ppe,
            'law_ref':          law,
            'confidence':       0.1,
            'candidate_trades': {},
        }

    # 점수 상위 선택 (동점 시 specificity 높은 것 우선)
    best = max(scores, key=lambda t: (scores[t], TRADE_SPECIFICITY.get(t, 3)))
    total = sum(scores.values())
    confidence = round(scores[best] / total, 4) if total > 0 else 0.1
    confidence = max(confidence, 0.05)

    top_candidates = dict(sorted(scores.items(), key=lambda x: -x[1])[:5])

    return {
        'trade_type':       best,
        'work_type':        wt,
        'hazard_type':      ht,
        'equipment':        eq,
        'location':         loc,
        'ppe':              ppe,
        'law_ref':          law,
        'confidence':       confidence,
        'candidate_trades': top_candidates,
    }


# ── DB 처리 ──────────────────────────────────────────────────────────────────

def classify_and_save_chunk(chunk: dict, material: dict) -> dict:
    """chunk 1건 분류 후 kosha_chunk_tags에 저장"""
    result = classify_chunk(
        chunk_text=chunk.get('raw_text', ''),
        normalized_text=chunk.get('normalized_text', ''),
        material_title=material.get('title', ''),
        material_industry=material.get('industry', ''),
        material_keyword=material.get('keyword', ''),
        material_note=material.get('note', ''),
    )
    combined = ' '.join(filter(None, [chunk.get('raw_text', ''), chunk.get('normalized_text', '')]))
    tag = {
        'chunk_id':         chunk['id'],
        'industry':         material.get('industry'),
        'trade_type':       result['trade_type'],
        'work_type':        result.get('work_type'),
        'hazard_type':      result.get('hazard_type'),
        'equipment':        result.get('equipment'),
        'location':         result.get('location'),
        'ppe':              result.get('ppe') or extract_ppe(combined),
        'law_ref':          result.get('law_ref') or extract_law_ref(combined),
        'confidence':       result['confidence'],
        'rule_version':     RULE_VERSION,
        'candidate_trades': json.dumps(result['candidate_trades'], ensure_ascii=False),
    }
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO kosha_chunk_tags
            (chunk_id, industry, trade_type, work_type, hazard_type,
             equipment, location, ppe, law_ref,
             confidence, rule_version, candidate_trades)
        VALUES
            (%(chunk_id)s, %(industry)s, %(trade_type)s, %(work_type)s, %(hazard_type)s,
             %(equipment)s, %(location)s, %(ppe)s, %(law_ref)s,
             %(confidence)s, %(rule_version)s, %(candidate_trades)s)
        ON CONFLICT DO NOTHING
    """, tag)
    conn.commit()
    cur.close(); conn.close()
    return result


def run_classify_all(batch_size: int = 500):
    """미분류 chunk 전체를 batch로 분류"""
    from datetime import datetime
    start = datetime.now()

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT COUNT(*) FROM kosha_material_chunks kmc
        WHERE NOT EXISTS (SELECT 1 FROM kosha_chunk_tags kct WHERE kct.chunk_id = kmc.id)
    """)
    total = cur.fetchone()[0]
    rlog.info('=== 분류 시작 === 미처리 chunk: %d건', total)
    print(f'[분류] 미처리 chunk: {total}건')

    offset = 0
    classified = 0

    while offset < total:
        cur.execute("""
            SELECT kmc.*, km.title AS mat_title, km.industry AS mat_industry,
                   km.keyword AS mat_keyword, km.note AS mat_note
            FROM kosha_material_chunks kmc
            JOIN kosha_materials km ON km.id = kmc.material_id
            WHERE NOT EXISTS (SELECT 1 FROM kosha_chunk_tags kct WHERE kct.chunk_id = kmc.id)
            ORDER BY kmc.id
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        rows = cur.fetchall()
        if not rows:
            break

        tags = []
        for row in rows:
            chunk = dict(row)
            material = {
                'title':    chunk.get('mat_title', ''),
                'industry': chunk.get('mat_industry', ''),
                'keyword':  chunk.get('mat_keyword', ''),
                'note':     chunk.get('mat_note', ''),
            }
            result = classify_chunk(
                chunk_text=chunk.get('raw_text', ''),
                normalized_text=chunk.get('normalized_text', ''),
                **{f'material_{k}': v for k, v in material.items()},
            )
            combined = ' '.join(filter(None, [chunk.get('raw_text', ''), chunk.get('normalized_text', '')]))
            log.debug('chunk id=%s trade=%s conf=%.2f', chunk['id'], result['trade_type'], result['confidence'])
            tags.append({
                'chunk_id':         chunk['id'],
                'industry':         chunk.get('mat_industry'),
                'trade_type':       result['trade_type'],
                'work_type':        result.get('work_type'),
                'hazard_type':      result.get('hazard_type'),
                'equipment':        result.get('equipment'),
                'location':         result.get('location'),
                'ppe':              result.get('ppe') or extract_ppe(combined),
                'law_ref':          result.get('law_ref') or extract_law_ref(combined),
                'confidence':       result['confidence'],
                'rule_version':     RULE_VERSION,
                'candidate_trades': json.dumps(result['candidate_trades'], ensure_ascii=False),
            })

        conn2 = get_conn()
        cur2 = conn2.cursor()
        psycopg2.extras.execute_batch(cur2, """
            INSERT INTO kosha_chunk_tags
                (chunk_id, industry, trade_type, work_type, hazard_type,
                 equipment, location, ppe, law_ref,
                 confidence, rule_version, candidate_trades)
            VALUES
                (%(chunk_id)s, %(industry)s, %(trade_type)s, %(work_type)s, %(hazard_type)s,
                 %(equipment)s, %(location)s, %(ppe)s, %(law_ref)s,
                 %(confidence)s, %(rule_version)s, %(candidate_trades)s)
            ON CONFLICT DO NOTHING
        """, tags)
        conn2.commit()
        cur2.close(); conn2.close()

        classified += len(tags)
        offset += batch_size
        log.info('분류 진행 %d/%d (batch %d)', classified, total, len(tags))
        print(f'  → {classified}/{total} 분류 완료')

    cur.close(); conn.close()
    elapsed = (datetime.now() - start).seconds
    rlog.info('=== 분류 완료 === 총 %d건 소요:%d초', classified, elapsed)
    print(f'[분류 완료] {classified}건')
    return classified


def run_reclassify_all(batch_size: int = 500):
    """전체 chunk를 v2.0으로 재분류 (equipment/location/ppe/law_ref 채우기)"""
    start = datetime.now()

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT COUNT(*) FROM kosha_material_chunks")
    total = cur.fetchone()[0]
    rlog.info('=== 전체 재분류(v2.0) 시작 === 대상:%d건', total)
    print(f'[재분류] 전체 대상: {total:,}건 (rule_version={RULE_VERSION})')

    offset = 0
    updated = 0

    while offset < total:
        cur.execute("""
            SELECT kmc.*, km.title AS mat_title, km.industry AS mat_industry,
                   km.keyword AS mat_keyword, km.note AS mat_note
            FROM kosha_material_chunks kmc
            JOIN kosha_materials km ON km.id = kmc.material_id
            ORDER BY kmc.id
            LIMIT %s OFFSET %s
        """, (batch_size, offset))
        rows = cur.fetchall()
        if not rows:
            break

        tags = []
        for row in rows:
            chunk = dict(row)
            material = {
                'title':    chunk.get('mat_title', ''),
                'industry': chunk.get('mat_industry', ''),
                'keyword':  chunk.get('mat_keyword', ''),
                'note':     chunk.get('mat_note', ''),
            }
            result = classify_chunk(
                chunk_text=chunk.get('raw_text', ''),
                normalized_text=chunk.get('normalized_text', ''),
                **{f'material_{k}': v for k, v in material.items()},
            )
            combined = ' '.join(filter(None, [chunk.get('raw_text', ''), chunk.get('normalized_text', '')]))
            tags.append({
                'chunk_id':         chunk['id'],
                'industry':         chunk.get('mat_industry'),
                'trade_type':       result['trade_type'],
                'work_type':        result.get('work_type'),
                'hazard_type':      result.get('hazard_type'),
                'equipment':        result.get('equipment'),
                'location':         result.get('location'),
                'ppe':              result.get('ppe') or extract_ppe(combined),
                'law_ref':          result.get('law_ref') or extract_law_ref(combined),
                'confidence':       result['confidence'],
                'rule_version':     RULE_VERSION,
                'candidate_trades': json.dumps(result['candidate_trades'], ensure_ascii=False),
            })

        conn2 = get_conn()
        cur2 = conn2.cursor()
        psycopg2.extras.execute_batch(cur2, """
            INSERT INTO kosha_chunk_tags
                (chunk_id, industry, trade_type, work_type, hazard_type,
                 equipment, location, ppe, law_ref,
                 confidence, rule_version, candidate_trades)
            VALUES
                (%(chunk_id)s, %(industry)s, %(trade_type)s, %(work_type)s, %(hazard_type)s,
                 %(equipment)s, %(location)s, %(ppe)s, %(law_ref)s,
                 %(confidence)s, %(rule_version)s, %(candidate_trades)s)
            ON CONFLICT (chunk_id) DO UPDATE SET
                industry         = EXCLUDED.industry,
                trade_type       = EXCLUDED.trade_type,
                work_type        = EXCLUDED.work_type,
                hazard_type      = EXCLUDED.hazard_type,
                equipment        = EXCLUDED.equipment,
                location         = EXCLUDED.location,
                ppe              = EXCLUDED.ppe,
                law_ref          = EXCLUDED.law_ref,
                confidence       = EXCLUDED.confidence,
                rule_version     = EXCLUDED.rule_version,
                candidate_trades = EXCLUDED.candidate_trades
        """, tags)
        conn2.commit()
        cur2.close(); conn2.close()

        updated += len(tags)
        offset += batch_size
        pct = updated * 100 // total
        print(f'  [{updated:,}/{total:,}] {pct}% 완료')

    cur.close(); conn.close()
    elapsed = (datetime.now() - start).seconds
    rlog.info('=== 재분류 완료 === 총 %d건 소요:%d초', updated, elapsed)
    print(f'[재분류 완료] {updated:,}건 / 소요: {elapsed}초')
    return updated


# ── 단독 실행 ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--reclassify', action='store_true', help='전체 재분류 (v2.0 업데이트)')
    args = parser.parse_args()

    if args.reclassify:
        print('=== KOSHA 전체 재분류 (v2.0) 시작 ===')
        n = run_reclassify_all()
        print(f'총 {n:,}건 재분류 완료')
    else:
        print('=== KOSHA 미분류 chunk 분류 시작 ===')
        n = run_classify_all()
        print(f'총 {n}건 분류 완료')
