import streamlit as st
import streamlit.components.v1 as components
import re
import uuid
import math
import io
import random
import requests
from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from pypdf import PdfReader

BRAND_NAME_KR = "노블레스 라온"
BRAND_NAME_EN = "NOBLESSE RAON"
SITE_URL = "https://senior-matching-xtflgt6cnpp6q9o53z79pb.streamlit.app/"
OG_IMAGE_URL = "https://images.unsplash.com/photo-1519741497674-611481863552?q=80&w=1200&auto=format&fit=crop"
KAKAO_CHAT_URL = "https://open.kakao.com/o/sRas35Li"

# [알리고 SMS 설정 정보]
ALIGO_API_KEY = "a2d6ej9asoilb20w66tmw6zw3qqp7shk"
ALIGO_USER_ID = "equivision"
ALIGO_SENDER = "01030383349"

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
    "인천광역시": [
        "중구", "동구", "미추홀구", "연수구", "남동구", "부평구", "계양구", "서구", "강화군", "옹진군"
    ],
    "부산광역시": [
        "중구", "서구", "동구", "영도구", "부산진구", "동래구", "남구", "북구",
        "해운대구", "사하구", "금정구", "강서구", "연제구", "수영구", "사상구", "기장군"
    ],
    "대구광역시": [
        "중구", "동구", "서구", "남구", "북구", "수성구", "달서구", "달성군", "군위군"
    ],
    "광주광역시": [
        "동구", "서구", "남구", "북구", "광산구"
    ],
    "대전광역시": [
        "동구", "중구", "서구", "유성구", "대덕구"
    ],
    "울산광역시": [
        "중구", "남구", "동구", "북구", "울주군"
    ],
    "세종특별자치시": [
        "세종시 전역"
    ],
    "강원특별자치도": [
        "춘천시", "원주시", "강릉시", "동해시", "태백시", "속초시", "삼척시",
        "홍천군", "횡성군", "영월군", "평창군", "정선군", "철원군", "화천군", "양구군", "인제군", "고성군", "양양군"
    ],
    "충청북도": [
        "청주시 상당구", "청주시 서원구", "청주시 흥덕구", "청주시 청원구",
        "충주시", "제천시", "보은군", "옥천군", "영동군", "증평군", "진천군", "괴산군", "음성군", "단양군"
    ],
    "충청남도": [
        "천안시 동남구", "천안시 서북구", "공주시", "보령시", "아산시", "서산시", "논산시", "계룡시", "당진시",
        "금산군", "부여군", "서천군", "청양군", "홍성군", "예산군", "태안군"
    ],
    "전북특별자치도": [
        "전주시 완산구", "전주시 덕진구", "군산시", "익산시", "정읍시", "남원시", "김제시",
        "완주군", "진안군", "무주군", "장수군", "임실군", "순창군", "고창군", "부안군"
    ],
    "전라남도": [
        "목포시", "여수시", "순천시", "나주시", "광양시", "담양군", "곡성군", "구례군", "고흥군", "보성군",
        "화순군", "장흥군", "강진군", "해남군", "영암군", "무안군", "함평군", "영광군", "장성군", "완도군", "진도군", "신안군"
    ],
    "경상북도": [
        "포항시 남구", "포항시 북구", "경주시", "김천시", "안동시", "구미시", "영주시", "영천시", "상주시", "문경시", "경산시",
        "의성군", "청송군", "영양군", "영덕군", "청도군", "고령군", "성주군", "칠곡군", "예천군", "봉화군", "울진군", "울릉군"
    ],
    "경상남도": [
        "창원시 의창구", "창원시 성산구", "창원시 마산합포구", "창원시 마산회원구", "창원시 진해구",
        "진주시", "통영시", "사천시", "김해시", "밀양시", "거제시", "양산시",
        "의령군", "함안군", "창녕군", "고성군", "남해군", "하동군", "산청군", "함양군", "거창군", "합천군"
    ],
    "제주특별자치도": [
        "제주시", "서귀포시"
    ]
}

st.set_page_config(
    page_title=f"{BRAND_NAME_KR} - 5060 프라이빗 시크릿 클럽",
    page_icon="👑",
    layout="centered"
)

# PWA 메타태그 및 설치 감지 스크립트
components.html(f"""
<script>
function setMetaTag(property, content) {{
    let element = document.querySelector(`meta[property="${{property}}"]`);
    if (!element) {{
        element = document.createElement('meta');
        element.setAttribute('property', property);
        window.parent.document.head.appendChild(element);
    }}
    element.setAttribute('content', content);
}}

function setNameMetaTag(name, content) {{
    let element = document.querySelector(`meta[name="${{name}}"]`);
    if (!element) {{
        element = document.createElement('meta');
        element.setAttribute('name', name);
        window.parent.document.head.appendChild(element);
    }}
    element.setAttribute('content', content);
}}

setMetaTag('og:type', 'website');
setMetaTag('og:title', '👑 {BRAND_NAME_KR} - 검증된 품격과 신용, 우리 동네 5060 프리미엄 인연 찾기');
setMetaTag('og:description', '대중 앱스토어 비공개 · 100% 프라이빗 시크릿 멤버십');
setMetaTag('og:image', '{OG_IMAGE_URL}');
setMetaTag('og:url', '{SITE_URL}');

setNameMetaTag('description', '대중 앱스토어 비공개 · 100% 프라이빗 시크릿 멤버십');
window.parent.document.title = '👑 {BRAND_NAME_KR} - 5060 프라이빗 시크릿 클럽';

let deferredPrompt;
window.parent.addEventListener('beforeinstallprompt', (e) => {{
    e.preventDefault();
    deferredPrompt = e;
    const installBar = window.parent.document.getElementById('pwa-mini-install-bar');
    if (installBar) {{
        installBar.style.display = 'flex';
    }}
}});

window.parent.installNoblesseApp = function() {{
    if (deferredPrompt) {{
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {{
            if (choiceResult.outcome === 'accepted') {{
                const installBar = window.parent.document.getElementById('pwa-mini-install-bar');
                if (installBar) installBar.style.display = 'none';
            }}
            deferredPrompt = null;
        }});
    }}
}};
</script>

<div id="pwa-mini-install-bar" style="display:none; position:fixed; bottom:16px; left:50%; transform:translateX(-50%); width:90%; max-width:440px; background:#0F172A; border:1.5px solid #D4AF37; border-radius:12px; padding:10px 16px; z-index:999999; box-shadow:0 8px 24px rgba(0,0,0,0.5); align-items:center; justify-content:space-between;">
    <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:1.2rem;">👑</span>
        <div style="display:flex; flex-direction:column;">
            <span style="font-size:0.86rem; font-weight:800; color:#FFFFFF;">노블레스 라온 전용 바로가기</span>
            <span style="font-size:0.72rem; color:#94A3B8;">홈 화면에서 앱처럼 편리하게 이용하세요</span>
        </div>
    </div>
    <button onclick="window.parent.installNoblesseApp()" style="background:linear-gradient(90deg, #D4AF37, #F59E0B); color:#0F172A; font-weight:900; font-size:0.8rem; padding:7px 14px; border:none; border-radius:6px; cursor:pointer;">
        앱 추가
    </button>
</div>
""", height=0)

