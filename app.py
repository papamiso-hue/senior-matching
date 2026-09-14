import streamlit as st
import streamlit.components.v1 as components
import re
import uuid
import math
import io
import json
import random
import requests
from datetime import datetime, timedelta, timezone
import pandas as pd
from supabase import create_client, Client
from pypdf import PdfReader

# 1. 스트림릿 기본 페이지 설정 (반드시 최상단 1회 호출)
st.set_page_config(
    page_title="노블레스 라온 - 5060 검증형 프라이빗 매칭",
    page_icon="👑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. PWA 모바일 웹앱 메타태그 주입
st.markdown("""
<head>
    <title>노블레스 라온</title>
    <meta name="apple-mobile-web-app-title" content="노블레스 라온">
    <meta name="application-name" content="노블레스 라온">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="apple-touch-icon" href="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=192&auto=format&fit=crop">
    <link rel="icon" type="image/png" href="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=192&auto=format&fit=crop">
</head>
""", unsafe_allow_html=True)

# 3. 서비스 기본 상수 정의
BRAND_NAME_KR = "노블레스 라온"
BRAND_NAME_EN = "NOBLESSE RAON 5060"
SITE_URL = "https://senior-matching-xtflgt6cnpp6q9o53z79pb.streamlit.app/"
OG_IMAGE_URL = "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=1200&auto=format&fit=crop"
KAKAO_CHAT_URL = "https://open.kakao.com/o/sRas35Li"

ALIGO_API_KEY = "a2d6ej9asoilb20w66tmw6zw3qqp7shk"
ALIGO_USER_ID = "equivision"
ALIGO_SENDER = "01030383349"

# 4. 플랫폼 전용 맞춤법/오타 검증 엔진
PLATFORM_TYPO_RULES = {
    r"안녕하새요": "안녕하세요",
    r"결재": "결제(이용권/티켓 결제)",
    r"됍니다": "됩니다",
    r"되요": "돼요",
    r"뵈요": "봬요",
    r"몇일": "며칠",
    r"바램": "바람",
    r"어의없": "어이없",
    r"신용점숫": "신용점수"
}

def audit_text_typos(text: str):
    """입력된 텍스트에서 오탈자 및 부적절한 표현 감지"""
    if not text:
        return []
    warnings = []
    for pattern, correct in PLATFORM_TYPO_RULES.items():
        if re.search(pattern, text):
            warnings.append(f"'{pattern}' ➡️ '{correct}'")
    return warnings

KOREA_REGIONS = {
    "서울특별시": [
        "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
        "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
        "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
    ],
    "경기도": [
        "수원시 장안구", "수원시 권선구", "수원시 팔달구", "수원시 영통구",
        "성남시 수정구", "성남시 중원구", "성남시 분당구",
        "의정부시", "안양시 만안구", "안양시 동안구", "부천시 원미구", "부천시 소사구", "부천시 오정구",
        "광명시", "평택시", "동두천시", "안산시 상록구", "안산시 단원구", "고양시 덕양구", "고양시 일산동구", "고양시 일산서구",
        "과천시", "구리시", "남양주시", "오산시", "시흥시", "군포시", "의왕시", "하남시",
        "용인시 처인구", "용인시 기흥구", "용인시 수지구", "파주시", "이천시", "안성시", "김포시", "화성시",
        "광주시", "양주시", "포천시", "여주시", "연천군", "가평군", "양평군"
    ],
    "인천광역시": ["중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"],
    "부산광역시": ["중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구", "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"],
    "대구광역시": ["중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군", "군위군"],
    "대전광역시": ["동구", "중구", "서구", "유성구", "대덕구"],
    "세종특별자치시": ["세종시 전역"]
}

# 5060 전용 필수 가치관 5대 문항
CORE_QUESTIONS_5060 = {
    1: {
        "text": "1. 이상적인 동반 형태 및 관계 방향?",
        "options": ["혼인신고(법적 재혼) 희망", "사실혼(동거 및 일상 공유)", "LAT(각자 주거 유지 + 데이트형 동반자)", "편안하게 의지하는 친구 같은 만남"]
    },
    2: {
        "text": "2. 자녀 독립 상태 및 교류 빈도?",
        "options": ["자녀 완전 출가·독립 (독립적인 둘만의 생활 선호)", "자녀와 정기적 교류 (명절·주말 식사 등)", "자녀 동거 중 (상호 이해와 배려 필요)", "자녀 없음"]
    },
    3: {
        "text": "3. 경제 관리 및 생활비 분담 기준?",
        "options": ["남성 전액 부담 또는 주도적 관리", "각자 자산 독립 관리 + 공동 생활비 반반", "상호 형편에 맞춘 유연한 분담", "사전 협의 후 공정 관리"]
    },
    4: {
        "text": "4. 은퇴 후 주거 환경 및 여가 지향점?",
        "options": ["도심 인프라 및 문화생활 중심", "근교 전원주택/타운하우스 여유로운 삶", "여행·캠핑·골프 등 활동적 여가 공유", "조용하고 정적인 힐링 라이프"]
    },
    5: {
        "text": "5. 종교 및 생활 습관(음주/흡연) 성향?",
        "options": ["동일 종교 필수", "종교 무관 / 상호 독립성 존중", "비흡연 필수 + 절주형 라이프", "자유로운 라이프스타일 양해"]
    }
}

# 5060 클래식 블랙 & 럭셔리 골드 테마 CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0A0A0B !important;
        color: #F8FAFC !important;
        font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Noto Sans KR", sans-serif;
    }
    .block-container { 
        padding-top: 1.8rem !important; 
        padding-bottom: 3.5rem !important; 
        max-width: 620px !important; 
    }

    .hero-box {
        background: linear-gradient(145deg, #18181B 0%, #111113 60%, #1C1917 100%);
        border: 1px solid rgba(212, 175, 55, 0.4);
        border-radius: 18px;
        padding: 26px 20px 22px 20px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px -10px rgba(212, 175, 55, 0.25);
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: rgba(212, 175, 55, 0.15);
        border: 1px solid rgba(212, 175, 55, 0.45);
        color: #FDE047 !important;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 2px;
        padding: 4px 12px;
        border-radius: 30px;
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 900;
        color: #FFFFFF !important;
        letter-spacing: -0.8px;
        line-height: 1.25;
        margin-bottom: 10px;
    }
    .hero-subtitle {
        font-size: 1.0rem;
        font-weight: 600;
        color: #E2E8F0 !important;
        line-height: 1.55;
        word-break: keep-all;
    }
    .hero-highlight {
        color: #FACC15 !important;
        font-weight: 800;
    }

    .promise-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 1rem;
    }
    .promise-card {
        background: #18181B !important;
        border: 1px solid #27272A !important;
        border-radius: 12px;
        padding: 14px 6px;
        text-align: center;
    }
    .promise-icon {
        font-size: 1.4rem;
        margin-bottom: 4px;
    }
    .promise-title {
        font-size: 0.84rem;
        font-weight: 800;
        color: #F4F4F5 !important;
    }
    .promise-desc {
        font-size: 0.70rem;
        color: #A1A1AA !important;
        margin-top: 2px;
    }

    .criteria-box {
        background: rgba(24, 24, 27, 0.8);
        border: 1px solid #3F3F46;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    div[data-baseweb="tab-list"] {
        background-color: #18181B !important;
        padding: 4px;
        border-radius: 10px;
        gap: 4px;
        border: 1px solid #27272A !important;
        margin-bottom: 1.2rem;
    }
    div[data-baseweb="tab"] {
        flex: 1;
        height: 44px;
        border-radius: 8px !important;
        background-color: transparent !important;
        color: #A1A1AA !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        border: none !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #CA8A04 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(202, 138, 4, 0.35);
    }
    div[data-baseweb="tab-border"] {
        display: none !important;
    }

    div[data-baseweb="input"] {
        background-color: #18181B !important;
        border: 1.5px solid #27272A !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #EAB308 !important;
    }
    div[data-baseweb="input"] input {
        color: #FFFFFF !important;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #F4F4F5 !important;
        font-weight: 700;
        font-size: 0.88rem;
    }

    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        font-weight: 800; 
        height: 3.2rem;
        font-size: 1.02rem;
        border: none !important;
        background: linear-gradient(90deg, #CA8A04 0%, #A16207 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(202, 138, 4, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #EAB308 0%, #CA8A04 100%) !important;
    }

    .badge-gold {
        background: rgba(202, 138, 4, 0.2);
        color: #FDE047;
        border: 1px solid rgba(234, 179, 8, 0.4);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .badge-credit {
        background: rgba(16, 185, 129, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .profile-avatar-blur {
        width: 74px;
        height: 74px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #EAB308;
        filter: blur(6px);
        transform: scale(0.96);
    }
    .profile-avatar-clear {
        width: 74px;
        height: 74px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #10B981;
    }

    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = "https://xxiagepuzmukwcdnurhg.supabase.co"
SUPABASE_KEY = "sb_publishable_CCbsSoMbvLYh1y4xJ2zYEA_XxisldNn"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

def send_aligo_sms(receiver_phone, auth_code):
    try:
        url = "https://apis.aligo.in/send/"
        payload = {
            "key": ALIGO_API_KEY,
            "user_id": ALIGO_USER_ID,
            "sender": ALIGO_SENDER,
            "receiver": receiver_phone,
            "msg": f"[{BRAND_NAME_KR}] 본인인증 번호는 [{auth_code}] 입니다. (타인 유출 주의)",
            "testmode_yn": "N"
        }
        res = requests.post(url, data=payload, timeout=6)
        if res.status_code == 200 and res.json().get("result_code") == "1":
            return True, "인증번호가 발송되었습니다."
        return False, "인증문자 발송 실패"
    except Exception as e:
        return False, f"SMS 오류: {e}"

def send_aligo_notice_sms(receiver_phone, text_message):
    try:
        url = "https://apis.aligo.in/send/"
        payload = {
            "key": ALIGO_API_KEY,
            "user_id": ALIGO_USER_ID,
            "sender": ALIGO_SENDER,
            "receiver": receiver_phone,
            "msg": f"[{BRAND_NAME_KR}] {text_message}",
            "testmode_yn": "N"
        }
        requests.post(url, data=payload, timeout=6)
    except Exception:
        pass

DEFAULT_AVATARS = {
    "남": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=300&auto=format&fit=crop",
    "여": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=300&auto=format&fit=crop"
}

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "sms_auth_code" not in st.session_state:
    st.session_state.sms_auth_code = None
if "sms_verified_phone" not in st.session_state:
    st.session_state.sms_verified_phone = None
if "sms_is_verified" not in st.session_state:
    st.session_state.sms_is_verified = False

# --- 1. 로그인 / 신규 가입 화면 ---
if not st.session_state.user_id:
    st.markdown(f"""
        <div class="hero-box">
            <div class="hero-badge">👑 5060 NOBLESSE MATCHING</div>
            <div class="hero-title">🌟 {BRAND_NAME_KR}</div>
            <div class="hero-subtitle">품격 있는 인생 2막을 함께할 진중한 동반자를 위한<br>
            <span class="hero-highlight">신용·신원 검증 기반 시니어 프라이빗 살롱</span></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="promise-grid">
            <div class="promise-card">
                <div class="promise-icon">🛡️</div>
                <div class="promise-title">신용·자산 검증</div>
                <div class="promise-desc">남 800 / 여 600점+</div>
            </div>
            <div class="promise-card">
                <div class="promise-icon">🚫</div>
                <div class="promise-title">지인 번호 완벽차단</div>
                <div class="promise-desc">가족/지인 안심 미노출</div>
            </div>
            <div class="promise-card">
                <div class="promise-icon">🔒</div>
                <div class="promise-title">안심 비공개 프로필</div>
                <div class="promise-desc">상호 수락 시 연락처 공개</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="criteria-box">
            <span style="font-weight:800; font-size:0.84rem; color:#FDE047;">📌 5060 정회원 입회 기준</span>
            <span style="font-weight:900; font-size:0.88rem; color:#6EE7B7;">만 40세 ~ 85세 (남 800 / 여 600점 이상)</span>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_join = st.tabs(["🔑 정회원 로그인", "📝 신규 프로필 등록"])

    with tab_login:
        login_name = st.text_input("성명", key="l_name")
        login_phone = st.text_input("휴대폰 번호 (- 제외 숫자만)", placeholder="01012345678", key="l_phone")
        login_pwd = st.text_input("간편 비밀번호 (4~6자리)", type="password", key="l_pwd")

        if st.button("안심 본인인증 로그인", key="btn_login"):
            clean_p = re.sub(r'[^0-9]', '', login_phone.strip())
            if not login_name.strip() or not clean_p or not login_pwd.strip():
                st.error("성명, 휴대폰 번호, 비밀번호를 모두 입력해 주세요.")
            else:
                res = supabase.table("users").select("*")\
                    .eq("name", login_name.strip())\
                    .eq("phone", clean_p)\
                    .eq("password", login_pwd.strip())\
                    .execute()
                if res.data:
                    u = res.data[0]
                    if u.get("is_suspended"):
                        st.error("🚫 제재 조치된 계정입니다. 고객센터로 문의해 주세요.")
                    else:
                        now_utc = datetime.now(timezone.utc).isoformat()
                        supabase.table("users").update({"last_login_at": now_utc}).eq("id", u["id"]).execute()
                        u["last_login_at"] = now_utc
                        st.session_state.user_id = u["id"]
                        st.session_state.user_info = u
                        st.rerun()
                else:
                    st.error("일치하는 회원 정보를 찾을 수 없습니다.")

    with tab_join:
        st.markdown("##### 👤 기본 인적사항 (만 40~85세 대상)")
        j_name = st.text_input("실명", key="j_name")
        
        col_p1, col_p2 = st.columns([2.5, 1.2])
        with col_p1:
            j_phone = st.text_input("휴대폰 번호 (- 제외)", placeholder="01012345678", key="j_phone")
        with col_p2:
            st.write("")
            btn_sms = st.button("인증번호 발송", key="btn_sms")

        clean_jp = re.sub(r'[^0-9]', '', j_phone.strip())
        if btn_sms:
            if len(clean_jp) < 10:
                st.error("올바른 휴대폰 번호를 입력해 주세요.")
            else:
                dup = supabase.table("users").select("id").eq("phone", clean_jp).execute().data
                if dup:
                    st.error("이미 등록된 휴대폰 번호입니다.")
                else:
                    code = str(random.randint(100000, 999999))
                    st.session_state.sms_auth_code = code
                    st.session_state.sms_verified_phone = clean_jp
                    st.session_state.sms_is_verified = False
                    send_aligo_sms(clean_jp, code)
                    st.success("문자로 발송된 6자리 인증번호를 입력해 주세요.")

        if st.session_state.sms_auth_code:
            c_code, c_btn = st.columns([2.5, 1.2])
            with c_code:
                in_code = st.text_input("인증번호 6자리", key="in_sms_code")
            with c_btn:
                st.write("")
                if st.button("인증 확인", key="btn_confirm_sms"):
                    if in_code.strip() == st.session_state.sms_auth_code:
                        st.session_state.sms_is_verified = True
                        st.success("✅ 휴대폰 인증이 완료되었습니다.")
                    else:
                        st.error("인증번호가 일치하지 않습니다.")

        j_pwd = st.text_input("간편 비밀번호 (4~6자리)", type="password", key="j_pwd")
        j_gender = st.radio("성별", ["남", "여"], horizontal=True, key="j_gender")
        j_age = st.number_input("나이 (만 나이)", 40, 85, 58, key="j_age")

        r_col1, r_col2 = st.columns(2)
        with r_col1:
            j_sido = st.selectbox("활동 광역시·도", list(KOREA_REGIONS.keys()), index=0, key="j_sido")
        with r_col2:
            j_sigungu = st.selectbox("시·군·구", KOREA_REGIONS[j_sido], index=0, key="j_sigungu")
        j_region = f"{j_sido} {j_sigungu}"

        st.markdown("##### 💼 경력 및 라이프스타일")
        j_job = st.text_input("직업 또는 이전 경력", placeholder="예: 사업체 운영 / 전문직 퇴직 / 프리랜서", key="j_job")
        job_typos = audit_text_typos(j_job)
        if job_typos:
            st.caption(f"💡 표현 교정 안내: {', '.join(job_typos)}")

        j_hobbies = st.text_input("취미 및 여가 생활", placeholder="예: 골프, 전원생활, 등산, 클래식 감상", key="j_hobbies")
        hobby_typos = audit_text_typos(j_hobbies)
        if hobby_typos:
            st.caption(f"💡 표현 교정 안내: {', '.join(hobby_typos)}")

        j_intro = st.text_area("동반자에게 전하고 싶은 말씀", value="인생의 후반전을 서로 존중하며 따뜻하게 보낼 인연을 찾습니다.", key="j_intro")
        intro_typos = audit_text_typos(j_intro)
        if intro_typos:
            st.caption(f"💡 소개글 맞춤법 안내: {', '.join(intro_typos)}")

        st.markdown("##### 🛡️ 신용 검증 기준")
        req_score = 800 if j_gender == "남" else 600
        st.caption(f"ℹ️ {j_gender}성 입회 기준: 공인 신용점수 {req_score}점 이상")
        j_credit = st.number_input(f"공인 신용점수 ({req_score}점 이상 필수)", 0, 1000, 820 if j_gender == "남" else 750, key="j_credit")
        j_doc = st.file_uploader("신용 증빙 서류 첨부 (NICE/KCB 리포트 또는 토스 캡처)", type=["jpg", "png", "pdf"], key="j_doc")

        st.markdown("##### 🎯 5060 필수 가치관 5대 문답")
        a1 = st.radio(CORE_QUESTIONS_5060[1]["text"], CORE_QUESTIONS_5060[1]["options"], key="jq_1")
        a2 = st.radio(CORE_QUESTIONS_5060[2]["text"], CORE_QUESTIONS_5060[2]["options"], key="jq_2")
        a3 = st.radio(CORE_QUESTIONS_5060[3]["text"], CORE_QUESTIONS_5060[3]["options"], key="jq_3")
        a4 = st.radio(CORE_QUESTIONS_5060[4]["text"], CORE_QUESTIONS_5060[4]["options"], key="jq_4")
        a5 = st.radio(CORE_QUESTIONS_5060[5]["text"], CORE_QUESTIONS_5060[5]["options"], key="jq_5")

        agree_terms = st.checkbox("[필수] 노블레스 라온 이용약관 및 증빙서류 확인 즉시 파기에 동의합니다.", key="agree_terms")

        if st.button("신원 검증 신청 및 가입 완료", key="btn_submit_join"):
            if not agree_terms:
                st.error("필수 이용약관에 동의해 주세요.")
            elif not j_name.strip():
                st.error("성명을 입력해 주세요.")
            elif not st.session_state.sms_is_verified or st.session_state.sms_verified_phone != clean_jp:
                st.error("휴대폰 SMS 인증을 완료해 주세요.")
            elif len(j_pwd.strip()) < 4:
                st.error("비밀번호는 최소 4자리 이상이어야 합니다.")
            elif j_credit < req_score:
                st.error(f"입회 기준 미달: 노블레스 라온은 {j_gender}성 기준 {req_score}점 이상만 승인됩니다.")
            elif not j_doc:
                st.error("신원 및 신용 증빙 서류를 첨부해 주세요.")
            else:
                doc_ext = j_doc.name.split(".")[-1].lower()
                doc_name = f"verify_{clean_jp}_{uuid.uuid4().hex[:6]}.{doc_ext}"
                try:
                    supabase.storage.from_("credit-docs").upload(
                        doc_name, 
                        j_doc.read(), 
                        {"content-type": "application/pdf" if doc_ext == "pdf" else f"image/{doc_ext}"}
                    )
                    doc_url = f"{SUPABASE_URL}/storage/v1/object/public/credit-docs/{doc_name}"
                    now_utc = datetime.now(timezone.utc).isoformat()

                    new_u = supabase.table("users").insert({
                        "name": j_name.strip(),
                        "phone": clean_jp,
                        "password": j_pwd.strip(),
                        "gender": j_gender,
                        "age": int(j_age),
                        "region": j_region,
                        "credit_score": int(j_credit),
                        "credit_doc_url": doc_url,
                        "credit_status": "PENDING",
                        "is_verified": False,
                        "ticket_count": 3,
                        "is_vip": False,
                        "blocked_phones": [],
                        "last_login_at": now_utc,
                        "job": j_job.strip() if j_job else "개인사업/전문직",
                        "hobbies": j_hobbies.strip() if j_hobbies else "여가 생활",
                        "intro": j_intro.strip(),
                        "is_admin": False,
                        "is_suspended": False
                    }).execute().data[0]

                    uid = new_u["id"]
                    supabase.table("user_answers").insert([
                        {"user_id": uid, "question_num": 1, "answer_value": a1},
                        {"user_id": uid, "question_num": 2, "answer_value": a2},
                        {"user_id": uid, "question_num": 3, "answer_value": a3},
                        {"user_id": uid, "question_num": 4, "answer_value": a4},
                        {"user_id": uid, "question_num": 5, "answer_value": a5}
                    ]).execute()

                    st.session_state.user_id = uid
                    st.session_state.user_info = new_u
                    st.success("🎉 서류 제출 및 가입이 완료되었습니다! 웰컴 티켓 3장이 지급되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"가입 처리 중 오류 발생: {e}")

# --- 2. 메인 대시보드 화면 ---
else:
    me = st.session_state.user_info

    st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom: 2px solid #3F3F46; padding-bottom: 8px;">
            <div style="font-size:1.1rem; font-weight:900; color:#FFFFFF;">🌟 {BRAND_NAME_KR}</div>
            <div style="font-size:0.75rem; font-weight:800; color:#EAB308; letter-spacing:1px;">{BRAND_NAME_EN}</div>
        </div>
    """, unsafe_allow_html=True)

    t_col1, t_col2 = st.columns([1, 3])
    with t_col1:
        my_avatar = me.get("photo_url") or DEFAULT_AVATARS.get(me["gender"])
        st.markdown(f'<img src="{my_avatar}" class="profile-avatar-clear">', unsafe_allow_html=True)
    with t_col2:
        st.markdown(f"#### **{me['name']}** ({me['gender']} · {me['age']}세)")
        st.markdown(f'<span class="badge-gold">💼 {me.get("job", "경력 인증")}</span> <span class="badge-credit">🛡️ 신용 {me["credit_score"]}점</span>', unsafe_allow_html=True)
        st.caption(f"📍 {me['region']} | 🎟️ 보유 티켓: {me.get('ticket_count', 0)}장")

    with st.expander("🚫 아는 사람 / 지인 번호 차단 관리"):
        curr_blocks = me.get("blocked_phones") or []
        b_input = st.text_input("차단할 휴대폰 번호 (- 제외)", placeholder="예: 01098765432", key="in_block_p")
        if st.button("차단 목록에 등록"):
            clean_bp = re.sub(r'[^0-9]', '', b_input.strip())
            if len(clean_bp) >= 10 and clean_bp not in curr_blocks:
                curr_blocks.append(clean_bp)
                supabase.table("users").update({"blocked_phones": curr_blocks}).eq("id", me["id"]).execute()
                me["blocked_phones"] = curr_blocks
                st.session_state.user_info = me
                st.success(f"{clean_bp} 번호가 상호 차단되었습니다.")
                st.rerun()

    tabs_main = st.tabs(["💖 가치관 매칭 피드", "📬 신청 보관함", "👤 프로필 관리 및 사진"])

    my_ans_data = supabase.table("user_answers").select("question_num, answer_value").eq("user_id", me["id"]).execute().data
    my_answers = {item["question_num"]: item["answer_value"] for item in my_ans_data}

    with tabs_main[0]:
        target_gender = "여" if me["gender"] == "남" else "남"
        # 5060은 만 40세 이상만 추천 대상
        raw_candidates = supabase.table("users").select("*")\
            .eq("gender", target_gender)\
            .gte("age", 40)\
            .eq("is_suspended", False)\
            .execute().data

        my_blocked_set = set(me.get("blocked_phones") or [])
        my_phone = me.get("phone", "")

        candidates = []
        for cand in raw_candidates:
            c_phone = cand.get("phone", "")
            c_blocked = set(cand.get("blocked_phones") or [])
            if c_phone in my_blocked_set or my_phone in c_blocked:
                continue
            candidates.append(cand)

        sent_reqs = supabase.table("match_requests").select("receiver_id, status").eq("sender_id", me["id"]).execute().data
        sent_dict = {req["receiver_id"]: req["status"] for req in sent_reqs}

        if not candidates:
            st.info("현재 활동 중인 추천 회원이 없습니다.")
        else:
            cand_scores = []
            for cand in candidates:
                c_ans_data = supabase.table("user_answers").select("question_num, answer_value").eq("user_id", cand["id"]).execute().data
                c_answers = {item["question_num"]: item["answer_value"] for item in c_ans_data}
                
                common_keys = set(my_answers.keys()).intersection(set(c_answers.keys()))
                score = int((sum(1 for k in common_keys if my_answers[k] == c_answers[k]) / len(common_keys)) * 100) if common_keys else 0
                cand_scores.append((cand, c_answers, common_keys, score))

            cand_scores.sort(key=lambda x: x[3], reverse=True)

            for cand, c_answers, common_keys, score in cand_scores:
                with st.container():
                    c1, c2, c3 = st.columns([1, 2.5, 1])
                    with c1:
                        c_img = cand.get("photo_url") or DEFAULT_AVATARS.get(cand["gender"])
                        st.markdown(f'<img src="{c_img}" class="profile-avatar-blur">', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"**{cand['name'][0]}*님** ({cand['gender']} · {cand['age']}세)")
                        st.markdown(f'<span class="badge-gold">💼 {cand.get("job", "경력 인증")}</span> <span class="badge-credit">신용 {cand["credit_score"]}점</span>', unsafe_allow_html=True)
                        st.caption(f"📍 {cand['region']}")
                        if cand.get("intro"):
                            st.caption(f'"{cand["intro"]}"')
                    with c3:
                        st.metric("가치관 일치율", f"{score}%")

                    with st.expander("🔍 가치관 5대 문항 대조표 보기"):
                        for q_num in sorted(list(CORE_QUESTIONS_5060.keys())):
                            q_text = CORE_QUESTIONS_5060[q_num]["text"]
                            m_val = my_answers.get(q_num, "미응답")
                            c_val = c_answers.get(q_num, "미응답")
                            is_match = (m_val == c_val)
                            match_label = "🟢 일치" if is_match else "⚪ 상이"
                            st.markdown(f"**[{match_label}] {q_text}**")
                            st.caption(f"• 내 답변: {m_val} | 상대방: {c_val}")

                    req_status = sent_dict.get(cand["id"])
                    if req_status == "PENDING":
                        st.button(f"⏳ 대화 수락 대기중 ({cand['name'][0]}*님)", key=f"feed_btn_{cand['id']}", disabled=True)
                    elif req_status == "ACCEPTED":
                        st.success("🎉 매칭 성공! 보관함에서 선명한 프로필과 연락처를 확인하세요.")
                    else:
                        if st.button("💌 대화 신청 (티켓 1장 차감)", key=f"feed_btn_{cand['id']}"):
                            if me.get("ticket_count", 0) <= 0:
                                st.error("티켓이 부족합니다.")
                            else:
                                supabase.table("users").update({"ticket_count": me["ticket_count"] - 1}).eq("id", me["id"]).execute()
                                supabase.table("match_requests").insert({
                                    "sender_id": me["id"],
                                    "receiver_id": cand["id"],
                                    "status": "PENDING",
                                    "payment_status": "PAID"
                                }).execute()
                                send_aligo_notice_sms(cand["phone"], f"{me['name'][0]}* 님으로부터 가치관 기반 대화 신청이 도착했습니다.")
                                st.rerun()
                    st.divider()

    with tabs_main[1]:
        inbox_1, inbox_2 = st.tabs(["내가 보낸 신청", "나에게 온 신청"])
        
        with inbox_1:
            sent_list = supabase.table("match_requests").select("*").eq("sender_id", me["id"]).execute().data
            if not sent_list:
                st.caption("보낸 신청이 없습니다.")
            else:
                for req in sent_list:
                    rcv = supabase.table("users").select("*").eq("id", req["receiver_id"]).execute().data[0]
                    if req["status"] == "ACCEPTED":
                        st.success(f"🎉 **{rcv['name']}** 님과 매칭이 성사되었습니다!")
                        r_img = rcv.get("photo_url") or DEFAULT_AVATARS.get(rcv["gender"])
                        st.markdown(f'<img src="{r_img}" class="profile-avatar-clear">', unsafe_allow_html=True)
                        st.write(f"📞 안심 연락처: **{rcv['phone']}** | 💼 경력: **{rcv.get('job')}**")
                        st.markdown(f'<a href="tel:{rcv["phone"]}">📞 전화 걸기</a>', unsafe_allow_html=True)
                    else:
                        st.write(f"• **{rcv['name'][0]}*님**에게 보낸 신청 | 상태: `{req['status']}`")

        with inbox_2:
            rcv_list = supabase.table("match_requests").select("*").eq("receiver_id", me["id"]).execute().data
            if not rcv_list:
                st.caption("도착한 신청이 없습니다.")
            else:
                for req in rcv_list:
                    snd = supabase.table("users").select("*").eq("id", req["sender_id"]).execute().data[0]
                    st.markdown(f"**{snd['name'][0]}*님** ({snd['gender']} · {snd['age']}세 · {snd.get('job')})")
                    if req["status"] == "ACCEPTED":
                        st.success("🤝 대화 수락 완료! 연락처가 공개되었습니다.")
                        s_img = snd.get("photo_url") or DEFAULT_AVATARS.get(snd["gender"])
                        st.markdown(f'<img src="{s_img}" class="profile-avatar-clear">', unsafe_allow_html=True)
                        st.write(f"📞 안심 연락처: **{snd['phone']}**")
                    elif req["status"] == "PENDING":
                        col_ac, col_re = st.columns(2)
                        with col_ac:
                            if st.button("수락 및 연락처 공유", key=f"ac_{req['id']}"):
                                supabase.table("match_requests").update({"status": "ACCEPTED"}).eq("id", req["id"]).execute()
                                send_aligo_notice_sms(snd["phone"], f"{me['name'][0]}* 님이 대화를 수락했습니다. 안심 연락처를 확인하세요.")
                                st.rerun()
                        with col_re:
                            if st.button("거절", key=f"re_{req['id']}"):
                                supabase.table("match_requests").update({"status": "REJECTED"}).eq("id", req["id"]).execute()
                                st.rerun()
                    st.divider()

    with tabs_main[2]:
        st.markdown("##### ✏️ 자기소개 및 경력·취미 정보 수정")
        edit_job = st.text_input("직업 또는 경력 수정", value=me.get("job", ""), key="edit_job")
        job_errs = audit_text_typos(edit_job)
        if job_errs:
            st.caption(f"💡 권장 수정: {', '.join(job_errs)}")

        edit_hobbies = st.text_input("취미 및 여가 생활 수정", value=me.get("hobbies", ""), key="edit_hobbies")
        hobby_errs = audit_text_typos(edit_hobbies)
        if hobby_errs:
            st.caption(f"💡 권장 수정: {', '.join(hobby_errs)}")

        edit_intro = st.text_area("한 줄 소개 수정", value=me.get("intro", ""), key="edit_intro")
        intro_errs = audit_text_typos(edit_intro)
        if intro_errs:
            st.caption(f"💡 권장 수정: {', '.join(intro_errs)}")

        if st.button("프로필 정보 업데이트"):
            supabase.table("users").update({
                "job": edit_job.strip(),
                "hobbies": edit_hobbies.strip(),
                "intro": edit_intro.strip()
            }).eq("id", me["id"]).execute()
            me["job"] = edit_job.strip()
            me["hobbies"] = edit_hobbies.strip()
            me["intro"] = edit_intro.strip()
            st.session_state.user_info = me
            st.success("프로필 정보가 성공적으로 수정되었습니다.")
            st.rerun()

        st.markdown("---")
        st.markdown("##### 📸 프로필 사진 등록")
        st.caption("등록된 사진은 매칭 전까지 실루엣 블러 처리되어 안전하게 보호되며, 상호 수락 시에만 상대방에게 선명하게 공개됩니다.")
        new_avatar = st.file_uploader("사진 파일 선택 (JPG, PNG)", type=["jpg", "png", "jpeg"], key="up_avatar")
        if new_avatar and st.button("사진 등록 및 저장"):
            f_ext = new_avatar.name.split(".")[-1].lower()
            fname = f"avatar_5060_{me['id']}_{uuid.uuid4().hex[:6]}.{f_ext}"
            supabase.storage.from_("avatars").upload(fname, new_avatar.read(), {"content-type": f"image/{f_ext}"})
            url = f"{SUPABASE_URL}/storage/v1/object/public/avatars/{fname}"
            supabase.table("users").update({"photo_url": url}).eq("id", me["id"]).execute()
            me["photo_url"] = url
            st.session_state.user_info = me
            st.success("사진이 등록되었습니다. 매칭 전에는 블라인드 보호가 자동 적용됩니다.")
            st.rerun()

    st.markdown("---")
    if st.button("로그아웃"):
        st.session_state.user_id = None
        st.session_state.user_info = None
        st.rerun()
