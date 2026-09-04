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
                        st.error("🚫 운영 정책 위반 또는 이용 제한 조치된 계정입니다. 고객