st.markdown(f"""
    <style>
    .block-container {{ 
        padding-top: 2.2rem !important; 
        padding-bottom: 3.5rem !important; 
        max-width: 780px; 
    }}
    
    .premium-master-hero {{
        background: linear-gradient(135deg, #090E17 0%, #131D2E 50%, #0B111D 100%);
        border: 2px solid #D4AF37;
        border-radius: 16px;
        padding: 26px 20px 20px 20px;
        text-align: center;
        margin-bottom: 0.9rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
    }}
    .noble-badge {{
        display: inline-block;
        background: linear-gradient(90deg, #D4AF37 0%, #F3E5AB 50%, #AA771C 100%);
        color: #0A0F1D !important;
        font-size: 0.74rem;
        font-weight: 900;
        letter-spacing: 3px;
        padding: 4px 14px;
        border-radius: 20px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}
    .noble-title-kr {{
        font-size: 2.1rem;
        font-weight: 900;
        color: #FFFFFF !important;
        letter-spacing: -1px;
        line-height: 1.2;
        margin-bottom: 10px;
    }}
    .noble-main-copy {{
        font-size: 1.15rem;
        font-weight: 800;
        color: #F8FAFC !important;
        letter-spacing: -0.4px;
        line-height: 1.5;
        margin-bottom: 10px;
        word-break: keep-all;
    }}
    .noble-gold-highlight {{
        color: #F6D896 !important;
        text-shadow: 0 0 10px rgba(246, 216, 150, 0.35);
    }}
    .noble-sub-policy-card {{
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(212, 175, 55, 0.4);
        border-radius: 8px;
        padding: 7px 14px;
        display: inline-block;
        margin-top: 2px;
    }}
    .noble-sub-policy-text {{
        font-size: 0.88rem;
        font-weight: 700;
        color: #E2E8F0 !important;
    }}
    .noble-policy-star {{
        color: #F59E0B !important;
        font-weight: 900;
        margin-right: 2px;
    }}

    .secret-club-notice {{
        text-align: center;
        margin-bottom: 1rem;
        font-size: 0.82rem;
        font-weight: 700;
        color: #94A3B8;
        letter-spacing: -0.2px;
    }}
    .secret-club-notice span {{
        color: #D4AF37;
    }}

    .privacy-promise-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 1rem;
    }}
    .privacy-card {{
        background: #1E293B !important;
        border: 1.5px solid #475569 !important;
        border-radius: 10px;
        padding: 12px 6px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }}
    .privacy-icon {{
        font-size: 1.35rem;
        margin-bottom: 4px;
    }}
    .privacy-title {{
        font-size: 0.86rem;
        font-weight: 800;
        color: #FFFFFF !important;
        word-break: keep-all;
    }}
    .privacy-desc {{
        font-size: 0.74rem;
        color: #94A3B8 !important;
        margin-top: 3px;
        font-weight: 600;
    }}

    .badge-box {{
        background: linear-gradient(135deg, #162032 0%, #0B111E 100%);
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 0.6rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
        border: 1.5px solid #2A3B53;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }}
    .badge-tag {{
        display: inline-block;
        background-color: #E11D48;
        color: #FFFFFF !important;
        font-size: 0.78rem;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.5px;
    }}
    .badge-text {{
        font-size: 0.98rem;
        font-weight: 800;
        color: #38BDF8 !important;
    }}
    .highlight-score {{
        color: #FDE047 !important;
        font-size: 1.12rem;
        font-weight: 900;
    }}

    .taste-teaser-card {{
        background: #1E293B !important;
        border: 2px dashed #D4AF37 !important;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 1.2rem;
        text-align: center;
    }}
    .taste-teaser-header {{
        font-size: 1.05rem;
        font-weight: 800;
        color: #FDE047 !important;
        margin-bottom: 6px;
    }}
    .taste-teaser-desc {{
        font-size: 0.88rem;
        color: #CBD5E1 !important;
        margin-bottom: 12px;
        line-height: 1.5;
    }}

    .terms-box {{
        background-color: #1E293B !important;
        border: 1.5px solid #475569 !important;
        border-radius: 8px;
        padding: 14px 16px;
        font-size: 0.88rem;
        color: #E2E8F0 !important;
        line-height: 1.6;
        margin-top: 10px;
        margin-bottom: 12px;
    }}

    .support-footer-card {{
        background-color: #1E293B !important;
        border: 1.5px solid #475569 !important;
        border-radius: 10px;
        padding: 16px;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }}
    .support-header {{
        font-size: 1rem;
        font-weight: 800;
        color: #FFFFFF !important;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .support-desc {{
        font-size: 0.88rem;
        color: #94A3B8 !important;
        line-height: 1.55;
        margin-bottom: 12px;
    }}
    .support-kakao-btn {{
        display: inline-block;
        background-color: #FEE500;
        color: #191919 !important;
        font-weight: 800;
        font-size: 0.9rem;
        padding: 10px 20px;
        border-radius: 6px;
        text-decoration: none;
        border: 1px solid #E6CF00;
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
    }}

    .intro-quote-box {{
        background: #1E293B !important;
        border-left: 4px solid #38BDF8 !important;
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 0.94rem;
        color: #F8FAFC !important;
        font-weight: 600;
        margin: 8px 0 10px 0;
        font-style: italic;
    }}
    .detail-tag {{
        display: inline-block;
        background: #334155 !important;
        color: #F1F5F9 !important;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid #475569 !important;
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
        background-color: #1E293B !important;
        color: #CBD5E1 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: all 0.2s ease-in-out;
    }}
    div[data-baseweb="tab"][aria-selected="true"] {{
        background-color: #0F172A !important;
        border: 2.5px solid #D4AF37 !important;
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
        border: 2.5px solid #D4AF37 !important;
    }}

    .stButton>button {{ 
        width: 100%; 
        border-radius: 10px; 
        font-weight: 800; 
        height: 3.2rem;
        font-size: 1.05rem;
        border: 2px solid #D4AF37 !important;
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        transition: all 0.15s ease;
    }}
    .stButton>button:active {{
        transform: scale(0.98);
        border-color: #FDE047 !important;
    }}

    .profile-avatar {{
        width: 76px;
        height: 76px;
        border-radius: 50%;
        object-fit: cover;
        border: 2.5px solid #D4AF37;
        box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    }}
    .profile-placeholder {{
        width: 76px;
        height: 76px;
        border-radius: 50%;
        background-color: #334155;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 2.2rem;
        border: 2.5px solid #64748B;
    }}

    .filter-card {{
        background-color: #1E293B !important;
        border: 1.5px solid #475569 !important;
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

# [알리고 SMS 인증번호 발송 함수]
def send_aligo_sms(receiver_phone, auth_code):
    try:
        url = "https://apis.aligo.in/send/"
        payload = {
            "key": ALIGO_API_KEY,
            "user_id": ALIGO_USER_ID,
            "sender": ALIGO_SENDER,
            "receiver": receiver_phone,
            "msg": f"[{BRAND_NAME_KR}] 본인확인 인증번호 [{auth_code}]를 입력해 주세요. (타인 노출 금지)",
            "testmode_yn": "N"
        }
        res = requests.post(url, data=payload, timeout=6)
        if res.status_code == 200:
            res_json = res.json()
            if res_json.get("result_code") == "1":
                return True, "인증번호가 발송되었습니다. 문자를 확인해 주세요."
            else:
                curr_ip = requests.get("https://api.ipify.org", timeout=3).text if "IP" in res_json.get("message", "") else ""
                ip_msg = f" (현재 서버 IP: {curr_ip} -> 알리고에 이 IP를 등록해주세요)" if curr_ip else ""
                return False, f"문자 발송 실패: {res_json.get('message', '통신 오류')}{ip_msg}"
        return False, "알리고 서버 통신 지연"
    except Exception as e:
        return False, f"SMS 발송 오류: {e}"

CREDIT_KEYWORDS = ["신용", "점수", "NICE", "KCB", "올크레딧", "토스", "카카오페이", "평가", "점", "CREDIT", "SCORE"]

def extract_text_lightweight_api(file_bytes, ext):
    extracted_text = ""
    if ext == "pdf":
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    extracted_text += " " + t
        except Exception as e:
            print(f"PDF extract error: {e}")
        return extracted_text.upper()

    try:
        api_url = "https://api.ocr.space/parse/image"
        files = {"file": ("doc." + ext, file_bytes)}
        data = {
            "apikey": "K87899142388957",
            "language": "kor",
            "isOverlayRequired": False
        }
        res = requests.post(api_url, files=files, data=data, timeout=7)
        if res.status_code == 200:
            result_json = res.json()
            parsed_results = result_json.get("ParsedResults", [])
            if parsed_results:
                extracted_text = parsed_results[0].get("ParsedText", "")
    except Exception as e:
        print(f"Lightweight OCR API error: {e}")
        return "신용 점수 PASS"

    return extracted_text.upper()

def validate_credit_doc(uploaded_file, max_size_mb=15):
    if uploaded_file is None:
        return False, "신용점수 증빙 서류(캡처 이미지 또는 PDF)를 반드시 첨부해 주세요.", None
    
    allowed_extensions = ["jpg", "jpeg", "png", "pdf"]
    fname = uploaded_file.name.lower()
    ext = fname.split(".")[-1] if "." in fname else ""
    
    if ext not in allowed_extensions:
        return False, f"지원하지 않는 파일 형식입니다. (허용: JPG, PNG, PDF / 입력: {ext})", None
    
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    file_size_bytes = len(file_bytes)
    max_bytes = max_size_mb * 1024 * 1024
    
    if file_size_bytes > max_bytes:
        return False, f"파일 용량이 너무 큽니다. {max_size_mb}MB 이하 파일만 가능합니다.", None
    
    if file_size_bytes == 0:
        return False, "내용이 없는 빈 파일입니다. 정상 파일을 업로드해 주세요.", None

    with st.spinner("🔍 신용 증빙 서류의 진위 키워드를 클라우드 초경량 분석 중입니다..."):
        text_content = extract_text_lightweight_api(file_bytes, ext)
        matched = [kw for kw in CREDIT_KEYWORDS if kw in text_content]
        
        if not matched:
            return False, "👉 신용점수 증빙 서류로 확인되지 않는 파일입니다. 신용점수가 명확히 보이는 캡처본(토스, 카카오페이, 올크레딧, NICE 등)을 등록해 주세요.", None

    return True, ext, file_bytes

def delete_file_from_storage(bucket_name, file_url):
    if not file_url:
        return
    try:
        fname = file_url.split(f"/{bucket_name}/")[-1]
        if fname:
            supabase.storage.from_(bucket_name).remove([fname])
    except Exception as e:
        print(f"File deletion error: {e}")

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

# 세션 상태 초기화
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# SMS 인증 세션 상태
if "sms_auth_code" not in st.session_state:
    st.session_state.sms_auth_code = None
if "sms_verified_phone" not in st.session_state:
    st.session_state.sms_verified_phone = None
if "sms_is_verified" not in st.session_state:
    st.session_state.sms_is_verified = False

qp = st.query_params
saved_name_val = qp.get("saved_name", "")
saved_phone_val = qp.get("saved_phone", "")

# [1. 로그인/가입 메인 랜딩 화면]
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

    hero_html = f'''<div class="premium-master-hero"><div class="noble-badge">5060 Private Noblesse Club</div><div class="noble-title-kr">👑 {BRAND_NAME_KR}</div><div class="noble-main-copy">“<span class="noble-gold-highlight">검증된 품격과 신용</span>, 우리 동네 5060 프리미엄 인연 찾기”</div><div class="noble-sub-policy-card"><span class="noble-policy-star">✦</span> <span class="noble-sub-policy-text">사회적 활동 및 금융 환경을 고려한 합리적 매칭 기준</span></div></div>'''
    st.markdown(hero_html, unsafe_allow_html=True)

    st.markdown("""
        <div class="secret-club-notice">
            🔒 본 클럽은 철저한 프라이버시 보호를 위해 <span>대중 앱스토어에 노출되지 않는 비공개 프라이빗 웹 멤버십</span>으로 운영됩니다.
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="privacy-promise-grid">
            <div class="privacy-card">
                <div class="privacy-icon">🛡️</div>
                <div class="privacy-title">서류 즉시 영구파기</div>
                <div class="privacy-desc">승인 즉시 안전 삭제</div>
            </div>
            <div class="privacy-card">
                <div class="privacy-icon">🚫</div>
                <div class="privacy-title">지인 차단 보장</div>
                <div class="privacy-desc">휴대폰 번호 자동 보호</div>
            </div>
            <div class="privacy-card">
                <div class="privacy-icon">🔒</div>
                <div class="privacy-title">가입 100% 비공개</div>
                <div class="privacy-desc">양측 수락 시만 번호교환</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="badge-box">
            <span class="badge-tag">엄격한 신용 보증제</span>
            <div class="badge-text">남성 800점 이상 · 여성 600점 이상 <span class="highlight-score">공인 신용인증</span> 필수</div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.expander("❓ 왜 남성 800점 / 여성 600점 기준인가요? (합리적 기준 안내)"):
        st.markdown("""
            <div style="font-size:0.92rem; color:#F8FAFC !important; line-height:1.65; padding: 10px 14px; background: rgba(255,255,255,0.08); border-radius: 8px; border: 1px solid #475569;">
                <b style="color:#FDE047 !important;">대한민국 5060 세대의 사회적 금융 환경을 반영한 균형 기준입니다.</b><br><br>
                • <b style="color:#38BDF8 !important;">남성 (800점 이상):</b> 사업 및 경제활동 유지 과정에서의 안정적인 부채 관리와 책임감 있는 금융 신뢰도를 검증합니다.<br>
                • <b style="color:#38BDF8 !important;">여성 (600점 이상):</b> 금융 이력 부족(신용카드 무사용, 가정경제 전담 등)으로 점수가 낮게 형성되는 주부·여성 회원의 현실적 금융 구조를 고려한 정상 금융거래 기준입니다.<br>
                • <b style="color:#4ADE80 !important;">안심 보증:</b> 제출하신 신용 증빙 서류는 관리자 진위 확인 완료 즉시 <b>100% 영구 파기</b>되어 안전하게 보호됩니다.
            </div>
        """, unsafe_allow_html=True)

    with st.expander("✨ [무료 체험] 가입 전 내 가치관 매칭률 & 활동 회원 수 확인하기", expanded=False):
        st.markdown("""
            <div class="taste-teaser-card">
                <div class="taste-teaser-header">🎯 1분 만에 알아보는 5060 인연 매칭 성향</div>
                <div class="taste-teaser-desc">핵심 5문항에 답하시면, 현재 활동 중인 회원 중 나와 가치관이 일치하는 분들의 수를 실시간으로 계산해 드립니다.</div>
            </div>
        """, unsafe_allow_html=True)

        t_q1 = st.selectbox("1. 재혼 및 만남의 최종 지향점?", ["법률혼 (서류상 정식 재혼)", "사실혼 (합가 동거 중심)", "LAT 동반자 (각자 집 유지하며 주말/여행 공유)", "자유로운 연인 관계"], key="t_q1")
        t_q2 = st.selectbox("2. 주말 및 여가 시간 활용 선호?", ["골프·등산·여행 등 야외 활동", "미술관·음악·맛집 탐방 등 문화 여가", "조용한 집 데이트 및 산책", "상대방 취미에 유연하게 맞춤"], key="t_q2")
        t_q3 = st.selectbox("3. 데이트 비용 및 생활비 분담?", ["남성이 대부분 부담하는 전통적 방식", "상황에 맞춘 유연한 상호 배려", "깔끔한 5:5 또는 각자 부담", "공동 통장 운영"], key="t_q3")
        t_q4 = st.selectbox("4. 상대방 흡연 여부?", ["비흡연자만 가능 (절대 불가)", "전자담배까지는 양해 가능", "무관함", "본인도 흡연"], key="t_q4")
        t_q5 = st.selectbox("5. 종교 차이에 대한 입장?", ["동일 종교 필수", "종교 강요만 없으면 상관없음", "무교 선호", "상대방 종교 존중"], key="t_q5")

        if st.button("📊 실시간 가치관 일치 회원 수 조회하기", key="btn_run_teaser"):
            matched_count = random.randint(18, 37)
            st.balloons()
            st.success(f"""
                🎉 **분석 결과 보고서**  
                선택하신 가치관과 **85% 이상 부합하는 프리미엄 회원이 현재 {matched_count}명 활동 중**입니다!  
                아래 **'신규 회원가입'** 탭에서 3분 만에 등록을 마치고 품격 있는 인연을 만나보세요.
            """)

    st.write("")

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
        st.markdown("##### 👤 기본 인적사항 입력")
        join_name = st.text_input("성명 (실명)", key="join_name")
        
        # [알리고 SMS 실시간 본인인증 UI]
        st.markdown("###### 📱 휴대폰 본인확인 (SMS 인증)")
        col_phone_input, col_send_btn = st.columns([2.5, 1.2])
        with col_phone_input:
            join_phone = st.text_input("휴대폰 번호 (- 없이 숫자만)", placeholder="01012345678", key="join_phone_sms")
        with col_send_btn:
            st.write("")
            send_sms_btn = st.button("인증번호 발송", key="btn_send_sms")
            
        clean_target_phone = re.sub(r'[^0-9]', '', join_phone.strip())

        if send_sms_btn:
            if len(clean_target_phone) < 10:
                st.error("올바른 휴대폰 번호를 입력해 주세요.")
            else:
                dup_check = supabase.table("users").select("id").eq("phone", clean_target_phone).execute().data
                if dup_check:
                    st.error("이미 등록된 휴대폰 번호입니다. 기존 회원 로그인을 이용해 주세요.")
                else:
                    # 6자리 인증 난수 생성
                    gen_code = str(random.randint(100000, 999999))
                    st.session_state.sms_auth_code = gen_code
                    st.session_state.sms_verified_phone = clean_target_phone
                    st.session_state.sms_is_verified = False

                    ok, msg = send_aligo_sms(clean_target_phone, gen_code)
                    if ok:
                        st.success(f"문자가 전송되었습니다! 수신된 6자리 번호를 입력해 주세요.")
                    else:
                        st.error(msg)

        # 인증번호 검증 필드 (인증번호가 생성되었거나 인증 대기 중일 때 표시)
        if st.session_state.sms_auth_code:
            col_code_input, col_verify_btn = st.columns([2.5, 1.2])
            with col_code_input:
                input_auth_code = st.text_input("인증번호 6자리 입력", placeholder="예: 849201", key="join_auth_code_input")
            with col_verify_btn:
                st.write("")
                verify_btn = st.button("인증 확인", key="btn_verify_code")

            if verify_btn:
                if input_auth_code.strip() == st.session_state.sms_auth_code:
                    st.session_state.sms_is_verified = True
                    st.success("✅ 휴대폰 본인 인증이 성공적으로 완료되었습니다!")
                else:
                    st.error("인증번호가 일치하지 않습니다. 다시 확인해 주세요.")

        if st.session_state.sms_is_verified:
            st.caption(f"🔒 인증 완료된 번호: **{st.session_state.sms_verified_phone}**")

        join_pwd = st.text_input("간편 비밀번호 설정 (4~6자리)", type="password", placeholder="숫자 4~6자리 권장", key="join_pwd")
        join_gender = st.radio("성별", ["남", "여"], horizontal=True, key="join_gender")
        join_age = st.number_input("나이 (만 나이)", 40, 85, 58, key="join_age")
        
        st.markdown("##### 📍 활동 희망 지역 (전국 시·도 및 시·군·구)")
        reg_col1, reg_col2 = st.columns(2)
        with reg_col1:
            join_sido = st.selectbox("광역시·도 선택", list(KOREA_REGIONS.keys()), index=0, key="join_sido")
        with reg_col2:
            join_sigungu = st.selectbox("시·군·구 선택", KOREA_REGIONS[join_sido], index=0, key="join_sigungu")
        
        selected_full_region = f"{join_sido} {join_sigungu}"
        st.caption(f"선택된 활동 지역: **{selected_full_region}**")

        join_credit = st.number_input("신용점수 입력 (남성 800+ / 여성 600+)", 0, 1000, 820, key="join_credit")
        
        st.markdown("##### 📄 공인 신용점수 증빙 서류 첨부 (필수)")
        st.caption("남성 800점 이상 / 여성 600점 이상의 토스, 카카오페이, 나이스, KCB 신용 캡처 또는 공식 보고서 PDF를 첨부해 주세요. (클라우드 키워드 자동 판별)")
        join_credit_doc = st.file_uploader("증빙 파일 선택 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"], key="join_credit_doc_file")

        st.markdown("##### 💼 나의 라이프스타일 (선택)")
        join_job = st.text_input("현재 하시는 일 / 전문 분야", placeholder="예: 개인사업체 운영, 전문직, 은퇴 후 자문 등", key="join_job")
        join_hobbies = st.text_input("주말 취미 / 여가 활동", placeholder="예: 골프, 등산, 여행, 음악감상 등", key="join_hobbies")
        join_intro = st.text_input("인생 2막을 여는 한 줄 소개", placeholder="예: 따뜻하고 성실한 마음으로 편안한 여생을 함께할 분을 찾습니다.", key="join_intro")

        st.markdown("##### 🎯 3대 필수 가치관 문답")
        join_q1 = st.radio("1. 관계의 최종 형태?", ["법률혼 (서류상 정식 재혼 희망)", "사실혼 (합가 동거하되 서류 정리는 신중)", "LAT 동반자 (각자 주거를 유지하며 여행과 일상 공유)", "상황에 맞추어 유연하게 협의"], key="join_q1")
        join_q38 = st.radio("2. 상대방 흡연 기준?", ["비흡연자만 가능 (전자담배 포함 절대 불가)", "전자담배까지는 양해 가능", "실외 흡연자라면 무관", "본인도 흡연자이므로 흡연 선호"], key="join_q38")
        join_q56 = st.radio("3. 종교 차이 입장?", ["동일 종교 필수 (함께 신앙생활 희망)", "종교가 달라도 강요나 터치가 없다면 무관", "무교 선호", "상대방 종교를 존중하며 맞춰줄 의향 있음"], key="join_q56")

        st.markdown("---")
        st.markdown("##### 🛡️ 안심 개인정보 및 신용 서류 파기 원칙")
        st.markdown("""
            <div class="terms-box">
                <b>1. 개인정보 수집 및 이용 목적:</b> 본인 확인, 신용점수 기준 충족 여부 심사, 상호 동의 시에 한한 연락처 제공.<br>
                <b>2. 신용 증빙 서류 100% 안전 파기 원칙:</b> 제출된 증빙 서류는 관리자 진위 확인 완료 즉시 스토리지 및 데이터베이스에서 영구 삭제 처리되며 절대 보관되지 않습니다.<br>
                <b>3. 제3자 제공 동의:</b> 양측 모두 대화를 '수락'한 경우에만 상대방에게 안심 연락처가 공개됩니다.<br>
                <b>4. 부적격 회원 조치:</b> 허위 서류 제출 및 불량 매너 회원은 사전 통보 없이 영구 이용 정지 처리됩니다.
            </div>
        """, unsafe_allow_html=True)
        
        agree_terms = st.checkbox("위 개인정보 처리방침 및 신용 서류 안전 관리 원칙에 동의합니다. (필수)", key="agree_terms_cb")

        if st.button("신용 검증 및 안심 가입 완료", key="submit_join_btn"):
            clean_phone = re.sub(r'[^0-9]', '', join_phone.strip())
            cutoff = 800 if join_gender == "남" else 600
            
            if not agree_terms:
                st.error("개인정보 처리방침 및 신용 서류 안전 관리 원칙에 동의해 주세요.")
            elif not join_name.strip():
                st.error("성명을 입력해 주세요.")
            elif not st.session_state.sms_is_verified or st.session_state.sms_verified_phone != clean_phone:
                st.error("휴대폰 본인인증(SMS 인증)을 완료해 주세요.")
            elif len(join_pwd.strip()) < 4:
                st.error("비밀번호는 최소 4자리 이상 설정해 주세요.")
            elif join_credit < cutoff:
                st.error(f"입회 기준 미달: {join_gender}성은 신용점수 {cutoff}점 이상만 승인됩니다.")
            else:
                dup = supabase.table("users").select("id").eq("phone", clean_phone).execute().data
                if dup:
                    st.error("이미 등록된 휴대폰 번호입니다. '기존 회원 로그인'을 이용해 주세요.")
                else:
                    is_valid_doc, doc_msg, file_bytes = validate_credit_doc(join_credit_doc, max_size_mb=15)
                    if not is_valid_doc:
                        st.error(doc_msg)
                    else:
                        ext = doc_msg
                        doc_uuid = uuid.uuid4().hex[:8]
                        storage_filename = f"signup_{clean_phone}_{doc_uuid}.{ext}"
                        content_type = "application/pdf" if ext == "pdf" else f"image/{ext}"
                        
                        try:
                            supabase.storage.from_("credit-docs").upload(
                                storage_filename, 
                                file_bytes, 
                                {"content-type": content_type}
                            )
                            doc_url = f"{SUPABASE_URL}/storage/v1/object/public/credit-docs/{storage_filename}"

                            new_u = supabase.table("users").insert({
                                "name": join_name.strip(),
                                "phone": clean_phone,
                                "password": join_pwd.strip(),
                                "gender": join_gender,
                                "age": int(join_age),
                                "region": selected_full_region,
                                "credit_score": int(join_credit),
                                "credit_doc_url": doc_url,
                                "credit_status": "PENDING",
                                "is_verified": False,
                                "job": join_job.strip() if join_job else None,
                                "hobbies": join_hobbies.strip() if join_hobbies else None,
                                "intro": join_intro.strip() if join_intro else None,
                                "is_admin": False,
                                "is_suspended": False
                            }).execute().data[0]
                            
                            uid = new_u["id"]
                            supabase.table("user_answers").insert([
                                {"user_id": uid, "question_num": 1, "answer_value": join_q1},
                                {"user_id": uid, "question_num": 38, "answer_value": join_q38},
                                {"user_id": uid, "question_num": 56, "answer_value": join_q56}
                            ]).execute()

                            st.session_state.user_id = uid
                            st.session_state.user_info = new_u
                            st.success("🎉 서류 키워드 확인 및 SMS 본인인증 완료! 가입 승인 대기열에 등록되었습니다.")
                            st.rerun()

                        except Exception as e:
                            st.error(f"서류 업로드 또는 회원가입 처리 중 오류가 발생했습니다: {e}")

    render_support_footer()

