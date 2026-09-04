import streamlit as st
import streamlit.components.v1 as components
import re
import uuid
import math
from datetime import datetime
import pandas as pd
from supabase import create_client, Client

# 브랜드 기본 정보 및 카카오 오픈채팅 공식 연동
BRAND_NAME_KR = "노블레스 라온"
BRAND_NAME_EN = "NOBLESSE RAON"
BRAND_SLOGAN = "신용과 품격이 통하는 5060 프리미엄 맞춤 인연"
KAKAO_CHAT_URL = "https://open.kakao.com/o/sRas35Li"

st.set_page_config(
    page_title=f"{BRAND_NAME_KR} - 5060 프리미엄 안심 매칭",
    page_icon="👑",
    layout="centered"
)

# 반응형 고대비 및 프리미엄 브랜드 전면 스타일
st.markdown(f"""
    <style>
    .block-container {{ 
        padding-top: 2.8rem !important; 
        padding-bottom: 3.5rem !important; 
        max-width: 780px; 
    }}
    
    /* 브랜드 헤더 전면 배너 */
    .brand-hero-header {{
        text-align: center;
        padding: 22px 16px 18px 16px;
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
        border: 2px solid #D97706;
        border-radius: 14px;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.15);
    }}
    .brand-logo-en {{
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 3.5px;
        color: #F59E0B;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    .brand-logo-kr {{
        font-size: 1.95rem;
        font-weight: 900;
        color: #FFFFFF;
        letter-spacing: -0.8px;
        line-height: 1.25;
        margin-bottom: 8px;
    }}
    .brand-slogan {{
        font-size: 0.95rem;
        font-weight: 700;
        color: #94A3B8;
        letter-spacing: -0.2px;
    }}

    .badge-box {{
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        border: 2px solid #334155;
    }}
    .badge-tag {{
        display: inline-block;
        background-color: #E11D48;
        color: #FFFFFF !important;
        font-size: 0.78rem;
        font-weight: 800;
        padding: 4px 9px;
        border-radius: 5px;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }}
    .badge-text {{
        font-size: 1.05rem;
        font-weight: 800;
        color: #38BDF8 !important;
        line-height: 1.45;
    }}
    .highlight-score {{
        color: #FDE047 !important;
        font-size: 1.15rem;
        font-weight: 900;
        text-decoration: underline;
        text-underline-offset: 4px;
    }}

    .premium-hero-box {{
        background: #F8FAFC;
        border: 2px solid #E2E8F0;
        border-left: 5px solid #D97706;
        padding: 16px 18px;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }}
    .hero-line1 {{
        font-size: 1.05rem;
        font-weight: 800;
        color: #0F172A !important;
        margin-bottom: 6px;
        line-height: 1.4;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .hero-line2 {{
        font-size: 0.95rem;
        font-weight: 700;
        color: #475569 !important;
        line-height: 1.5;
    }}
    .highlight-gold {{
        color: #B45309 !important;
        font-weight: 900;
    }}
    .highlight-blue {{
        color: #0369A1 !important;
        font-weight: 900;
    }}

    .network-accent-card {{
        background: linear-gradient(135deg, #FFFDF7 0%, #FEF9EE 100%);
        border: 1.5px solid #F6D896;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 1.3rem;
        box-shadow: 0 3px 10px rgba(217, 119, 6, 0.08);
    }}
    .network-row-1 {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.96rem;
        font-weight: 800;
        color: #B45309 !important;
        margin-bottom: 4px;
    }}
    .network-row-2 {{
        padding-left: 26px;
        font-size: 0.98rem;
        font-weight: 800;
        color: #0F172A !important;
        line-height: 1.4;
    }}
    .network-highlight {{
        color: #E11D48 !important;
        font-weight: 900;
    }}

    div[data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
        border-bottom: none !important;
        margin-bottom: 1.2rem;
    }}
    div[data-baseweb="tab"] {{
        flex: 1;
        height: 50px;
        border: 2px solid #CBD5E1 !important;
        border-radius: 10px !important;
        background-color: #F1F5F9 !important;
        color: #475569 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: all 0.2s ease-in-out;
    }}
    div[data-baseweb="tab"][aria-selected="true"] {{
        background-color: #0F172A !important;
        border: 2.5px solid #E11D48 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.2);
    }}
    div[data-baseweb="tab-border"] {{
        display: none !important;
    }}

    div[data-baseweb="input"] {{
        border: 2px solid #94A3B8 !important;
        border-radius: 8px !important;
    }}
    div[data-baseweb="input"]:focus-within {{
        border: 2.5px solid #E11D48 !important;
    }}

    .stButton>button {{ 
        width: 100%; 
        border-radius: 10px; 
        font-weight: 800; 
        height: 3.2rem;
        font-size: 1.05rem;
        border: 2px solid #0F172A !important;
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        transition: all 0.15s ease;
    }}
    .stButton>button:active {{
        transform: scale(0.98);
        border-color: #E11D48 !important;
    }}

    .profile-avatar {{
        width: 76px;
        height: 76px;
        border-radius: 50%;
        object-fit: cover;
        border: 2.5px solid #D97706;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    }}
    .profile-placeholder {{
        width: 76px;
        height: 76px;
        border-radius: 50%;
        background-color: #E2E8F0;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 2.2rem;
        border: 2.5px solid #CBD5E1;
    }}

    .filter-card {{
        background-color: #F8FAFC;
        border: 1.5px solid #CBD5E1;
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 1rem;
    }}

    .pdf-preview-box {{
        border: 2px solid #CBD5E1;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 8px;
        margin-bottom: 12px;
        background-color: #F1F5F9;
    }}

    .intro-quote-box {{
        background: #F8FAFC;
        border-left: 3.5px solid #3B82F6;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 0.92rem;
        color: #1E293B;
        font-weight: 600;
        margin: 6px 0 8px 0;
        font-style: italic;
    }}
    .detail-tag {{
        display: inline-block;
        background: #F1F5F9;
        color: #334155;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid #E2E8F0;
    }}

    .terms-box {{
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 14px;
        font-size: 0.85rem;
        color: #475569;
        line-height: 1.5;
        margin-top: 10px;
        margin-bottom: 12px;
    }}

    .support-footer-card {{
        background-color: #F8FAFC;
        border: 1.5px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }}
    .support-header {{
        font-size: 0.98rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .support-desc {{
        font-size: 0.86rem;
        color: #64748B;
        line-height: 1.5;
        margin-bottom: 10px;
    }}
    .support-kakao-btn {{
        display: inline-block;
        background-color: #FEE500;
        color: #191919 !important;
        font-weight: 800;
        font-size: 0.88rem;
        padding: 9px 18px;
        border-radius: 6px;
        text-decoration: none;
        border: 1px solid #E6CF00;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}

    #MainMenu {{visibility: hidden !important;}}
    footer {{visibility: hidden !important;}}
    header {{visibility: hidden !important;}}
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = "https://xxiagepuzmukwcdnurhg.supabase.co"
SUPABASE_KEY = "sb_publishable_CCbsSoMbvLYh1y4xJ2zYEA_XxisldNn"

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

qp = st.query_params
saved_name_val = qp.get("saved_name", "")
saved_phone_val = qp.get("saved_phone", "")

def render_support_footer():
    st.markdown(f"""
        <div class="support-footer-card">
            <div class="support-header">
                <span>💬</span> <span>{BRAND_NAME_KR} 안심 전담 고객지원센터</span>
            </div>
            <div class="support-desc">
                서류 심사 문의, 비밀번호 변경 지원, 불량 매너 회원 신고 등 불편하신 점은 언제든 1:1 상담창구로 말씀해 주세요.
            </div>
            <a href="{KAKAO_CHAT_URL}" target="_blank" class="support-kakao-btn">
                💬 카카오톡 1:1 상담문의 열기
            </a>
        </div>
    """, unsafe_allow_html=True)

# [1. 로그인/가입 화면]
if not st.session_state.user_id:
    components.html("""
    <script>
    const savedName = localStorage.getItem('senior_match_name') || '';
    const savedPhone = localStorage.getItem('senior_match_phone') || '';
    const isRemembered = localStorage.getItem('senior_match_remember') === 'true';

    const urlParams = new URLSearchParams(window.parent.location.search);
    if (isRemembered && savedName && (!urlParams.get('saved_name') || !urlParams.get('saved_phone'))) {
        urlParams.set('saved_name', savedName);
        urlParams.set('saved_phone', savedPhone);
        window.parent.location.search = urlParams.toString();
    }
    </script>
    """, height=0)

    st.markdown(f"""
        <div class="brand-hero-header">
            <div class="brand-logo-en">{BRAND_NAME_EN}</div>
            <div class="brand-logo-kr">👑 {BRAND_NAME_KR}</div>
            <div class="brand-slogan">{BRAND_SLOGAN}</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="badge-box">
            <span class="badge-tag">엄격한 입회 기준</span>
            <div class="badge-text">남성 800점 이상 · 여성 600점 이상 <span class="highlight-score">신용점수</span> 인증 필수</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="premium-hero-box">
            <div class="hero-line1">
                <span>🏆</span> <span><span class="highlight-gold">신용이 검증된 분들</span>만 모시는 고품격 만남</span>
            </div>
            <div class="hero-line2">
                <span>💬</span> <span class="highlight-blue">75가지 가치관 문답</span>으로 깊이가 통하는 진짜 인연을 찾습니다.
            </div>
        </div>
        
        <div class="network-accent-card">
            <div class="network-row-1">
                <span>✨</span> <span>검증된 품격 있는 인연이 모일수록</span>
            </div>
            <div class="network-row-2">
                내 기준에 꼭 맞는 <span class="network-highlight">단 한 사람과의 만남</span>은 더욱 완벽해집니다.
            </div>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_join = st.tabs(["🔑 기존 회원 로그인", "📝 신규 회원가입"])

    with tab_login:
        login_name = st.text_input("가입하신 성함", value=saved_name_val, key="login_name")
        login_phone = st.text_input("가입하신 휴대폰 번호 (- 없이 숫자만)", value=saved_phone_val, placeholder="01012345678", key="login_phone")
        login_pwd = st.text_input("간편 비밀번호 (4~6자리)", type="password", placeholder="비밀번호 입력", key="login_pwd")
        
        remember_me = st.checkbox("성함 및 휴대폰 번호 기억하기", value=bool(saved_name_val and saved_phone_val))

        if st.button("안심 본인인증 로그인"):
            clean_lphone = re.sub(r'[^0-9]', '', login_phone.strip())
            if not login_name.strip() or not clean_lphone or not login_pwd.strip():
                st.error("성함, 휴대폰 번호, 비밀번호를 모두 입력해 주세요.")
            else:
                res = supabase.table("users").select("*")\
                    .eq("name", login_name.strip())\
                    .eq("phone", clean_lphone)\
                    .eq("password", login_pwd.strip())\
                    .execute()
                if res.data:
                    user_data = res.data[0]
                    if user_data.get("is_suspended"):
                        st.error("🚫 운영 정책 위반 또는 이용 제한 조치된 계정입니다. 고객센터에 문의해 주세요.")
                    else:
                        st.session_state.user_id = user_data["id"]
                        st.session_state.user_info = user_data

                        if remember_me:
                            components.html(f"""
                            <script>
                            localStorage.setItem('senior_match_name', '{login_name.strip()}');
                            localStorage.setItem('senior_match_phone', '{clean_lphone}');
                            localStorage.setItem('senior_match_remember', 'true');
                            </script>
                            """, height=0)
                        else:
                            components.html("""
                            <script>
                            localStorage.removeItem('senior_match_name');
                            localStorage.removeItem('senior_match_phone');
                            localStorage.setItem('senior_match_remember', 'false');
                            </script>
                            """, height=0)

                        st.rerun()
                else:
                    st.error("회원 정보 또는 비밀번호가 일치하지 않습니다. 다시 확인해 주세요.")

        with st.expander("❓ 비밀번호를 잊으셨나요? (비밀번호 재설정)"):
            st.caption("가입 시 등록하신 본인 정보(성함, 휴대폰 번호, 나이)를 확인 후 즉시 새 비밀번호로 변경합니다.")
            reset_name = st.text_input("성함 확인", key="reset_name")
            reset_phone = st.text_input("휴대폰 번호 확인 (- 없이 숫자만)", placeholder="01012345678", key="reset_phone")
            reset_age = st.number_input("가입 시 등록한 나이 (만 나이)", 40, 85, 58, key="reset_age")
            new_pwd = st.text_input("새로운 간편 비밀번호 (4~6자리)", type="password", placeholder="새 비밀번호 입력", key="new_pwd")

            if st.button("비밀번호 즉시 변경하기"):
                clean_rphone = re.sub(r'[^0-9]', '', reset_phone.strip())
                if not reset_name.strip() or not clean_rphone or len(new_pwd.strip()) < 4:
                    st.error("모든 항목을 올바르게 입력해 주세요. (비밀번호는 최소 4자리 이상)")
                else:
                    match_u = supabase.table("users").select("id, is_suspended").eq("name", reset_name.strip()).eq("phone", clean_rphone).eq("age", int(reset_age)).execute().data
                    if match_u:
                        if match_u[0].get("is_suspended"):
                            st.error("이용이 제한된 계정은 비밀번호를 변경할 수 없습니다.")
                        else:
                            user_target_id = match_u[0]["id"]
                            supabase.table("users").update({"password": new_pwd.strip()}).eq("id", user_target_id).execute()
                            st.success("🎉 비밀번호가 성공적으로 변경되었습니다! 위 로그인 창에서 새 비밀번호로 로그인해 주세요.")
                    else:
                        st.error("일치하는 회원 정보를 찾을 수 없습니다. 성함, 휴대폰 번호, 나이를 다시 확인해 주세요.")

    with tab_join:
        with st.form("join_form"):
            name = st.text_input("성명 (실명)")
            phone = st.text_input("휴대폰 번호 (- 없이 숫자만 입력)", placeholder="01012345678")
            pwd = st.text_input("간편 비밀번호 설정 (4~6자리)", type="password", placeholder="숫자 4~6자리 권장")
            gender = st.radio("성별", ["남", "여"], horizontal=True)
            age = st.number_input("나이 (만 나이)", 40, 85, 58)
            region = st.selectbox("활동 희망 지역", ["서울 강남/서초", "서울 강북/도심", "서울 서남/영등포", "경기 분당/판교", "경기 일산", "인천/부천", "기타"])
            credit_score = st.number_input("신용점수 입력 (남성 800+ / 여성 600+)", 0, 1000, 820)
            
            st.markdown("##### 💼 나의 라이프스타일 (선택)")
            job = st.text_input("현재 하시는 일 / 전문 분야", placeholder="예: 개인사업체 운영, 전문직, 은퇴 후 자문 등")
            hobbies = st.text_input("주말 취미 / 여가 활동", placeholder="예: 골프, 등산, 여행, 음악감상 등")
            intro = st.text_input("인생 2막을 여는 한 줄 소개", placeholder="예: 따뜻하고 성실한 마음으로 편안한 여생을 함께할 분을 찾습니다.")

            st.markdown("##### 🎯 3대 필수 가치관 문답")
            q1 = st.radio("1. 관계의 최종 형태?", ["법률혼 (서류상 정식 재혼 희망)", "사실혼 (합가 동거하되 서류 정리는 신중)", "LAT 동반자 (각자 주거를 유지하며 여행과 일상 공유)", "상황에 맞추어 유연하게 협의"])
            q38 = st.radio("2. 상대방 흡연 기준?", ["비흡연자만 가능 (전자담배 포함 절대 불가)", "전자담배까지는 양해 가능", "실외 흡연자라면 무관", "본인도 흡연자이므로 흡연 선호"])
            q56 = st.radio("3. 종교 차이 입장?", ["동일 종교 필수 (함께 신앙생활 희망)", "종교가 달라도 강요나 터치가 없다면 무관", "무교 선호", "상대방 종교를 존중하며 맞춰줄 의향 있음"])

            st.markdown("---")
            st.markdown("##### 🛡️ 안심 개인정보 및 신용 서류 파기 원칙")
            st.markdown("""
                <div class="terms-box">
                    <b>1. 개인정보 수집 및 이용 목적:</b> 본인 확인, 신용점수 기준 충족 여부 심사, 상호 동의 시에 한한 연락처 제공.<br>
                    <b>2. 신용 증빙 서류 100% 안전 원칙:</b> 제출된 증빙 서류는 관리자 진위 확인 완료 즉시 안전하게 비공개 처리되며 타인에게 절대 노출되지 않습니다.<br>
                    <b>3. 제3자 제공 동의:</b> 양측 모두 대화를 '수락'한 경우에만 상대방에게 안심 연락처가 공개됩니다.<br>
                    <b>4. 부적격 회원 조치:</b> 허위 서류 제출 및 불량 매너 회원은 사전 통보 없이 영구 이용 정지 처리됩니다.
                </div>
            """, unsafe_allow_html=True)
            
            agree_terms = st.checkbox("위 개인정보 처리방침 및 신용 서류 안전 관리 원칙에 동의합니다. (필수)")

            submit_join = st.form_submit_button("신용 검증 및 안심 가입 완료")
            if submit_join:
                clean_phone = re.sub(r'[^0-9]', '', phone.strip())
                cutoff = 800 if gender == "남" else 600
                
                if not agree_terms:
                    st.error("개인정보 처리방침 및 신용 서류 안전 관리 원칙에 동의해 주세요.")
                elif not name.strip():
                    st.error("성명을 입력해 주세요.")
                elif len(clean_phone) < 10:
                    st.error("올바른 휴대폰 번호를 입력해 주세요. (예: 01012345678)")
                elif len(pwd.strip()) < 4:
                    st.error("비밀번호는 최소 4자리 이상 설정해 주세요.")
                elif credit_score < cutoff:
                    st.error(f"입회 기준 미달: {gender}성은 신용점수 {cutoff}점 이상만 승인됩니다.")
                else:
                    dup = supabase.table("users").select("id").eq("phone", clean_phone).execute().data
                    if dup:
                        st.error("이미 등록된 휴대폰 번호입니다. '기존 회원 로그인'을 이용해 주세요.")
                    else:
                        new_u = supabase.table("users").insert({
                            "name": name.strip(),
                            "phone": clean_phone,
                            "password": pwd.strip(),
                            "gender": gender,
                            "age": int(age),
                            "region": region,
                            "credit_score": int(credit_score),
                            "job": job.strip() if job else None,
                            "hobbies": hobbies.strip() if hobbies else None,
                            "intro": intro.strip() if intro else None,
                            "is_verified": False,
                            "credit_status": "PENDING",
                            "is_admin": False,
                            "is_suspended": False
                        }).execute().data[0]
                        
                        uid = new_u["id"]
                        supabase.table("user_answers").insert([
                            {"user_id": uid, "question_num": 1, "answer_value": q1},
                            {"user_id": uid, "question_num": 38, "answer_value": q38},
                            {"user_id": uid, "question_num": 56, "answer_value": q56}
                        ]).execute()

                        st.session_state.user_id = uid
                        st.session_state.user_info = new_u
                        st.rerun()

    render_support_footer()

# [2. 메인 대시보드]
else:
    me = st.session_state.user_info

    st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px;">
            <div style="font-size:1.1rem; font-weight:900; color:#0F172A;">👑 {BRAND_NAME_KR}</div>
            <div style="font-size:0.75rem; font-weight:800; color:#D97706; letter-spacing:1px;">{BRAND_NAME_EN}</div>
        </div>
    """, unsafe_allow_html=True)

    top_col1, top_col2 = st.columns([1, 3])
    with top_col1:
        if me.get("photo_url"):
            st.markdown(f'<img src="{me["photo_url"]}" class="profile-avatar">', unsafe_allow_html=True)
        else:
            default_icon = "👨🏻‍💼" if me["gender"] == "남" else "👩🏻‍💼"
            st.markdown(f'<div class="profile-placeholder">{default_icon}</div>', unsafe_allow_html=True)
    with top_col2:
        st.markdown(f"#### **{me['name']}** 님 ({me['gender']}·{me['age']}세)")
        
        c_status = me.get("credit_status", "PENDING")
        if c_status == "APPROVED":
            st.markdown(f"🛡️ **<span style='color:#0284C7;'>공인 신용 인증 완료</span>** ({me['credit_score']}점)", unsafe_allow_html=True)
        elif c_status == "REJECTED":
            st.markdown(f"⚠️ **<span style='color:#EF4444;'>신용 증빙 서류 반려 (재제출 필요)</span>**", unsafe_allow_html=True)
        else:
            st.markdown(f"🛡️ **<span style='color:#D97706;'>안심 서류 검토 중</span>** ({me['credit_score']}점)", unsafe_allow_html=True)
        
        sub_info = f"📍 {me['region']}"
        if me.get("job"):
            sub_info += f" | 💼 {me['job']}"
        st.caption(sub_info)

    if me.get("intro"):
        st.markdown(f'<div class="intro-quote-box">“{me["intro"]}”</div>', unsafe_allow_html=True)

    with st.expander("✏️ 프로필 사진 · 상세소개 · 신용 서류 관리"):
        tab_p_edit, tab_p_pic, tab_p_doc = st.tabs(["📝 소개 및 취미 수정", "📸 프로필 사진 등록", "📄 신용 증빙 서류"])
        
        with tab_p_edit:
            new_job = st.text_input("현재 하시는 일 / 전문 분야", value=me.get("job") or "", placeholder="예: 개인사업체 운영, 전문직 등")
            new_hobbies = st.text_input("주말 취미 / 여가 활동", value=me.get("hobbies") or "", placeholder="예: 골프, 등산, 여행, 음악감상 등")
            new_intro = st.text_area("인생 2막을 여는 한 줄 소개", value=me.get("intro") or "", placeholder="상대방에게 나를 어필하는 따뜻한 소개글을 남겨보세요.", height=80)
            
            if st.button("내 프로필 정보 저장"):
                supabase.table("users").update({
                    "job": new_job.strip() if new_job else None,
                    "hobbies": new_hobbies.strip() if new_hobbies else None,
                    "intro": new_intro.strip() if new_intro else None
                }).eq("id", me["id"]).execute()
                
                me["job"] = new_job.strip() if new_job else None
                me["hobbies"] = new_hobbies.strip() if new_hobbies else None
                me["intro"] = new_intro.strip() if new_intro else None
                st.session_state.user_info = me
                st.success("프로필 정보가 성공적으로 변경되었습니다!")
                st.rerun()

        with tab_p_pic:
            up_pic = st.file_uploader("프로필 사진 선택 (JPG, PNG)", type=["jpg", "jpeg", "png"], key="user_avatar_up")
            if up_pic and st.button("프로필 사진 저장"):
                ext = up_pic.name.split(".")[-1].lower()
                fname = f"user_{me['id']}_{uuid.uuid4().hex[:6]}.{ext}"
                try:
                    supabase.storage.from_("avatars").upload(fname, up_pic.read(), {"content-type": f"image/{ext}"})
                    url = f"{SUPABASE_URL}/storage/v1/object/public/avatars/{fname}"
                    supabase.table("users").update({"photo_url": url}).eq("id", me["id"]).execute()
                    me["photo_url"] = url
                    st.session_state.user_info = me
                    st.success("프로필 사진이 저장되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"사진 저장 실패: {e}")

        with tab_p_doc:
            st.caption("토스/카카오페이 신용점수 캡처 이미지(JPG, PNG) 또는 나이스/KCB 공식 신용조회서(PDF)를 등록해 주세요.")
            up_doc = st.file_uploader("신용 증빙 서류 첨부 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"], key="user_credit_doc_up")
            if up_doc and st.button("증빙 서류 제출하기"):
                ext = up_doc.name.split(".")[-1].lower()
                fname = f"doc_{me['id']}_{uuid.uuid4().hex[:6]}.{ext}"
                content_type = "application/pdf" if ext == "pdf" else f"image/{ext}"
                try:
                    supabase.storage.from_("credit-docs").upload(fname, up_doc.read(), {"content-type": content_type})
                    url = f"{SUPABASE_URL}/storage/v1/object/public/credit-docs/{fname}"
                    supabase.table("users").update({
                        "credit_doc_url": url,
                        "credit_status": "PENDING"
                    }).execute()
                    me["credit_doc_url"] = url
                    me["credit_status"] = "PENDING"
                    st.session_state.user_info = me
                    st.success("증빙 서류가 정상 제출되었습니다. 관리자 심사 후 공인 인증 마크가 부여됩니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"서류 제출 실패: {e}")

    st.divider()

    tabs_list = ["💖 추천 피드", "📝 가치관 문답 이어하기", "📬 매칭 보관함"]
    if me.get("is_admin"):
        tabs_list.append("👑 관리자 콘솔")

    tabs = st.tabs(tabs_list)

    all_questions_raw = supabase.table("question_master").select("question_num, question_text, category, options").execute().data
    q_map = {q["question_num"]: q for q in all_questions_raw}

    my_ans_data = supabase.table("user_answers").select("question_num, answer_value").eq("user_id", me["id"]).execute().data
    my_answers = {item["question_num"]: item["answer_value"] for item in my_ans_data}

    # --- 탭 1: 이성 추천 피드 ---
    with tabs[0]:
        st.markdown("##### 🌟 가치관 일치율 순 추천 리스트")
        target_gender = "여" if me["gender"] == "남" else "남"
        candidates = supabase.table("users").select("*").eq("gender", target_gender).eq("is_suspended", False).execute().data

        sent_reqs = supabase.table("match_requests").select("receiver_id, status").eq("sender_id", me["id"]).execute().data
        sent_dict = {req["receiver_id"]: req["status"] for req in sent_reqs}

        if not candidates:
            st.info("현재 매칭 가능한 회원이 없습니다.")
        else:
            cand_scores = []
            for cand in candidates:
                cand_ans_data = supabase.table("user_answers").select("question_num, answer_value").eq("user_id", cand["id"]).execute().data
                cand_answers = {item["question_num"]: item["answer_value"] for item in cand_ans_data}

                common_keys = set(my_answers.keys()).intersection(set(cand_answers.keys()))
                score = int((sum(1 for k in common_keys if my_answers[k] == cand_answers[k]) / len(common_keys)) * 100) if common_keys else 0
                cand_scores.append((cand, cand_answers, common_keys, score))

            cand_scores.sort(key=lambda x: x[3], reverse=True)

            for cand, cand_answers, common_keys, score in cand_scores:
                with st.container():
                    c_col_img, c_col_info, c_col_score = st.columns([1, 2.5, 1])
                    with c_col_img:
                        if cand.get("photo_url"):
                            st.markdown(f'<img src="{cand["photo_url"]}" class="profile-avatar">', unsafe_allow_html=True)
                        else:
                            c_icon = "👩🏻‍💼" if cand["gender"] == "여" else "👨🏻‍💼"
                            st.markdown(f'<div class="profile-placeholder">{c_icon}</div>', unsafe_allow_html=True)
                    
                    with c_col_info:
                        st.markdown(f"**{cand['name']}** ({cand['age']}세 / {cand['region']})")
                        if cand.get("credit_status") == "APPROVED":
                            st.caption(f"🛡️ **공인 신용 인증 통과** ({cand['credit_score']}점)")
                        else:
                            st.caption(f"🛡️ 안심 서류 검토 중 ({cand['credit_score']}점)")
                    with c_col_score:
                        st.metric("일치율", f"{score}%")

                    tags_lifestyle = []
                    if cand.get("job"): tags_lifestyle.append(f"💼 {cand['job']}")
                    if cand.get("hobbies"): tags_lifestyle.append(f"⛳ {cand['hobbies']}")
                    if tags_lifestyle:
                        tags_html = " ".join([f'<span class="detail-tag">{t}</span>' for t in tags_lifestyle])
                        st.markdown(tags_html, unsafe_allow_html=True)

                    if cand.get("intro"):
                        st.markdown(f'<div class="intro-quote-box">“{cand["intro"]}”</div>', unsafe_allow_html=True)

                    tags = []
                    if my_answers.get(1) == cand_answers.get(1): tags.append("💍 혼인관 일치")
                    if my_answers.get(38) == cand_answers.get(38): tags.append("🚭 흡연관 일치")
                    if my_answers.get(56) == cand_answers.get(56): tags.append("🙏 종교관 일치")
                    if tags:
                        st.write(" ".join([f"`{t}`" for t in tags]))

                    with st.expander(f"🔍 {cand['name']} 님과의 가치관 문답 대조표 보기"):
                        if not common_keys:
                            st.caption("공통으로 응답한 문항이 아직 없습니다.")
                        else:
                            for q_num in sorted(list(common_keys)):
                                q_info = q_map.get(q_num, {})
                                q_title = q_info.get("question_text", f"문항 Q{q_num}")
                                my_val = my_answers[q_num]
                                cand_val = cand_answers[q_num]
                                is_same = (my_val == cand_val)

                                match_icon = "🟢 일치" if is_same else "⚪ 상이"
                                st.markdown(f"**[{match_icon}] {q_title}**")
                                st.markdown(f"- **나의 답변:** {my_val}")
                                st.markdown(f"- **상대방 답변:** {cand_val}")
                                st.write("")

                    req_status = sent_dict.get(cand["id"])
                    if req_status == "PENDING":
                        st.button(f"⏳ 답변을 기다리는 중 ({cand['name']})", key=f"btn_{cand['id']}", disabled=True)
                    elif req_status == "ACCEPTED":
                        cand_phone = cand.get("phone", "연락처 미등록")
                        st.success(f"🎉 대화 성사! {cand['name']} 님 연락처: **{cand_phone}**")
                    else:
                        if st.button(f"💌 {cand['name']} 님에게 대화 신청", key=f"btn_{cand['id']}"):
                            supabase.table("match_requests").insert({
                                "sender_id": me["id"],
                                "receiver_id": cand["id"],
                                "status": "PENDING"
                            }).execute()
                            st.toast(f"{cand['name']} 님에게 대화 신청을 보냈습니다!")
                            st.rerun()

                    st.divider()

    # --- 탭 2: 75문항 문답 이어하기 ---
    with tabs[1]:
        answered_qnums = list(my_answers.keys())
        st.progress(len(answered_qnums) / 75, text=f"전체 75문항 중 {len(answered_qnums)}개 답변 완료")

        unanswered = supabase.table("question_master")\
            .select("*")\
            .not_.in_("question_num", answered_qnums)\
            .order("priority", desc=True)\
            .order("question_num")\
            .limit(1)\
            .execute().data

        if unanswered:
            q = unanswered[0]
            st.info(f"카테고리: **{q['category']}** (문항 Q{q['question_num']})")
            st.markdown(f"#### **{q['question_text']}**")

            valid_options = q.get("options", [])
            if not valid_options:
                valid_options = ["예", "아니오"]

            selected_opt = st.radio("선택지:", valid_options, key=f"q_{q['question_num']}")

            if st.button("답변 저장하고 다음 질문"):
                supabase.table("user_answers").insert({
                    "user_id": me["id"],
                    "question_num": q["question_num"],
                    "answer_value": selected_opt
                }).execute()
                st.success("저장되었습니다!")
                st.rerun()
        else:
            st.success("🎉 모든 문항 답변을 완료하셨습니다.")

    # --- 탭 3: 대화 신청 보관함 ---
    with tabs[2]:
        st.markdown("##### 📬 매칭 신청 현황")
        inbox_tab1, inbox_tab2 = st.tabs(["내가 보낸 신청", "나에게 온 신청"])

        def get_match_status_text(status):
            if status == "PENDING":
                return "⏳ 답변을 기다리는 중"
            elif status == "ACCEPTED":
                return "🎉 대화 수락 완료"
            elif status == "REJECTED":
                return "소중한 마음만 간직"
            return status

        with inbox_tab1:
            sent_list = supabase.table("match_requests").select("id, receiver_id, status, created_at").eq("sender_id", me["id"]).execute().data
            if not sent_list:
                st.caption("아직 보낸 대화 신청이 없습니다.")
            else:
                for req in sent_list:
                    rcv_user = supabase.table("users").select("name, age, region, phone, photo_url, credit_status, job, intro").eq("id", req["receiver_id"]).execute().data
                    if rcv_user:
                        rcv = rcv_user[0]
                        status_kr = get_match_status_text(req['status'])
                        if req['status'] == 'ACCEPTED':
                            st.write(f"• **{rcv['name']}** 님 | 상태: `{status_kr}` | 📞 연락처: **{rcv.get('phone', '미등록')}**")
                        else:
                            st.write(f"• **{rcv['name']}** 님에게 보낸 신청 | 상태: `{status_kr}`")

        with inbox_tab2:
            received_list = supabase.table("match_requests").select("id, sender_id, status, created_at").eq("receiver_id", me["id"]).execute().data
            if not received_list:
                st.caption("도착한 대화 신청이 없습니다.")
            else:
                for req in received_list:
                    snd_user = supabase.table("users").select("id, name, age, region, credit_score, phone, photo_url, credit_status, job, hobbies, intro").eq("id", req["sender_id"]).execute().data
                    if snd_user:
                        u = snd_user[0]
                        u_ans_data = supabase.table("user_answers").select("question_num, answer_value").eq("user_id", u["id"]).execute().data
                        u_answers = {item["question_num"]: item["answer_value"] for item in u_ans_data}

                        common_keys = set(my_answers.keys()).intersection(set(u_answers.keys()))
                        score = int((sum(1 for k in common_keys if my_answers[k] == cand_answers[k]) / len(common_keys)) * 100) if common_keys else 0

                        rcv_c_img, rcv_c_info, rcv_c_score = st.columns([1, 2.5, 1])
                        with rcv_c_img:
                            if u.get("photo_url"):
                                st.markdown(f'<img src="{u["photo_url"]}" class="profile-avatar">', unsafe_allow_html=True)
                            else:
                                snd_icon = "👩🏻‍💼" if me["gender"] == "남" else "👨🏻‍💼"
                                st.markdown(f'<div class="profile-placeholder">{snd_icon}</div>', unsafe_allow_html=True)

                        with rcv_c_info:
                            st.markdown(f"**{u['name']}** ({u['age']}세 / {u['region']})")
                            if u.get("credit_status") == "APPROVED":
                                st.caption(f"🛡️ **공인 신용 인증 통과** ({u['credit_score']}점)")
                            else:
                                st.caption(f"🛡️ 안심 서류 검토 중 ({u['credit_score']}점)")
                        with rcv_c_score:
                            st.metric("일치율", f"{score}%")

                        tags_lifestyle = []
                        if u.get("job"): tags_lifestyle.append(f"💼 {u['job']}")
                        if u.get("hobbies"): tags_lifestyle.append(f"⛳ {u['hobbies']}")
                        if tags_lifestyle:
                            tags_html = " ".join([f'<span class="detail-tag">{t}</span>' for t in tags_lifestyle])
                            st.markdown(tags_html, unsafe_allow_html=True)

                        if u.get("intro"):
                            st.markdown(f'<div class="intro-quote-box">“{u["intro"]}”</div>', unsafe_allow_html=True)

                        tags = []
                        if my_answers.get(1) == u_answers.get(1): tags.append("💍 혼인관 일치")
                        if my_answers.get(38) == u_answers.get(38): tags.append("🚭 흡연관 일치")
                        if my_answers.get(56) == u_answers.get(56): tags.append("🙏 종교관 일치")
                        if tags:
                            st.write(" ".join([f"`{t}`" for t in tags]))

                        with st.expander(f"🔍 {u['name']} 님의 가치관 문답 대조표 확인하기"):
                            if not common_keys:
                                st.caption("공통으로 응답한 문항이 아직 없습니다.")
                            else:
                                for q_num in sorted(list(common_keys)):
                                    q_info = q_map.get(q_num, {})
                                    q_title = q_info.get("question_text", f"문항 Q{q_num}")
                                    my_val = my_answers[q_num]
                                    u_val = u_answers[q_num]
                                    is_same = (my_val == u_val)

                                    match_icon = "🟢 일치" if is_same else "⚪ 상이"
                                    st.markdown(f"**[{match_icon}] {q_title}**")
                                    st.markdown(f"- **나의 답변:** {my_val}")
                                    st.markdown(f"- **상대방({u['name']}) 답변:** {u_val}")
                                    st.write("")

                        if req['status'] == 'ACCEPTED':
                            st.success(f"대화 성사 완료! 📞 연락처: **{u.get('phone', '미등록')}**")
                        elif req['status'] == 'REJECTED':
                            st.caption("정중히 거절된 신청입니다.")
                        else:
                            col_acc, col_rej = st.columns(2)
                            with col_acc:
                                if st.button("수락", key=f"acc_{req['id']}"):
                                    supabase.table("match_requests").update({"status": "ACCEPTED"}).eq("id", req["id"]).execute()
                                    st.rerun()
                            with col_rej:
                                if st.button("거절", key=f"rej_{req['id']}"):
                                    supabase.table("match_requests").update({"status": "REJECTED"}).eq("id", req["id"]).execute()
                                    st.rerun()
                        st.divider()

    # --- 탭 4: 👑 관리자 콘솔 ---
    if me.get("is_admin"):
        with tabs[3]:
            st.markdown("### 👑 운영자 전용 통합 관리 콘솔")
            st.caption(f"{BRAND_NAME_KR} 신용 증빙 심사, 전체 고객 명부 및 권한/회원 제재를 관리합니다.")
            
            adm_sub1, adm_sub2, adm_sub3 = st.tabs(["📑 신용 서류 심사 대기열", "👥 전체 고객 명부", "🔑 회원 제재 및 관리자 권한"])
            
            # [1] 신용 심사 대기열
            with adm_sub1:
                pending_users = supabase.table("users").select("*").eq("credit_status", "PENDING").not_.is_("credit_doc_url", "null").execute().data
                
                if not pending_users:
                    st.info("현재 안심 서류 검토 대상이 없습니다.")
                else:
                    st.write(f"총 **{len(pending_users)}명**의 회원이 안심 서류 검토를 기다리고 있습니다.")
                    for pu in pending_users:
                        with st.container():
                            st.markdown(f"##### **{pu['name']}** 회원 ({pu['gender']} / {pu['age']}세 / {pu['region']})")
                            st.write(f"• 입력 신용점수: **{pu['credit_score']}점** | 📞 연락처: `{pu['phone']}`")
                            
                            doc_url = pu['credit_doc_url']
                            is_pdf = doc_url.lower().endswith(".pdf")
                            
                            st.write("• 제출된 증빙 서류:")
                            if is_pdf:
                                st.markdown(f"""
                                    <div class="pdf-preview-box">
                                        <iframe src="{doc_url}" width="100%" height="450px" style="border:none;"></iframe>
                                    </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f'<a href="{doc_url}" target="_blank" style="display:inline-block; margin-bottom:12px; font-weight:800; color:#0284C7; text-decoration:none;">📄 PDF 새 창에서 크게 보기 & 다운로드</a>', unsafe_allow_html=True)
                            else:
                                st.image(doc_url, caption=f"{pu['name']} 님의 제출 이미지", use_container_width=True)
                            
                            bcol1, bcol2 = st.columns(2)
                            with bcol1:
                                if st.button(f"✅ 공인 인증 승인 ({pu['name']})", key=f"adm_app_{pu['id']}"):
                                    supabase.table("users").update({"credit_status": "APPROVED", "is_verified": True}).eq("id", pu["id"]).execute()
                                    st.success(f"{pu['name']} 님의 신용 공인 인증이 승인되었습니다!")
                                    st.rerun()
                            with bcol2:
                                if st.button(f"❌ 서류 반려 ({pu['name']})", key=f"adm_rej_{pu['id']}"):
                                    supabase.table("users").update({"credit_status": "REJECTED"}).eq("id", pu["id"]).execute()
                                    st.warning(f"{pu['name']} 님의 서류를 반려 처리했습니다.")
                                    st.rerun()
                            st.divider()

            # [2] 전체 고객 데이터 명부
            with adm_sub2:
                st.markdown("##### 👥 회원 조회 및 실시간 검색")

                all_users = supabase.table("users").select("id, name, gender, age, region, credit_score, credit_status, phone, job, hobbies, intro, is_admin, is_suspended, created_at").execute().data

                if all_users:
                    raw_df = pd.DataFrame(all_users)
                    raw_df["phone"] = raw_df["phone"].fillna("-").astype(str)
                    raw_df["job"] = raw_df["job"].fillna("-").astype(str)
                    raw_df["hobbies"] = raw_df["hobbies"].fillna("-").astype(str)
                    raw_df["intro"] = raw_df["intro"].fillna("-").astype(str)
                    raw_df["credit_score"] = raw_df["credit_score"].fillna(0).astype(int)
                    raw_df["age"] = raw_df["age"].fillna(0).astype(int)
                    raw_df["created_at"] = raw_df["created_at"].fillna("-").apply(lambda x: str(x)[:10] if len(str(x)) >= 10 else str(x))

                    excel_export_df = raw_df.copy()
                    excel_export_df["권한"] = excel_export_df["is_admin"].apply(lambda x: "관리자" if x else "일반회원")
                    excel_export_df["계정상태"] = excel_export_df["is_suspended"].apply(lambda s: "이용정지" if s else "정상")
                    excel_export_df["신용심사상태"] = excel_export_df["credit_status"].apply(
                        lambda s: "공인인증완료" if s == "APPROVED" else ("서류반려" if s == "REJECTED" else "검토대기중")
                    )

                    export_cols = excel_export_df[[
                        "name", "gender", "age", "region", "job", "hobbies", "intro",
                        "credit_score", "신용심사상태", "계정상태", "phone", "권한", "created_at"
                    ]].rename(columns={
                        "name": "성명", "gender": "성별", "age": "나이", "region": "활동지역",
                        "job": "직업_전문분야", "hobbies": "취미_여가", "intro": "한줄소개",
                        "credit_score": "신용점수", "phone": "연락처", "created_at": "가입일자"
                    })

                    csv_data = export_cols.to_csv(index=False, encoding="utf-8-sig")
                    today_str = datetime.now().strftime("%Y%m%d")
                    st.download_button(
                        label="📥 전체 회원 명부 엑셀(CSV) 다운로드",
                        data=csv_data,
                        file_name=f"노블레스라온_회원명부_{today_str}.csv",
                        mime="text/csv"
                    )

                    with st.container():
                        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
                        f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 2])
                        with f_col1:
                            search_name = st.text_input("🔍 성명 검색", placeholder="이름 입력 (예: 김진호)")
                        with f_col2:
                            search_phone4 = st.text_input("📱 전화번호 뒷 4자리", placeholder="뒷 4자리 (예: 2222)")
                        with f_col3:
                            sort_option = st.selectbox(
                                "📊 정렬 기준",
                                ["가입일시 최신순", "가입일시 과거순", "신용점수 높은순", "신용점수 낮은순", "나이 많은순", "나이 적은순", "성명 가나다순"]
                            )
                        st.markdown('</div>', unsafe_allow_html=True)

                    df = raw_df.copy()
                    if search_name.strip():
                        df = df[df["name"].str.contains(search_name.strip(), na=False)]

                    if search_phone4.strip():
                        clean_p4 = re.sub(r'[^0-9]', '', search_phone4.strip())
                        df = df[df["phone"].apply(lambda p: p.endswith(clean_p4) if len(p) >= 4 else False)]

                    if sort_option == "가입일시 최신순":
                        df = df.sort_values(by="created_at", ascending=False)
                    elif sort_option == "가입일시 과거순":
                        df = df.sort_values(by="created_at", ascending=True)
                    elif sort_option == "신용점수 높은순":
                        df = df.sort_values(by="credit_score", ascending=False)
                    elif sort_option == "신용점수 낮은순":
                        df = df.sort_values(by="credit_score", ascending=True)
                    elif sort_option == "나이 많은순":
                        df = df.sort_values(by="age", ascending=False)
                    elif sort_option == "나이 적은순":
                        df = df.sort_values(by="age", ascending=True)
                    elif sort_option == "성명 가나다순":
                        df = df.sort_values(by="name", ascending=True)

                    total_found = len(df)
                    st.caption(f"검색 결과: 총 **{total_found}명**")

                    if total_found == 0:
                        st.warning("조건에 일치하는 회원이 없습니다.")
                    else:
                        page_size_col, page_no_col = st.columns([1.5, 2])
                        with page_size_col:
                            page_size = st.selectbox("페이지당 인원", [10, 20, 50], index=0)
                        
                        total_pages = math.ceil(total_found / page_size)
                        with page_no_col:
                            page_num = st.selectbox("페이지 이동", list(range(1, total_pages + 1)), index=0)

                        start_idx = (page_num - 1) * page_size
                        end_idx = start_idx + page_size
                        page_df = df.iloc[start_idx:end_idx].copy()

                        page_df["권한"] = page_df["is_admin"].apply(lambda x: "👑 관리자" if x else "일반회원")
                        page_df["계정상태"] = page_df["is_suspended"].apply(lambda s: "🚫 이용정지" if s else "정상")
                        page_df["심사상태"] = page_df["credit_status"].apply(
                            lambda s: "✅ 승인완료" if s == "APPROVED" else ("❌ 반려" if s == "REJECTED" else "🛡️ 안심 서류 검토 중")
                        )

                        display_df = page_df[[
                            "name", "gender", "age", "region", "job", "credit_score", "심사상태", "계정상태", "phone", "권한", "created_at"
                        ]].rename(columns={
                            "name": "성명", "gender": "성별", "age": "나이", "region": "지역", "job": "직업/전문분야",
                            "credit_score": "신용점수", "phone": "휴대폰 번호", "created_at": "가입일"
                        })

                        display_df.index = range(start_idx + 1, start_idx + len(display_df) + 1)

                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            height=380,
                            column_config={
                                "성명": st.column_config.TextColumn("성명", width="small"),
                                "성별": st.column_config.TextColumn("성별", width="small"),
                                "나이": st.column_config.NumberColumn("나이", width="small"),
                                "지역": st.column_config.TextColumn("지역", width="small"),
                                "직업/전문분야": st.column_config.TextColumn("직업/전문분야", width="medium"),
                                "신용점수": st.column_config.NumberColumn("신용점수", width="small"),
                                "심사상태": st.column_config.TextColumn("심사상태", width="medium"),
                                "계정상태": st.column_config.TextColumn("계정상태", width="small"),
                                "휴대폰 번호": st.column_config.TextColumn("휴대폰 번호", width="medium"),
                                "권한": st.column_config.TextColumn("권한", width="small"),
                                "가입일": st.column_config.TextColumn("가입일", width="small")
                            }
                        )
                else:
                    st.caption("등록된 회원이 없습니다.")

            # [3] 🔑 회원 제재 및 관리자 권한 관리
            with adm_sub3:
                st.markdown("##### 👥 회원 계정 제재(블랙리스트) 및 관리자 권한 설정")
                st.caption("불량 회원을 즉시 차단하거나, 신뢰할 수 있는 회원을 공동 관리자로 임명합니다.")
                
                users_list = supabase.table("users").select("id, name, phone, is_admin, is_suspended").order("name").execute().data
                
                if users_list:
                    def make_label(u):
                        status_str = "🚫이용정지" if u.get("is_suspended") else "정상"
                        role_str = "👑관리자" if u.get("is_admin") else "일반회원"
                        return f"{u['name']} ({u['phone']}) - [{status_str} / {role_str}]"

                    user_options = {make_label(u): u for u in users_list}
                    selected_label = st.selectbox("대상 회원 선택", list(user_options.keys()))
                    target_user = user_options[selected_label]
                    
                    st.write("")
                    st.markdown("###### 1. 계정 이용 상태 제어 (블랙리스트)")
                    col_ban1, col_ban2 = st.columns(2)
                    with col_ban1:
                        if not target_user.get("is_suspended"):
                            if target_user["id"] == me["id"]:
                                st.caption("본인 계정은 정지할 수 없습니다.")
                            else:
                                if st.button(f"🚫 {target_user['name']} 회원 이용 정지 (차단)", key=f"ban_{target_user['id']}"):
                                    supabase.table("users").update({"is_suspended": True}).eq("id", target_user["id"]).execute()
                                    st.warning(f"{target_user['name']} 회원이 이용 정지(차단) 처리되었습니다.")
                                    st.rerun()
                        else:
                            st.info("현재 이용 정지(차단) 상태입니다.")
                    with col_ban2:
                        if target_user.get("is_suspended"):
                            if st.button(f"✅ {target_user['name']} 회원 정지 해제 (정상 복원)", key=f"unban_{target_user['id']}"):
                                supabase.table("users").update({"is_suspended": False}).eq("id", target_user["id"]).execute()
                                st.success(f"{target_user['name']} 회원의 이용 정지가 해제되었습니다.")
                                st.rerun()

                    st.markdown("---")
                    st.markdown("###### 2. 관리자 권한 위임 및 회수")
                    col_adm_btn1, col_adm_btn2 = st.columns(2)
                    with col_adm_btn1:
                        if not target_user.get("is_admin"):
                            if st.button(f"👑 {target_user['name']} 님을 관리자로 임명"):
                                supabase.table("users").update({"is_admin": True}).eq("id", target_user["id"]).execute()
                                st.success(f"{target_user['name']} 님이 새로운 관리자로 임명되었습니다!")
                                st.rerun()
                        else:
                            st.info("이미 관리자 권한을 보유하고 있습니다.")

                    with col_adm_btn2:
                        if target_user.get("is_admin"):
                            if target_user["id"] == me["id"]:
                                st.caption("⚠️ 현재 로그인된 본인 계정은 관리자 해제할 수 없습니다.")
                            else:
                                if st.button(f"❌ {target_user['name']} 님 관리자 권한 회수"):
                                    supabase.table("users").update({"is_admin": False}).eq("id", target_user["id"]).execute()
                                    st.warning(f"{target_user['name']} 님의 관리자 권한이 회수되었습니다.")
                                    st.rerun()

    render_support_footer()

    st.markdown("---")
    if st.button("로그아웃"):
        st.session_state.user_id = None
        st.session_state.user_info = None
        st.rerun()