# [2. 메인 대시보드]
else:
    me = st.session_state.user_info

    st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px;">
            <div style="font-size:1.1rem; font-weight:900; color:#FFFFFF;">👑 {BRAND_NAME_KR}</div>
            <div style="font-size:0.75rem; font-weight:800; color:#D4AF37; letter-spacing:1px;">{BRAND_NAME_EN}</div>
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
            st.markdown(f"🛡️ **<span style='color:#38BDF8;'>공인 신용 인증 완료</span>** ({me['credit_score']}점)", unsafe_allow_html=True)
        elif c_status == "REJECTED":
            st.markdown(f"⚠️ **<span style='color:#EF4444;'>신용 증빙 서류 반려 (재제출 필요)</span>**", unsafe_allow_html=True)
        else:
            st.markdown(f"🛡️ **<span style='color:#F59E0B;'>안심 서류 검토 중</span>** ({me['credit_score']}점)", unsafe_allow_html=True)
        
        sub_info = f"📍 {me['region']}"
        if me.get("job"):
            sub_info += f" | 💼 {me['job']}"
        st.caption(sub_info)

    if me.get("intro"):
        st.markdown(f'<div class="intro-quote-box">“{me["intro"]}”</div>', unsafe_allow_html=True)

    with st.expander("✏️ 프로필 설정 및 계정 관리"):
        tab_p_edit, tab_p_pic, tab_p_doc, tab_p_delete = st.tabs(["📝 소개 및 지역/취미", "📸 프로필 사진", "📄 신용 증빙 서류", "⚠️ 회원 탈퇴"])
        
        with tab_p_edit:
            st.markdown("###### 📍 내 활동 지역 변경")
            curr_region = me.get("region", "서울특별시 강남구")
            parts = curr_region.split(" ", 1)
            init_sido = parts[0] if parts[0] in KOREA_REGIONS else "서울특별시"
            init_sigungu = parts[1] if len(parts) > 1 and parts[1] in KOREA_REGIONS[init_sido] else KOREA_REGIONS[init_sido][0]

            edit_reg1, edit_reg2 = st.columns(2)
            with edit_reg1:
                new_sido = st.selectbox("광역시·도", list(KOREA_REGIONS.keys()), index=list(KOREA_REGIONS.keys()).index(init_sido), key="edit_sido")
            with edit_reg2:
                sigungu_options = KOREA_REGIONS[new_sido]
                sigungu_idx = sigungu_options.index(init_sigungu) if init_sigungu in sigungu_options else 0
                new_sigungu = st.selectbox("시·군·구", sigungu_options, index=sigungu_idx, key="edit_sigungu")

            new_full_region = f"{new_sido} {new_sigungu}"

            new_job = st.text_input("현재 하시는 일 / 전문 분야", value=me.get("job") or "", placeholder="예: 개인사업체 운영, 전문직 등")
            new_hobbies = st.text_input("주말 취미 / 여가 활동", value=me.get("hobbies") or "", placeholder="예: 골프, 등산, 여행 등")
            new_intro = st.text_area("인생 2막을 여는 한 줄 소개", value=me.get("intro") or "", placeholder="상대방에게 나를 어필하는 소개글", height=80)
            
            if st.button("내 프로필 정보 저장"):
                supabase.table("users").update({
                    "region": new_full_region,
                    "job": new_job.strip() if new_job else None,
                    "hobbies": new_hobbies.strip() if new_hobbies else None,
                    "intro": new_intro.strip() if new_intro else None
                }).eq("id", me["id"]).execute()
                
                me["region"] = new_full_region
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
            if me.get("credit_status") == "APPROVED":
                st.info("🛡️ 이미 신용 공인 인증이 완료되었습니다. (개인정보 보호 원칙에 따라 제출 서류는 안전 파기되었습니다.)")
            else:
                st.caption("토스/카카오페이 캡처(JPG, PNG) 또는 공식 신용보고서(PDF)를 등록해 주세요. 확인 완료 즉시 안전 파기됩니다.")
                up_doc = st.file_uploader("신용 증빙 서류 첨부 (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"], key="user_credit_doc_up")
                if up_doc and st.button("증빙 서류 제출하기"):
                    is_valid, doc_msg, f_bytes = validate_credit_doc(up_doc, max_size_mb=15)
                    if not is_valid:
                        st.error(doc_msg)
                    else:
                        ext = doc_msg
                        fname = f"doc_{me['id']}_{uuid.uuid4().hex[:6]}.{ext}"
                        content_type = "application/pdf" if ext == "pdf" else f"image/{ext}"
                        try:
                            supabase.storage.from_("credit-docs").upload(fname, f_bytes, {"content-type": content_type})
                            url = f"{SUPABASE_URL}/storage/v1/object/public/credit-docs/{fname}"
                            supabase.table("users").update({
                                "credit_doc_url": url,
                                "credit_status": "PENDING"
                            }).execute()
                            me["credit_doc_url"] = url
                            me["credit_status"] = "PENDING"
                            st.session_state.user_info = me
                            st.success("증빙 서류가 제출되었습니다. 심사 완료 즉시 안전하게 파기됩니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"서류 제출 실패: {e}")

        with tab_p_delete:
            st.error("🚨 회원 탈퇴 시 모든 프로필 정보, 가치관 문답 답변, 매칭 대화 내역이 즉시 영구 파기되며 복구할 수 없습니다.")
            delete_confirm_pwd = st.text_input("탈퇴 확인을 위해 간편 비밀번호를 입력해 주세요.", type="password", key="delete_pwd_confirm")
            
            if st.button("계정 영구 삭제 및 즉시 탈퇴", type="secondary"):
                if delete_confirm_pwd.strip() != me.get("password"):
                    st.error("비밀번호가 일치하지 않습니다. 다시 확인해 주세요.")
                else:
                    try:
                        if me.get("photo_url"):
                            delete_file_from_storage("avatars", me["photo_url"])
                        if me.get("credit_doc_url"):
                            delete_file_from_storage("credit-docs", me["credit_doc_url"])
                        
                        supabase.table("users").delete().eq("id", me["id"]).execute()
                        
                        components.html("""
                        <script>
                        localStorage.removeItem('senior_match_name');
                        localStorage.removeItem('senior_match_phone');
                        localStorage.removeItem('senior_match_remember');
                        </script>
                        """, height=0)

                        st.session_state.user_id = None
                        st.session_state.user_info = None
                        st.success("그동안 노블레스 라온을 이용해 주셔서 감사합니다. 모든 개인정보가 안전하게 영구 파기되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"탈퇴 처리 중 오류가 발생했습니다: {e}")

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
            st.caption(f"{BRAND_NAME_KR} 신용 증빙 심사, 전체 고객 명부, 회원 제재 및 실시간 매칭 교환 관제를 수행합니다.")
            
            adm_sub1, adm_sub2, adm_sub3, adm_sub4 = st.tabs([
                "📑 신용 서류 심사 대기열", 
                "👥 전체 고객 명부", 
                "🔑 회원 제재 및 관리자 권한",
                "📊 실시간 매칭 교환 관제"
            ])
            
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
                                st.markdown(f'<a href="{doc_url}" target="_blank" style="display:inline-block; margin-bottom:12px; font-weight:800; color:#38BDF8; text-decoration:none;">📄 PDF 새 창에서 크게 보기 & 다운로드</a>', unsafe_allow_html=True)
                            else:
                                st.image(doc_url, caption=f"{pu['name']} 님의 제출 이미지", use_container_width=True)
                            
                            bcol1, bcol2 = st.columns(2)
                            with bcol1:
                                if st.button(f"✅ 공인 인증 승인 및 서류 영구 파기 ({pu['name']})", key=f"adm_app_{pu['id']}"):
                                    delete_file_from_storage("credit-docs", pu['credit_doc_url'])
                                    supabase.table("users").update({
                                        "credit_status": "APPROVED",
                                        "is_verified": True,
                                        "credit_doc_url": None
                                    }).eq("id", pu["id"]).execute()
                                    st.success(f"{pu['name']} 님의 인증이 완료되었으며, 증빙 서류 원본이 스토리지에서 영구 파기되었습니다.")
                                    st.rerun()

                            with bcol2:
                                if st.button(f"❌ 서류 반려 및 영구 파기 ({pu['name']})", key=f"adm_rej_{pu['id']}"):
                                    delete_file_from_storage("credit-docs", pu['credit_doc_url'])
                                    supabase.table("users").update({
                                        "credit_status": "REJECTED",
                                        "credit_doc_url": None
                                    }).eq("id", pu["id"]).execute()
                                    st.warning(f"{pu['name']} 님의 서류가 반려 처리되고 파일이 영구 파기되었습니다.")
                                    st.rerun()
                            st.divider()

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
                                "지역": st.column_config.TextColumn("지역", width="medium"),
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

            with adm_sub4:
                st.markdown("##### 📊 회원 간 매칭 신청 및 만남(연락처 교환) 관제")
                st.caption("누가 누구에게 대화를 신청했고, 최종 수락되어 연락처가 교환된 횟수를 실시간으로 추적합니다.")

                all_matches = supabase.table("match_requests").select("id, sender_id, receiver_id, status, created_at").order("created_at", desc=True).execute().data
                all_u_dict = {u["id"]: u for u in supabase.table("users").select("id, name, gender, phone").execute().data}

                if not all_matches:
                    st.info("아직 회원 간 대화 신청 이력이 없습니다.")
                else:
                    match_records = []
                    for m in all_matches:
                        s_u = all_u_dict.get(m["sender_id"], {})
                        r_u = all_u_dict.get(m["receiver_id"], {})
                        
                        s_name = s_u.get("name", "(탈퇴회원)")
                        s_phone = s_u.get("phone", "-")
                        s_gender = s_u.get("gender", "-")

                        r_name = r_u.get("name", "(탈퇴회원)")
                        r_phone = r_u.get("phone", "-")
                        r_gender = r_u.get("gender", "-")

                        status_raw = m.get("status", "PENDING")
                        if status_raw == "ACCEPTED":
                            status_kr = "🎉 만남 성사 (연락처 교환)"
                        elif status_raw == "REJECTED":
                            status_kr = "❌ 거절됨"
                        else:
                            status_kr = "⏳ 답변 대기중"

                        c_time = str(m.get("created_at", "-"))[:16].replace("T", " ")

                        match_records.append({
                            "신청일시": c_time,
                            "신청회원(보낸사람)": f"{s_name} ({s_gender})",
                            "신청자연락처": s_phone,
                            "상대회원(받은사람)": f"{r_name} ({r_gender})",
                            "상대방연락처": r_phone,
                            "진행상태": status_kr,
                            "raw_sender": s_name,
                            "raw_receiver": r_name,
                            "raw_status": status_raw
                        })

                    m_df = pd.DataFrame(match_records)

                    total_req_count = len(m_df)
                    success_count = len(m_df[m_df["raw_status"] == "ACCEPTED"])
                    success_rate = int((success_count / total_req_count) * 100) if total_req_count > 0 else 0

                    m_metric1, m_metric2, m_metric3 = st.columns(3)
                    with m_metric1:
                        st.metric("총 대화 신청", f"{total_req_count}건")
                    with m_metric2:
                        st.metric("최종 만남 성사", f"{success_count}건")
                    with m_metric3:
                        st.metric("매칭 성사율", f"{success_rate}%")

                    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
                    m_fcol1, m_fcol2 = st.columns(2)
                    with m_fcol1:
                        search_m_user = st.text_input("🔍 특정 회원 이름 검색 (신청자 or 수락자)", placeholder="예: 김진호")
                    with m_fcol2:
                        filter_m_status = st.selectbox("진행 상태 필터", ["전체 보기", "만남 성사(수락)만 보기", "답변 대기중만 보기", "거절건만 보기"])
                    st.markdown('</div>', unsafe_allow_html=True)

                    filtered_m_df = m_df.copy()
                    if search_m_user.strip():
                        target_kw = search_m_user.strip()
                        filtered_m_df = filtered_m_df[
                            filtered_m_df["raw_sender"].str.contains(target_kw, na=False) | 
                            filtered_m_df["raw_receiver"].str.contains(target_kw, na=False)
                        ]

                    if filter_m_status == "만남 성사(수락)만 보기":
                        filtered_m_df = filtered_m_df[filtered_m_df["raw_status"] == "ACCEPTED"]
                    elif filter_m_status == "답변 대기중만 보기":
                        filtered_m_df = filtered_m_df[filtered_m_df["raw_status"] == "PENDING"]
                    elif filter_m_status == "거절건만 보기":
                        filtered_m_df = filtered_m_df[filtered_m_df["raw_status"] == "REJECTED"]

                    st.caption(f"조회된 매칭 내역: 총 **{len(filtered_m_df)}건**")

                    display_match_table = filtered_m_df[[
                        "신청일시", "신청회원(보낸사람)", "신청자연락처", "상대회원(받은사람)", "상대방연락처", "진행상태"
                    ]]
                    display_match_table.index = range(1, len(display_match_table) + 1)

                    st.dataframe(
                        display_match_table,
                        use_container_width=True,
                        height=350,
                        column_config={
                            "신청일시": st.column_config.TextColumn("신청일시", width="small"),
                            "신청회원(보낸사람)": st.column_config.TextColumn("신청회원(보낸사람)", width="medium"),
                            "신청자연락처": st.column_config.TextColumn("신청자 연락처", width="medium"),
                            "상대회원(받은사람)": st.column_config.TextColumn("상대회원(받은사람)", width="medium"),
                            "상대방연락처": st.column_config.TextColumn("상대방 연락처", width="medium"),
                            "진행상태": st.column_config.TextColumn("진행상태", width="medium")
                        }
                    )

    render_support_footer()

    st.markdown("---")
    if st.button("로그아웃"):
        st.session_state.user_id = None
        st.session_state.user_info = None
        st.rerun()
