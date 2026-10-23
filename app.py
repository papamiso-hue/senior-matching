import streamlit as st
import streamlit.components.v1 as components
import re
import uuid
import math
import io
import json
import random
import secrets
import base64
import logging
import threading
import time
import hashlib
import hmac
import html
import requests
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
import pandas as pd
from supabase import create_client, Client
from pypdf import PdfReader
from kakao_auth import get_kakao_login_url, get_kakao_user_info

# 1. 스트림릿 기본 페이지 설정
st.set_page_config(
    page_title="노블레스 라온 - 5060 동반자·친구 만남",
    page_icon="👑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. PWA 모바일 전용 앱 아이콘 & 브랜드명 주입
manifest_5060 = {
    "name": "노블레스 라온",
    "short_name": "노블레스라온",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0A0A0C",
    "theme_color": "#1F190B",
    "icons": [
        {
            "src": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=192&auto=format&fit=crop",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=512&auto=format&fit=crop",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
manifest_5060_json = json.dumps(manifest_5060)

st.markdown(f"""
    <head>
        <title>노블레스 라온</title>
        <meta name="apple-mobile-web-app-title" content="노블레스 라온">
        <meta name="application-name" content="노블레스 라온">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="theme-color" content="#1F190B">
        <link rel="apple-touch-icon" href="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=192&auto=format&fit=crop">
        <link rel="icon" type="image/png" href="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=192&auto=format&fit=crop">
    </head>
    <script>
        const manifestBlob = new Blob([`{manifest_5060_json}`], {{type: 'application/json'}});
        const manifestURL = URL.createObjectURL(manifestBlob);
        let manifestLink = document.querySelector("link[rel='manifest']");
        if (!manifestLink) {{
            manifestLink = document.createElement('link');
            manifestLink.rel = 'manifest';
            document.head.appendChild(manifestLink);
        }}
        manifestLink.href = manifestURL;
        document.title = "노블레스 라온";
    </script>
""", unsafe_allow_html=True)

# 3. 서비스 기본 상수 및 보안 Secrets 연동
BRAND_NAME_KR = "노블레스 라온"
BRAND_NAME_EN = "NOBLESSE RAON 5060"
import os as _os
_BASE_URL = _os.environ.get("SITE_URL", "https://senior-matching-xtflgt6cnpp6q9o53z79pb.streamlit.app").rstrip("/")  # Render 이사 후에는 환경변수 SITE_URL=https://noblesseraon.com
SITE_URL = _BASE_URL + "/"
OG_IMAGE_URL = "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=1200&auto=format&fit=crop"
KAKAO_CHAT_URL = "https://open.kakao.com/o/sRas35Li"

# 문자(알리고)는 쓰지 않습니다(비용). 값이 있어도 없어도 앱이 멈추지 않게 .get 으로 읽습니다.
ALIGO_API_KEY = st.secrets.get("ALIGO_API_KEY", "")
ALIGO_USER_ID = st.secrets.get("ALIGO_USER_ID", "")
ALIGO_SENDER = st.secrets.get("ALIGO_SENDER", "")
# 이메일 인증번호 발송용 (Gmail 앱 비밀번호). 없으면 이메일 가입은 '준비 중'으로 안내하고 카카오 가입은 그대로 됩니다.
SMTP_USER = st.secrets.get("SMTP_USER", "")
SMTP_APP_PASSWORD = st.secrets.get("SMTP_APP_PASSWORD", "")
EMAIL_QNUM = 95  # 가입 이메일 보관 (user_answers 한 줄, 탈퇴 시 함께 삭제)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

def flat_html(s: str) -> str:
    """HTML 안의 빈 줄·들여쓰기를 없애 마크다운이 코드 블록으로 오해하지 않게 합니다."""
    return "\n".join(l.strip() for l in s.splitlines() if l.strip())


def esc(value) -> str:
    """사용자가 입력한 글을 화면(HTML)에 안전하게 넣기 위한 처리 (악성 코드 삽입 방지)"""
    return html.escape(str(value)) if value is not None else ""

# =====================================================================
# [보안 점검에서 추가한 도우미들]  (앞으로 바꿀 때 이 구간부터 읽으세요)
# =====================================================================
logger = logging.getLogger("raon")

def log_error(where, err) -> str:
    """오류의 '종류'만 서버 로그에 남기고, 화면에는 짧은 문의번호만 보여 줍니다.
    (오류 원문에는 DB 구조·키 일부·개인정보가 섞일 수 있어 화면/로그에 그대로 쓰지 않습니다)"""
    ref = uuid.uuid4().hex[:8]
    try:
        logger.error("[%s] ref=%s type=%s code=%s", where, ref, type(err).__name__, getattr(err, "code", None))
    except Exception:
        pass
    return ref

def friendly_error(where, err, what="처리 중") -> str:
    ref = log_error(where, err)
    return f"{what} 문제가 생겼습니다. 잠시 후 다시 시도해 주세요. 계속되면 고객센터에 문의번호 [{ref}]를 알려 주세요."

_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|<>~$&:])")
def md_esc(value) -> str:
    """st.markdown 에 사용자 글을 넣을 때 링크·이미지(추적 그림)·서식이 먹지 않게 특수문자를 막습니다."""
    return _MD_SPECIAL.sub(r"\\\1", str(value)) if value is not None else ""

def only_digits(value) -> str:
    return re.sub(r"[^0-9]", "", str(value or ""))

PHONE_RE = re.compile(r"01[016789]\d{7,8}")
def valid_phone(p: str) -> bool:
    return bool(PHONE_RE.fullmatch(p or ""))

PWD_MIN, PWD_MAX = 4, 20
def valid_pwd(p: str) -> bool:
    return PWD_MIN <= len((p or "").strip()) <= PWD_MAX

def _h(value) -> str:
    """전화번호 등을 메모리 속 시도 횟수 장부에 그대로 두지 않기 위한 해시"""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:24]

# ---- 시도 횟수 제한 (서버 메모리 기준: 브라우저를 새로 열어도 우회되지 않음. 앱이 재시작되면 초기화됨) ----
@st.cache_resource
def _rl_store():
    return {"lock": threading.Lock(), "hits": {}}

def rl_count(key: str, window: int) -> int:
    s = _rl_store(); now = time.time()
    with s["lock"]:
        arr = [t for t in s["hits"].get(key, []) if now - t < window]
        s["hits"][key] = arr
        return len(arr)

def rl_hit(key: str, window: int = 86400):
    s = _rl_store(); now = time.time()
    with s["lock"]:
        arr = [t for t in s["hits"].get(key, []) if now - t < window]
        arr.append(now)
        s["hits"][key] = arr
        if len(s["hits"]) > 20000:  # 메모리 보호: 비어 있는 칸 정리
            for k in [k for k, v in s["hits"].items() if not v]:
                s["hits"].pop(k, None)

def rl_clear(key: str):
    s = _rl_store()
    with s["lock"]:
        s["hits"].pop(key, None)

LOGIN_FAIL_LIMIT = 8        # 같은 번호로 15분 안에 비밀번호를 틀릴 수 있는 횟수
SMS_CODE_TTL = 300          # 인증번호 유효시간(초)
SMS_VERIFY_MAX_TRIES = 5    # 인증번호 1개당 입력 가능 횟수
SMS_SEND_PER_PHONE = 3      # 같은 번호로 1시간에 보낼 수 있는 인증문자 수
SMS_GLOBAL_PER_DAY = 300    # 하루 전체 인증문자 상한 (문자 비용 폭탄 방지. 가입자가 늘면 대표님 확인 후 올리세요)

def sms_quota_ok(phone: str):
    if rl_count("sms_global", 86400) >= SMS_GLOBAL_PER_DAY:
        return False, "현재 인증문자 요청이 많아 잠시 후 다시 시도해 주세요."
    if rl_count("sms_" + _h(phone), 3600) >= SMS_SEND_PER_PHONE:
        return False, "같은 번호로는 1시간에 3회까지만 인증번호를 받을 수 있습니다. 잠시 후 다시 시도해 주세요."
    return True, ""

def sms_quota_hit(phone: str):
    rl_hit("sms_global", 86400)
    rl_hit("sms_" + _h(phone), 3600)

def new_sms_code() -> str:
    return str(secrets.randbelow(900000) + 100000)  # random 대신 보안용 난수 사용

def check_code(kind: str, phone: str, entered: str, real, issued_at):
    """문자 인증번호 확인: 유효시간 5분, 번호 1개당 5회까지만 입력 가능."""
    generic = "인증번호가 일치하지 않거나 유효시간이 지났습니다. 새 인증번호를 받아 주세요."
    if not real or not issued_at or not phone:
        return False, generic
    if time.time() - issued_at > SMS_CODE_TTL:
        return False, generic
    key = f"verify_{kind}_{_h(phone)}"
    if rl_count(key, SMS_CODE_TTL) >= SMS_VERIFY_MAX_TRIES:
        return False, "인증번호를 여러 번 틀리셨습니다. 새 인증번호를 받아 주세요."
    if hmac.compare_digest((entered or "").strip().encode("utf-8"), str(real).encode("utf-8")):
        rl_clear(key)
        return True, ""
    rl_hit(key, SMS_CODE_TTL)
    return False, "인증번호가 일치하지 않습니다."

# ---- 업로드 검사 (파일 이름이 아니라 '내용'으로 형식 확인) ----
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_PIXELS = 40_000_000       # 비정상적으로 큰 그림(압축 폭탄) 차단

def detect_doc_type(data: bytes):
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return None

def _image_ok(data: bytes) -> bool:
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
        im = Image.open(io.BytesIO(data))
        im.verify()
        return True
    except Exception:
        return False

def check_doc_upload(f):
    """신용 증빙 서류(JPG/PNG/PDF, 5MB 이하) 검사. 문제가 있으면 안내 문구를 돌려줍니다."""
    data = f.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        return "서류 파일은 5MB 이하만 올릴 수 있습니다."
    t = detect_doc_type(data)
    if not t:
        return "JPG, PNG, PDF 파일만 올릴 수 있습니다. (파일이 손상되었거나 형식이 다릅니다)"
    if t == "pdf":
        try:
            if len(PdfReader(io.BytesIO(data)).pages) > 30:
                return "PDF는 30쪽 이하만 올릴 수 있습니다."
        except Exception:
            return "PDF 파일을 열 수 없습니다. 다른 파일로 올려 주세요."
    elif not _image_ok(data):
        return "이미지 파일을 열 수 없습니다. 다른 파일로 올려 주세요."
    return None

def check_image_upload(f):
    """프로필 사진(JPG/PNG, 5MB 이하) 검사."""
    data = f.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        return "사진은 5MB 이하만 올릴 수 있습니다."
    if detect_doc_type(data) not in ("jpg", "png"):
        return "JPG 또는 PNG 사진만 올릴 수 있습니다."
    if not _image_ok(data):
        return "사진 파일을 열 수 없습니다. 다른 사진으로 올려 주세요."
    return None

def sanitize_image(raw: bytes) -> bytes:
    """사진을 JPEG로 다시 저장합니다. 이때 촬영 위치(GPS) 등 숨은 정보(EXIF)가 모두 사라지고, 너무 큰 사진은 줄어듭니다."""
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1600, 1600))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()

def detect_key_role() -> str:
    """앱이 쓰는 Supabase 키의 '종류'만 알려 줍니다 (키 값은 절대 보여주지 않음). 관리자 화면에서만 표시."""
    k = str(SUPABASE_KEY or "")
    if k.startswith("sb_secret_"):
        return "service_role급 (sb_secret 키)"
    if k.startswith("sb_publishable_"):
        return "anon급 (publishable 키)"
    try:
        seg = k.split(".")[1]
        seg += "=" * (-len(seg) % 4)
        return str(json.loads(base64.urlsafe_b64decode(seg)).get("role", "알 수 없음"))
    except Exception:
        return "알 수 없음"

# 티켓 가격표 (원). 가격을 바꿀 때는 여기 숫자만 고치면 화면과 환불 안내에 같이 반영됩니다.
TICKET_PRICE_1 = 10000
TICKET_PRICE_3 = 27000
TICKET_PRICE_5 = 43000

def won(n: int) -> str:
    return f"{n:,}원"

# 친구 추천 보상 설정 (바꾸려면 여기 숫자만 고치세요)
WELCOME_TICKETS = 1         # 가입 선물 티켓 수
REFERRAL_BONUS = 1          # 추천한 분 / 가입한 분 각각 받는 티켓 수
REFERRAL_PAID_QNUM = 93     # 추천 보상 지급 완료 기록 (친구가 첫 결제한 뒤 지급)
PURCHASE_QNUM = 94          # 유료 티켓 충전 기록 (사람당 1줄, JSON)
REFERRAL_MAX_REWARDS = 5    # 한 분이 받을 수 있는 추천 보상 최대 횟수
REFERRAL_QNUM = 90          # 추천 기록을 user_answers에 남길 때 쓰는 번호 (문답 1~5와 겹치지 않음)
APP_URL = _BASE_URL
SHARE_URL = "https://noblesseraon.com"   # 친구 초대 링크에 쓰는 대표 도메인 (접속하면 사이트로 이동하고 ?ref= 값은 유지됩니다)

PBKDF2_ROUNDS = 200_000

# ---- 무료 티켓 유효기간 (가입 선물·친구 추천 티켓은 지급일부터 FREE_TICKET_DAYS일) ----
FREE_TICKET_DAYS = 90
GRANT_QNUM = 91     # 무료 티켓 지급 기록 (user_answers에 사람당 1줄, JSON)
EXPIRE_QNUM = 92    # 소멸 처리 완료 기록 (사람당 1줄, JSON)

def _ledger_get(uid, qnum):
    try:
        rows = supabase.table("user_answers").select("answer_value").eq("user_id", uid).eq("question_num", qnum).execute().data
        if rows:
            return json.loads(rows[0]["answer_value"]), True
    except Exception:
        pass
    return [], False

def _ledger_put(uid, qnum, value, exists):
    payload = json.dumps(value, ensure_ascii=False)
    if exists:
        supabase.table("user_answers").update({"answer_value": payload}).eq("user_id", uid).eq("question_num", qnum).execute()
    else:
        supabase.table("user_answers").insert({"user_id": uid, "question_num": qnum, "answer_value": payload}).execute()

def record_free_grant(uid, qty):
    """무료 티켓을 준 날짜와 장수를 기록합니다. 실패해도 지급 자체는 막지 않습니다."""
    try:
        grants, exists = _ledger_get(uid, GRANT_QNUM)
        grants.append({"qty": int(qty), "at": datetime.now(timezone.utc).isoformat()})
        _ledger_put(uid, GRANT_QNUM, grants, exists)
    except Exception:
        pass

def expire_free_tickets(user) -> int:
    """유효기간이 지난 무료 티켓을 소멸시킵니다. 무료 티켓부터 먼저 쓴 것으로 계산하며(오래된 것 먼저),
    유료로 충전한 티켓은 건드리지 않습니다. 소멸한 장수를 돌려줍니다."""
    try:
        grants, _ = _ledger_get(user["id"], GRANT_QNUM)
        if not grants:
            return 0
        done, done_exists = _ledger_get(user["id"], EXPIRE_QNUM)
        reqs = supabase.table("match_requests").select("status").eq("sender_id", user["id"]).execute().data
        spent = sum(1 for r in reqs if r.get("status") in ("PENDING", "ACCEPTED"))
        now_dt = datetime.now(timezone.utc)
        balance = user.get("ticket_count", 0) or 0
        expired_total = 0
        for g in sorted(grants, key=lambda x: x["at"]):
            used = min(g["qty"], spent)
            spent -= used
            unused = g["qty"] - used
            granted_dt = datetime.fromisoformat(g["at"])
            if now_dt - granted_dt > timedelta(days=FREE_TICKET_DAYS) and g["at"] not in [d["at"] for d in done]:
                n = max(0, min(unused, balance))
                balance -= n
                expired_total += n
                done.append({"at": g["at"], "n": n})
        if len(done) != len(_ledger_get(user["id"], EXPIRE_QNUM)[0]):
            _ledger_put(user["id"], EXPIRE_QNUM, done, done_exists)  # 기록을 먼저 남겨야 두 번 깎이지 않습니다 (실패하면 아래로 못 내려가 티켓은 그대로)
            if expired_total > 0:
                # 화면에 들고 있던 옛 잔액으로 덮어쓰지 않고, DB 최신 잔액에서 소멸 장수만 뺍니다 (그 사이 충전된 티켓 보호)
                nb = adjust_tickets(user["id"], -expired_total)
                if nb is not None:
                    user["ticket_count"] = nb
        return expired_total
    except Exception:
        return 0

def _blur_token(orig_fname: str) -> str:
    """원본 파일명으로부터 흐린 사본의 '추측 불가능한' 이름 조각을 만듭니다 (서버 비밀키로 만들어 외부에서는 계산할 수 없음)."""
    key = str(SUPABASE_KEY or "").encode()
    return hmac.new(key, orig_fname.encode(), hashlib.sha256).hexdigest()[:24]

def blur_fname_for(orig_fname: str) -> str:
    """원본 파일명 -> 흐린 사본 파일명. 새 사진(긴 무작위 꼬리)은 원본 이름을 알아낼 수 없는 이름을 씁니다."""
    # 형식: avatar_5060_{회원번호}_{꼬리}.jpg  (예전 사진의 꼬리는 6자, 새 사진은 32자)
    stem = orig_fname.rsplit(".", 1)[0]
    uid_part, _, tail = stem[len("avatar_5060_"):].rpartition("_")
    if len(tail) >= 32:
        return f"blur_avatar_5060_{uid_part}_{_blur_token(orig_fname)}.jpg"
    return "blur_" + orig_fname  # 예전 사진: 기존 이름 유지(호환)

def blur_photo_url(photo_url, gender):
    """피드에는 서버에서 미리 흐리게 만든 사진만 보여줍니다. 원본 주소는 화면에 절대 내보내지 않습니다."""
    marker = "/avatars/avatar_5060_"
    if photo_url and marker in photo_url:
        base, fn = photo_url.rsplit("/avatars/", 1)
        fn = fn.split("?")[0]
        return f"{base}/avatars/{blur_fname_for(fn)}"
    return DEFAULT_AVATARS.get(gender)

def clear_photo_url(photo_url, gender):
    """상대가 대화를 수락한 뒤에만 부릅니다. 가능하면 60분짜리 임시 주소(서명 URL)로 원본을 내보냅니다."""
    if not photo_url:
        return DEFAULT_AVATARS.get(gender)
    if "/avatars/avatar_5060_" in photo_url:
        fn = photo_url.split("/avatars/")[-1].split("?")[0]
        try:
            r = supabase.storage.from_("avatars").create_signed_url(fn, 3600)
            u = (r or {}).get("signedURL") or (r or {}).get("signedUrl")
            if u:
                return u if u.startswith("http") else f"{SUPABASE_URL}/storage/v1{u}"
        except Exception:
            pass
    return photo_url

def make_blurred_copy(raw_bytes: bytes) -> bytes:
    from PIL import Image, ImageFilter
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    img.thumbnail((320, 320))
    img = img.filter(ImageFilter.GaussianBlur(radius=20))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=70)
    return out.getvalue()

def hash_password(pwd: str) -> str:
    """비밀번호를 사람마다 다른 소금(salt)을 섞어 여러 번 해시해서 저장합니다."""
    if not pwd:
        return ""
    salt = uuid.uuid4().hex
    h = hashlib.pbkdf2_hmac("sha256", pwd.strip().encode("utf-8"), salt.encode("utf-8"), PBKDF2_ROUNDS).hex()
    return f"pbkdf2${PBKDF2_ROUNDS}${salt}${h}"

def verify_password(pwd: str, stored: str) -> bool:
    """새 방식과, 예전 방식(단순 해시·평문) 모두 확인합니다."""
    if not pwd or not stored:
        return False
    pwd = pwd.strip()
    if stored.startswith("pbkdf2$"):
        try:
            _, rounds, salt, h = stored.split("$")
            calc = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), salt.encode("utf-8"), int(rounds)).hex()
            return hmac.compare_digest(calc.encode("utf-8"), h.encode("utf-8"))
        except Exception:
            return False
    legacy = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
    return hmac.compare_digest(stored.encode("utf-8"), legacy.encode("utf-8")) or hmac.compare_digest(stored.encode("utf-8"), pwd.encode("utf-8"))

def is_modern_hash(stored: str) -> bool:
    return bool(stored) and stored.startswith("pbkdf2$")

BANK_INFO = {
    "bank": "IBK기업은행",
    "account": "079-154812-04-018",
    "holder": "이퀴비젼에이아이 주식회사"
}

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

CORE_QUESTIONS_5060 = {
    1: {
        "text": "1. 어떤 만남을 원하세요?",
        "options": ["취미·여행을 함께하는 동반자", "자주 안부를 나누는 가까운 친구", "각자 생활을 지키며 가끔 만나는 편안한 사이", "대화가 잘 통하는 말벗"]
    },
    2: {
        "text": "2. 평소 가족·지인과의 시간은 어떠세요?",
        "options": ["시간이 자유로워 약속 잡기가 쉬워요", "가족과 정기적으로 만나요 (명절·주말 식사 등)", "가족 돌봄 때문에 시간이 제한적이에요", "혼자 보내는 시간이 많아요"]
    },
    3: {
        "text": "3. 함께 만났을 때 비용은 어떻게 하는 것이 편하세요?",
        "options": ["번갈아 가며 내는 게 좋아요", "각자 부담하는 게 편해요", "그때그때 형편에 맞춰 정해요", "미리 이야기해서 정해요"]
    },
    4: {
        "text": "4. 여가 시간에 가장 하고 싶은 활동은?",
        "options": ["전시·공연 등 문화생활", "근교 나들이·산책·전원 생활", "여행·캠핑·골프 등 활동적인 취미", "조용한 대화·독서·차 한잔"]
    },
    5: {
        "text": "5. 만남에서 중요하게 생각하는 생활 습관은?",
        "options": ["종교가 같으면 좋아요", "종교는 상관없고 서로 존중해요", "비흡연·절주를 선호해요", "생활 습관은 크게 따지지 않아요"]
    }
}

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* ===== 5060 눈이 편한 화면: 밝은 배경 + 큰 글씨 + 진한 글자색 ===== */
    html { font-size: 19px !important; color-scheme: light !important; }
    .stApp {
        background: #FFFBF2 !important;
        color: #1A1A1A !important;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .stApp, .stApp * { word-break: keep-all; overflow-wrap: break-word; }
    .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p,
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
    [data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span,
    [data-testid="stRadio"] label p, [data-testid="stCheckbox"] label p {
        color: #1A1A1A !important;
        line-height: 1.65 !important;
    }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #4A4A4A !important; font-size: 0.92rem !important; }
    .stApp a { color: #8A4B00 !important; text-decoration: underline; font-weight: 700; }

    .stLinkButton > a {
        background-color: #FEE500 !important;
        color: #191919 !important;
        font-weight: 900 !important;
        font-size: 1.15rem !important;
        border-radius: 14px !important;
        height: 3.8rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border: 2px solid #C9B200 !important;
        text-decoration: none !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.18) !important;
        margin-bottom: 12px !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 4rem !important;
        max-width: 560px !important;
    }

    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 16px 0;
        border-bottom: 2px solid #E3D3A8;
        margin-bottom: 16px;
    }
    .app-brand {
        font-size: 1.45rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        color: #7A4A00 !important;
        -webkit-text-fill-color: #7A4A00;
    }

    .hero-box {
        background: #FFFFFF;
        border: 2px solid #B7791F;
        border-radius: 20px;
        padding: 26px 20px;
        text-align: center;
        margin-bottom: 1.2rem;
        box-shadow: 0 6px 18px rgba(122, 74, 0, 0.15);
    }
    .hero-badge {
        display: inline-block;
        background: #FFF3CC;
        border: 1.5px solid #B7791F;
        color: #6B4000 !important;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 1px;
        padding: 5px 16px;
        border-radius: 9999px;
        margin-bottom: 10px;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 900;
        line-height: 1.3;
        letter-spacing: -0.8px;
        color: #1A1A1A !important;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        font-weight: 600;
        color: #2B2B2B !important;
        line-height: 1.65;
    }

    .promise-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 1.2rem;
    }
    .promise-card {
        background: #FFFFFF;
        border: 1.5px solid #D9C48F;
        border-radius: 14px;
        padding: 14px 6px;
        text-align: center;
    }
    .promise-icon { font-size: 1.5rem; margin-bottom: 4px; }
    .promise-title { font-size: 0.95rem; font-weight: 800; color: #1A1A1A !important; }
    .promise-desc { font-size: 0.82rem; color: #4A4A4A !important; margin-top: 2px; }

    .senior-card {
        position: relative;
        border-radius: 22px;
        overflow: hidden;
        margin-bottom: 1.6rem;
        background: #FFFFFF;
        border: 2px solid #D9C48F;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }
    .senior-img-box {
        position: relative;
        width: 100%;
        height: 390px;
        overflow: hidden;
    }
    .senior-img-blur {
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: blur(10px) brightness(0.95);
        transform: scale(1.08);
    }
    .senior-img-clear {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .senior-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 45%;
        background: linear-gradient(to top, #FFFFFF 10%, transparent 100%);
        pointer-events: none;
    }
    .senior-blind-tag {
        position: absolute;
        top: 16px;
        left: 16px;
        background: #FFFFFF;
        border: 1.5px solid #B7791F;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.88rem;
        font-weight: 800;
        color: #6B4000;
    }
    .senior-match-badge {
        position: absolute;
        top: 16px;
        right: 16px;
        background: #F2B705;
        padding: 7px 16px;
        border-radius: 20px;
        font-size: 0.98rem;
        font-weight: 900;
        color: #1A1A1A;
        border: 1.5px solid #8A5A00;
    }
    .senior-content {
        padding: 16px 20px 22px 20px;
        margin-top: -24px;
        position: relative;
    }
    .senior-name-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-bottom: 8px;
    }
    .senior-name {
        font-size: 1.7rem;
        font-weight: 900;
        color: #1A1A1A;
        letter-spacing: -0.5px;
    }
    .senior-age {
        font-size: 1.25rem;
        font-weight: 700;
        color: #333333;
    }
    .badge-pill-gold {
        background: #FFF3CC;
        color: #6B4000;
        border: 1.5px solid #B7791F;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 800;
    }
    .badge-pill-credit {
        background: #DFF5E8;
        color: #0B5B34;
        border: 1.5px solid #2E8B57;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 800;
    }
    .senior-intro {
        margin-top: 12px;
        font-size: 1.05rem;
        color: #1A1A1A;
        line-height: 1.7;
        word-break: keep-all;
    }

    .shop-card {
        background: #FFFFFF;
        border: 2px solid #D9C48F;
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .shop-card.featured {
        border-color: #B7791F;
        background: #FFF8E1;
        box-shadow: 0 4px 14px rgba(183, 121, 31, 0.25);
    }
    .shop-title { font-size: 1.2rem; font-weight: 900; color: #1A1A1A; margin-bottom: 4px; }
    .shop-desc { font-size: 0.95rem; color: #3A3A3A; }
    .shop-price { white-space: nowrap; margin-left: 10px; font-size: 1.4rem; font-weight: 900; color: #7A4A00; text-align: right; }
    .shop-badge { display: inline-block; background: #7A4A00; color: #FFFFFF; font-size: 0.8rem; font-weight: 800; padding: 2px 8px; border-radius: 4px; margin-bottom: 4px; }
    .bank-box { background: #FFFFFF; border: 2px dashed #B7791F; border-radius: 14px; padding: 18px; text-align: center; margin: 16px 0; }

    div[data-baseweb="tab-list"] {
        background-color: #F3E9D2 !important;
        padding: 5px;
        border-radius: 14px;
        border: 1.5px solid #D9C48F !important;
        margin-bottom: 1.4rem;
        gap: 4px;
    }
    div[data-baseweb="tab"] {
        flex: 1;
        height: 52px;
        border-radius: 10px !important;
        background-color: transparent !important;
        color: #1A1A1A !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        border: none !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background: #7A4A00 !important;
        color: #FFFFFF !important;
        box-shadow: 0 3px 10px rgba(122, 74, 0, 0.35);
    }
    div[data-baseweb="tab-border"] { display: none !important; }
    div[data-baseweb="tab-highlight"] { display: none !important; }
    button[data-baseweb="tab"] p, button[data-baseweb="tab"] span, div[data-baseweb="tab"] p { color: #1A1A1A !important; font-weight: 800 !important; font-size: 1rem !important; }
    button[data-baseweb="tab"][aria-selected="true"] p, div[data-baseweb="tab"][aria-selected="true"] p { color: #FFFFFF !important; }
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { color: #1A1A1A !important; font-size: 1.05rem !important; font-weight: 700 !important; }

    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #6B5B3A !important;
        border-radius: 12px !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {
        border-color: #B7791F !important;
        box-shadow: 0 0 0 2px #F2B705 !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea, div[data-baseweb="select"] div {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        font-size: 1.05rem !important;
        background-color: transparent !important;
    }
    div[data-baseweb="input"] input::placeholder, div[data-baseweb="textarea"] textarea::placeholder {
        color: #6B6B6B !important; -webkit-text-fill-color: #6B6B6B !important; opacity: 1 !important;
    }
    div[data-baseweb="popover"] ul, div[data-baseweb="popover"] li, div[data-baseweb="menu"] { background-color: #FFFFFF !important; color: #111111 !important; }
    div[data-baseweb="popover"] li * { color: #111111 !important; }

    [data-testid="stExpander"] { background: #FFFFFF !important; border: 2px solid #D9C48F !important; border-radius: 12px !important; }
    [data-testid="stExpander"] summary { background: #FFFFFF !important; }
    [data-testid="stExpander"] summary svg { color: #1A1A1A !important; fill: #1A1A1A !important; }
    [data-testid="stCode"], [data-testid="stCode"] pre, .stCodeBlock pre, pre { background: #FFFFFF !important; color: #111111 !important; border: 2px solid #D9C48F !important; font-size: 0.95rem !important; }
    [data-testid="stCode"] code, pre code, code { color: #111111 !important; background: transparent !important; }
    [data-testid="stAlert"] p, [data-testid="stAlert"] div { color: #1A1A1A !important; }

    .stButton>button {
        width: 100%;
        border-radius: 12px;
        font-weight: 800;
        min-height: 3.6rem;
        font-size: 1.15rem;
        letter-spacing: -0.3px;
        border: 2px solid #8A5A00 !important;
        background: #F2B705 !important;
        color: #111111 !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
        transition: transform 0.1s ease;
    }
    .stButton>button p, .stButton>button span { color: #111111 !important; font-size: 1.15rem !important; font-weight: 800 !important; }
    .stButton>button:hover { background: #FFC81F !important; }
    .stButton>button:active { transform: scale(0.98); }
    .stButton>button:focus-visible, a:focus-visible, input:focus-visible { outline: 3px solid #1A5FB4 !important; outline-offset: 2px; }

    #MainMenu, footer, header { visibility: hidden !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

def adjust_tickets(uid, delta):
    """티켓 수를 안전하게 바꿉니다. 같은 순간에 다른 화면에서도 바꿨다면 다시 읽고 재시도합니다
    (동시에 두 번 눌러 티켓이 공짜로 늘거나 이중 차감되는 문제 방지). 성공하면 새 잔액, 실패하면 None."""
    for _ in range(6):
        rows = supabase.table("users").select("ticket_count").eq("id", uid).execute().data
        if not rows:
            return None
        raw = rows[0].get("ticket_count")
        new = (raw or 0) + delta
        if new < 0:
            return None
        q = supabase.table("users").update({"ticket_count": new}).eq("id", uid)
        q = q.is_("ticket_count", "null") if raw is None else q.eq("ticket_count", raw)
        if q.execute().data:
            return new
    return None

def _avatar_names_from_url(photo_url):
    names = set()
    if photo_url and "/avatars/" in photo_url:
        fn = photo_url.split("/avatars/")[-1].split("?")[0]
        if fn.startswith("avatar_5060_"):
            names.add(fn)
            names.add("blur_" + fn)           # 예전 이름
            names.add(blur_fname_for(fn))     # 새 이름
    return names

def remove_avatar_files(uid=None, photo_url=None) -> int:
    """보관함의 사진 원본과 흐린 사본(blur_)을 지웁니다. uid를 주면 예전에 올린 사진까지 모두 찾아 지웁니다."""
    names = _avatar_names_from_url(photo_url)
    if uid:
        # 끝에 "_"를 붙여야 합니다: 번호가 숫자형일 때 1번 회원 탈퇴가 10~19번 회원 사진까지 지우는 사고를 막습니다
        for prefix in (f"avatar_5060_{uid}_", f"blur_avatar_5060_{uid}_"):
            try:
                for it in supabase.storage.from_("avatars").list("", {"search": prefix, "limit": 200}) or []:
                    n = it.get("name", "")
                    if n.startswith(prefix):
                        names.add(n)
            except Exception:
                pass
    if names:
        try:
            supabase.storage.from_("avatars").remove(list(names))
        except Exception:
            pass
    return len(names)

def withdraw_member(uid):
    """회원 탈퇴 처리 (개인정보 보호법: 동의 철회 시 지체 없이 파기).
    - 사진(원본+흐린 사본), 신용서류, 답변, 대화 신청 기록, 차단 목록을 삭제합니다.
    - [처리 방식 선택 이유] 유료 충전 장부(PURCHASE_QNUM=94번)는 전자상거래법 시행령상 대금결제·공급 기록 5년 보관 대상일 수 있어
      (전문가 확인 필요) 유료 충전 이력이 '있는' 회원은 users 행을 지우지 않고 이름·전화·비밀번호·카카오번호 등을 모두 지운 '익명 행'으로
      바꿔 두고 94번 장부만 남깁니다 (장부가 users 행을 가리키고 있어, 행을 지우면 장부도 함께 사라지거나 삭제가 막히기 때문입니다.
      새 표/칸을 만들지 않고 법정 보관을 지키는 가장 단순한 방법). 보관 5년이 지나면 관리자가 이 익명 행과 94번 장부를 삭제합니다.
      유료 충전 이력이 '없는' 회원은 users 행까지 완전히 삭제합니다.
    - 관리자 계정은 탈퇴할 수 없습니다. 돈(환불)은 이 함수가 다루지 않습니다 (환불은 대표님 확인 사항).
    돌려주는 값: (성공 여부, 안내 문구)"""
    rows = supabase.table("users").select("id,is_admin,credit_doc_url,photo_url").eq("id", uid).execute().data
    if not rows:
        return False, "회원 정보를 찾을 수 없습니다."
    u = rows[0]
    if u.get("is_admin"):
        return False, "관리자 계정은 탈퇴할 수 없습니다."

    # 1) 나에게 온 '대기중' 신청: 보낸 분의 티켓을 돌려드린 뒤 기록 삭제
    for r in supabase.table("match_requests").select("id,sender_id").eq("receiver_id", uid).eq("status", "PENDING").execute().data:
        if supabase.table("match_requests").update({"status": "EXPIRED"}).eq("id", r["id"]).eq("status", "PENDING").execute().data:
            adjust_tickets(r["sender_id"], 1)
    supabase.table("match_requests").delete().eq("sender_id", uid).execute()
    supabase.table("match_requests").delete().eq("receiver_id", uid).execute()

    # 2) 파일 삭제 (사진 원본·흐린 사본·예전에 올린 사진·남아있는 신용서류)
    remove_avatar_files(uid, u.get("photo_url"))
    doc_path = u.get("credit_doc_url") or ""
    if doc_path and not doc_path.startswith("["):
        try:
            supabase.storage.from_("credit-docs").remove([doc_path.split("/")[-1]])
        except Exception:
            pass

    # 3) 문답·장부 삭제 (유료 충전 장부는 법정 보관 때문에 조건부로 남김)
    purchases, _ = _ledger_get(uid, PURCHASE_QNUM)
    if purchases:
        supabase.table("user_answers").delete().eq("user_id", uid).neq("question_num", PURCHASE_QNUM).execute()
        anon = {
            "name": "탈퇴회원", "phone": "del" + uuid.UUID(str(uid)).hex[:12] if _is_uuid(uid) else "del" + _h(uid)[:12],
            "password": "", "kakao_id": None, "photo_url": None, "region": "", "job": "", "hobbies": "", "intro": "",
            "credit_doc_url": "", "credit_score": 0, "blocked_phones": [], "ticket_count": 0,
            "is_suspended": True, "is_vip": False,
        }
        supabase.table("users").update(anon).eq("id", uid).execute()
        return True, ("탈퇴가 완료되었습니다. 이름·연락처·사진·소개글·답변은 모두 삭제되었습니다. "
                      "다만 전자상거래법에 따라 유료 결제 기록(충전 날짜·수량·금액)만 5년간 보관한 뒤 파기합니다.")
    supabase.table("user_answers").delete().eq("user_id", uid).execute()
    supabase.table("users").delete().eq("id", uid).execute()
    return True, "탈퇴가 완료되었습니다. 회원님의 모든 정보가 삭제되었습니다. 그동안 이용해 주셔서 감사합니다."

def _is_uuid(v) -> bool:
    try:
        uuid.UUID(str(v))
        return True
    except Exception:
        return False

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
        _rj = res.json() if res.status_code == 200 else {}
        if res.status_code == 200 and str(_rj.get("result_code")) == "1":
            return True, "인증번호가 발송되었습니다."
        # 실패 이유(알리고 결과코드·안내문)만 서버 로그에 남깁니다. 번호·키·인증번호는 남기지 않습니다.
        logger.error("[sms_send] aligo_http=%s result_code=%s message=%s", res.status_code, _rj.get("result_code"), str(_rj.get("message"))[:80])
        return False, "인증문자 발송에 실패했습니다. 잠시 후 다시 시도해 주세요. 계속되면 고객센터(카카오톡·대표전화)로 알려 주세요."
    except Exception as e:
        log_error("sms_send", e)
        return False, "인증문자 발송 중 문제가 생겼습니다. 잠시 후 다시 시도해 주세요."

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
def valid_email(e: str) -> bool:
    return bool(EMAIL_RE.fullmatch(e or "")) and len(e) <= 100

def send_email_code(to_email, code):
    """인증번호를 이메일로 보냅니다(Gmail SMTP, 무료). 인증번호·비밀번호는 로그에 남기지 않습니다."""
    if not SMTP_USER or not SMTP_APP_PASSWORD:
        return False, "이메일 인증을 준비 중입니다. 카카오 계정으로 시작해 주세요."
    try:
        msg = EmailMessage()
        msg["Subject"] = f"[{BRAND_NAME_KR}] 이메일 인증번호 안내"
        msg["From"] = f"{BRAND_NAME_KR} <{SMTP_USER}>"
        msg["To"] = to_email
        msg.set_content(f"인증번호는 [{code}] 입니다. 5분 안에 입력해 주세요.\n본인이 요청하지 않았다면 이 메일은 무시하셔도 됩니다.")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10, context=ssl.create_default_context()) as sv:
            sv.login(SMTP_USER, SMTP_APP_PASSWORD)
            sv.send_message(msg)
        return True, "인증번호를 이메일로 보냈습니다."
    except Exception as e:
        log_error("email_send", e)
        return False, "이메일 발송에 실패했습니다. 주소를 확인하시고 잠시 후 다시 시도해 주세요."

def send_aligo_notice_sms(receiver_phone, text_message):
    if not (ALIGO_API_KEY and ALIGO_USER_ID and ALIGO_SENDER):
        return  # 문자 비용 없음: 설정이 없으면 보내지 않습니다
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
    "남": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=600&auto=format&fit=crop",
    "여": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=600&auto=format&fit=crop"
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
if "sms_send_count_5060" not in st.session_state:
    st.session_state.sms_send_count_5060 = 0
if "sms_last_sent_at_5060" not in st.session_state:
    st.session_state.sms_last_sent_at_5060 = None

if "reset_sms_code_5060" not in st.session_state:
    st.session_state.reset_sms_code_5060 = None
if "reset_verified_phone_5060" not in st.session_state:
    st.session_state.reset_verified_phone_5060 = None
if "reset_target_uid_5060" not in st.session_state:
    st.session_state.reset_target_uid_5060 = None

if "kakao_user" not in st.session_state:
    st.session_state.kakao_user = None
if "ref_id" not in st.session_state:
    st.session_state.ref_id = None

# 친구 추천 링크(?ref=...) 기억하기. 카카오 로그인을 거쳐 돌아올 때는 state 값으로 전달됩니다.
_ref_raw = st.query_params.get("ref") or st.query_params.get("state")
if _ref_raw and re.fullmatch(r"[A-Za-z0-9\-]{1,64}", str(_ref_raw)):
    st.session_state.ref_id = str(_ref_raw)

# 카카오 콜백 처리
params = st.query_params
if "code" in params and not st.session_state.user_id:
    kakao_code = params.get("code")
    k_user = get_kakao_user_info(kakao_code)
    
    # 1회용 인가 코드 사용 즉시 주소창 파라미터 삭제 (KOE320 방지)
    st.query_params.clear()
    
    if k_user:
        st.session_state.kakao_user = k_user
        kakao_id_str = str(k_user["id"])
        
        # 1) 기존 회원 여부 확인
        res = supabase.table("users").select("*").eq("kakao_id", kakao_id_str).execute()
        if res.data:
            u = res.data[0]
            if u.get("is_suspended"):
                st.session_state.kakao_user = None  # 정지된 회원이 새 가입 화면으로 넘어가지 못하게 함
                st.error("🚫 제재 조치된 계정입니다. 고객센터로 문의해 주세요.")
            else:
                now_utc = datetime.now(timezone.utc).isoformat()
                supabase.table("users").update({"last_login_at": now_utc}).eq("id", u["id"]).execute()
                u["last_login_at"] = now_utc
                st.session_state.user_id = u["id"]
                st.session_state.user_info = u
                st.rerun()
        else:
            # 2) 신규 회원인 경우: 안내 화면으로 갱신
            st.rerun()


# --- 로그인 7일 유지 (새로고침·앱 전환으로 튕기는 문제 방지) ---
# 브라우저 쿠키에 '서명된 로그인표'를 저장합니다. 비밀번호는 저장하지 않으며, 서명 없이는 위조할 수 없습니다.
# 이 부분이 어떤 이유로든 실패하면 조용히 넘어가고, 예전처럼 직접 로그인하면 됩니다.
import hmac as _hmac, hashlib as _hashlib, time as _time
import streamlit.components.v1 as _components
LOGIN_COOKIE = "nr_login"
LOGIN_DAYS = 7


def _login_sig(uid: str, exp: int) -> str:
    key = _hashlib.sha256(("nr-login|" + str(SUPABASE_KEY)).encode()).digest()
    return _hmac.new(key, f"{uid}.{exp}".encode(), _hashlib.sha256).hexdigest()


def make_login_token(uid) -> str:
    exp = int(_time.time()) + LOGIN_DAYS * 86400
    return f"{uid}.{exp}.{_login_sig(str(uid), exp)}"


def read_login_token(token: str):
    """맞는 로그인표면 회원 id를, 아니면 None을 돌려줍니다."""
    try:
        uid, exp_s, sig = str(token).rsplit(".", 2)
        exp = int(exp_s)
        if exp < int(_time.time()):
            return None
        if not _hmac.compare_digest(sig, _login_sig(uid, exp)):
            return None
        return uid
    except Exception:
        return None


def _cookie_js(script: str):
    _components.html(f"<script>{script}</script>", height=0)


def sync_login_cookie():
    try:
        ss = st.session_state
        if ss.user_id:
            ss["_logged_out"] = False
            if ss.get("_cookie_uid") != str(ss.user_id):
                tok = make_login_token(ss.user_id)
                _cookie_js(f"document.cookie='{LOGIN_COOKIE}={tok}; max-age={LOGIN_DAYS*86400}; path=/; SameSite=Lax; Secure';")
                ss["_cookie_uid"] = str(ss.user_id)
        else:
            if ss.get("_cookie_uid"):  # 로그아웃·탈퇴·제재로 로그인이 풀린 경우
                _cookie_js(f"document.cookie='{LOGIN_COOKIE}=; max-age=0; path=/; SameSite=Lax; Secure';")
                ss["_cookie_uid"] = None
                ss["_logged_out"] = True
            elif not ss.get("_logged_out") and not ss.get("_restore_tried"):
                ss["_restore_tried"] = True
                ck = getattr(st.context, "cookies", None)
                tok = ck.get(LOGIN_COOKIE) if ck else None
                uid = read_login_token(tok) if tok else None
                if uid:
                    rows = supabase.table("users").select("*").eq("id", uid).execute().data
                    if rows and not rows[0].get("is_suspended") and not rows[0].get("is_admin"):  # 관리자는 자동 로그인 제외
                        u = rows[0]
                        ss.user_id = u["id"]
                        ss.user_info = u
                        ss["_cookie_uid"] = str(u["id"])
    except Exception:
        pass


sync_login_cookie()

# --- 1. 로그인 / 신규 가입 화면 ---
if not st.session_state.user_id:
    st.markdown(f"""
        <div class="hero-box">
            <div class="hero-badge">👑 5060 NOBLESSE COMPANIONS</div>
            <div class="hero-title">🌟 {BRAND_NAME_KR}</div>
            <div class="hero-subtitle">품격 있는 인생 2막을 함께할 동반자·친구를 위한<br>
            <strong style="color:#7A4A00;">본인 확인으로 안심하는 5060 동반자·친구 만남</strong></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="promise-grid">
            <div class="promise-card">
                <div class="promise-icon">🛡️</div>
                <div class="promise-title">본인 확인 완료</div>
                <div class="promise-desc">카카오 로그인 · 이메일 인증</div>
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

    _wm = st.session_state.pop("withdrawn_msg_5060", None)
    if _wm:
        st.success(_wm)

    # 🌟 카카오 인증 완료 회원이면 환영 박스 표시 & 신규 가입 탭 우선 활성화
    if st.session_state.kakao_user:
        k_nick = st.session_state.kakao_user.get("nickname", "회원")
        st.success(f"🎉 **{md_esc(k_nick)}**님, 카카오 본인 확인이 완료되었습니다!\n\n회원 심사를 위해 아래에서 기본 정보와 서류를 제출해 주세요.")
        tab_join, tab_login = st.tabs(["📝 신규 프로필 등록 (카카오 연동)", "🔑 기존 정회원 로그인"])
    else:
        kakao_login_url = get_kakao_login_url(state=st.session_state.ref_id)
        st.link_button(
            "💬 카카오 계정으로 간편 시작",
            url=kakao_login_url,
            use_container_width=True
        )
        tab_login, tab_join = st.tabs(["🔑 정회원 로그인", "📝 신규 프로필 등록"])

    with tab_login:
        login_name = st.text_input("성명", key="l_name")
        login_phone = st.text_input("휴대폰 번호 (- 제외 숫자만)", placeholder="01012345678", key="l_phone")
        login_pwd = st.text_input("간편 비밀번호 (4~6자리)", type="password", key="l_pwd")

        if st.button("안심 본인인증 로그인", key="btn_login"):
            clean_p = re.sub(r'[^0-9]', '', login_phone.strip())
            lk = "login_" + _h(clean_p)
            if not login_name.strip() or not clean_p or not login_pwd.strip():
                st.error("성명, 휴대폰 번호, 비밀번호를 모두 입력해 주세요.")
            elif st.session_state.get("login_fail_5060", 0) >= 5 or rl_count(lk, 900) >= LOGIN_FAIL_LIMIT:
                st.error("비밀번호를 여러 번 틀리셨습니다. 15분 뒤에 다시 시도하시거나 고객센터로 문의해 주세요.")
            else:
                res = supabase.table("users").select("*").eq("name", login_name.strip()).eq("phone", clean_p).execute()
                u = res.data[0] if res.data else None
                stored_pwd = (u or {}).get("password", "")
                if u and verify_password(login_pwd, stored_pwd):
                    rl_clear(lk)
                    if u.get("is_suspended"):
                        st.error("🚫 제재 조치된 계정입니다. 고객센터로 문의해 주세요.")
                    else:
                        now_utc = datetime.now(timezone.utc).isoformat()
                        update_data = {"last_login_at": now_utc}
                        if not is_modern_hash(stored_pwd):
                            update_data["password"] = hash_password(login_pwd)  # 예전 방식 비밀번호는 로그인 때 새 방식으로 바꿔 저장

                        supabase.table("users").update(update_data).eq("id", u["id"]).execute()
                        u["last_login_at"] = now_utc
                        st.session_state.user_id = u["id"]
                        st.session_state.user_info = u
                        st.rerun()
                else:
                    # 번호가 없는 경우와 비밀번호가 틀린 경우를 같은 문구로 안내 (가입 여부를 알아내는 시도 방지)
                    st.session_state.login_fail_5060 = st.session_state.get("login_fail_5060", 0) + 1
                    rl_hit(lk, 900)
                    st.error("성명, 휴대폰 번호 또는 비밀번호가 일치하지 않습니다.")

        with st.expander("🔑 비밀번호를 잊으셨나요? (간편 재설정)"):
            st.caption("가입 때 등록한 성명과 이메일로 인증번호를 받아 새 비밀번호를 정할 수 있습니다. 이메일을 등록하지 않으신 분은 카카오톡 상담창으로 문의해 주세요.")
            f_name = st.text_input("가입 성명", key="f_name_5060")
            col_fp1, col_fp2 = st.columns([2.5, 1.2])
            with col_fp1:
                f_email = st.text_input("가입 이메일", placeholder="example@gmail.com", key="f_email_5060")
            with col_fp2:
                st.write("")
                btn_find_mail = st.button("인증번호 받기", key="btn_find_mail_5060")

            clean_fe = f_email.strip().lower()
            if btn_find_mail:
                now_ts = time.time()
                last_ts = st.session_state.get("reset_last_sent_5060")
                if not f_name.strip() or not valid_email(clean_fe):
                    st.error("성명과 이메일을 정확히 입력해 주세요.")
                elif last_ts and now_ts - last_ts < 60:
                    st.warning(f"⏳ {int(60 - (now_ts - last_ts))}초 후에 다시 요청할 수 있습니다.")
                else:
                    ok_q, msg_q = sms_quota_ok(clean_fe)
                    if not ok_q:
                        st.error(msg_q)
                    else:
                        sms_quota_hit(clean_fe)  # 가입 여부와 상관없이 횟수에 포함
                        st.session_state.reset_last_sent_5060 = now_ts
                        st.session_state.reset_sms_code_5060 = None
                        st.session_state.reset_target_uid_5060 = None
                        st.session_state.reset_form_open_5060 = True
                        try:
                            rows = supabase.table("user_answers").select("user_id").eq("question_num", EMAIL_QNUM).eq("answer_value", clean_fe).execute().data
                            uid_f = None
                            if rows:
                                u = supabase.table("users").select("id").eq("id", rows[0]["user_id"]).eq("name", f_name.strip()).execute().data
                                uid_f = u[0]["id"] if u else None
                        except Exception as e:
                            log_error("reset_lookup", e)
                            uid_f = None
                        if uid_f:
                            code = new_sms_code()
                            ok_m, _m = send_email_code(clean_fe, code)
                            if ok_m:
                                st.session_state.reset_sms_code_5060 = code
                                st.session_state.reset_verified_phone_5060 = clean_fe
                                st.session_state.reset_target_uid_5060 = uid_f
                                st.session_state.reset_code_issued_at = now_ts
                                rl_clear("verify_reset_" + _h(clean_fe))
                        st.success("입력하신 정보가 가입 정보와 일치하면 인증번호가 이메일로 발송됩니다. (스팸함도 확인해 주세요) 아래에 입력해 주세요.")

            if st.session_state.get("reset_form_open_5060"):
                in_fcode = st.text_input("이메일 인증번호 6자리", key="in_find_code_5060")
                new_reset_pwd = st.text_input("새로운 간편 비밀번호 (4~6자리)", type="password", key="new_reset_pwd_5060")

                if st.button("새 비밀번호로 변경 및 저장", key="btn_do_reset_5060"):
                    tgt_key = st.session_state.get("reset_verified_phone_5060")  # 인증번호를 받은 이메일 기준으로만 확인
                    ok_c, msg_c = check_code("reset", tgt_key, in_fcode, st.session_state.reset_sms_code_5060,
                                             st.session_state.get("reset_code_issued_at"))
                    if not ok_c:
                        st.error(msg_c)
                    elif not valid_pwd(new_reset_pwd):
                        st.error(f"비밀번호는 {PWD_MIN}자리 이상 {PWD_MAX}자리 이하로 입력해 주세요.")
                    elif not st.session_state.reset_target_uid_5060:
                        st.error("인증번호가 일치하지 않거나 유효시간이 지났습니다. 새 인증번호를 받아 주세요.")
                    else:
                        supabase.table("users").update({
                            "password": hash_password(new_reset_pwd)
                        }).eq("id", st.session_state.reset_target_uid_5060).execute()
                        st.session_state.login_fail_5060 = 0
                        st.session_state.reset_sms_code_5060 = None
                        st.session_state.reset_target_uid_5060 = None
                        st.session_state.reset_form_open_5060 = False
                        st.success("🎉 비밀번호가 안전하게 재설정되었습니다! 새 비밀번호로 로그인해 주세요.")

    with tab_join:
        st.markdown("##### 👤 기본 인적사항 (만 48~75세 대상)")
        
        default_name = ""
        if st.session_state.kakao_user:
            default_name = st.session_state.kakao_user.get("nickname", "")
            st.caption(f"💬 카카오 프로필 연동 중: **{md_esc(default_name)}**")

        j_name = st.text_input("실명", value=default_name, key="j_name")
        
        j_phone = st.text_input("휴대폰 번호 (- 제외, 연락용)", placeholder="01012345678", key="j_phone")
        clean_jp = re.sub(r'[^0-9]', '', j_phone.strip())

        is_kakao_join = bool(st.session_state.kakao_user)
        j_email_clean = ""
        if is_kakao_join:
            st.success("✅ 카카오 로그인으로 가입합니다. (별도 인증번호 없음)")
            j_email = st.text_input("이메일 (선택, 비밀번호를 잊었을 때 사용)", placeholder="example@gmail.com", key="j_email_k")
            j_email_clean = j_email.strip().lower()
        else:
            col_e1, col_e2 = st.columns([2.5, 1.2])
            with col_e1:
                j_email = st.text_input("이메일 (인증번호를 받을 주소)", placeholder="example@gmail.com", key="j_email")
            with col_e2:
                st.write("")
                btn_mail = st.button("인증번호 받기", key="btn_mail")
            j_email_clean = j_email.strip().lower()

            if btn_mail:
                now_ts = time.time()
                if not valid_email(j_email_clean):
                    st.error("올바른 이메일 주소를 입력해 주세요.")
                elif st.session_state.sms_send_count_5060 >= 3:
                    st.error("🚨 인증번호 발송 허용 횟수(3회)를 초과했습니다. 잠시 후 다시 시도해 주세요.")
                elif st.session_state.sms_last_sent_at_5060 and (now_ts - st.session_state.sms_last_sent_at_5060 < 60):
                    remaining = int(60 - (now_ts - st.session_state.sms_last_sent_at_5060))
                    st.warning(f"⏳ {remaining}초 후에 다시 요청할 수 있습니다.")
                else:
                    ok_q, msg_q = sms_quota_ok(j_email_clean)
                    if not ok_q:
                        st.error(msg_q)
                    else:
                        dup = supabase.table("user_answers").select("user_id").eq("question_num", EMAIL_QNUM).eq("answer_value", j_email_clean).execute().data
                        if dup:
                            st.error("이미 가입된 이메일입니다. 로그인하시거나 비밀번호 재설정을 이용해 주세요.")
                        else:
                            code = new_sms_code()
                            ok_s, _msg_s = send_email_code(j_email_clean, code)
                            if not ok_s:
                                st.error(_msg_s)
                            else:
                                sms_quota_hit(j_email_clean)
                                st.session_state.sms_auth_code = code
                                st.session_state.sms_verified_phone = j_email_clean  # (이름은 예전 그대로, 값은 이메일)
                                st.session_state.sms_is_verified = False
                                st.session_state.sms_last_sent_at_5060 = now_ts
                                st.session_state.sms_code_issued_at = now_ts
                                st.session_state.sms_send_count_5060 += 1
                                rl_clear("verify_join_" + _h(j_email_clean))
                                st.success(f"이메일로 보낸 6자리 인증번호를 입력해 주세요. (스팸함도 확인해 주세요 · {st.session_state.sms_send_count_5060}/3회, 유효시간 5분)")

            if st.session_state.sms_auth_code:
                c_code, c_btn = st.columns([2.5, 1.2])
                with c_code:
                    in_code = st.text_input("인증번호 6자리", key="in_sms_code")
                with c_btn:
                    st.write("")
                    if st.button("인증 확인", key="btn_confirm_sms"):
                        ok_c, msg_c = check_code("join", st.session_state.sms_verified_phone, in_code,
                                                 st.session_state.sms_auth_code, st.session_state.get("sms_code_issued_at"))
                        if ok_c:
                            st.session_state.sms_is_verified = True
                            st.success("✅ 이메일 인증이 완료되었습니다.")
                        else:
                            st.error(msg_c)

        j_pwd = st.text_input("간편 비밀번호 (4~6자리)", type="password", key="j_pwd")
        j_gender = st.radio("성별", ["남", "여"], horizontal=True, key="j_gender")
        j_age = st.number_input("나이 (만 나이)", 48, 75, 58, key="j_age")

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

        j_intro = st.text_area("동반자에게 전하고 싶은 말씀", value="", placeholder="예: 인생의 후반전을 서로 존중하며 함께 이야기 나눌 좋은 친구를 찾습니다. (비워 두면 이 문장이 들어갑니다)", max_chars=500, key="j_intro")
        intro_typos = audit_text_typos(j_intro)
        if intro_typos:
            st.caption(f"💡 소개글 맞춤법 안내: {', '.join(intro_typos)}")

        st.markdown("##### 🛡️ 인증 배지 (선택)")
        st.caption("ℹ️ 신용점수와 증빙서류 제출은 **선택**입니다. 제출하면 프로필에 '인증 배지'가 붙어 신뢰도가 올라갑니다. 서류는 확인 즉시 파기됩니다.")
        j_credit = st.number_input("공인 신용점수 (선택, 배지를 원하실 때만 입력)", 0, 1000, 0, key="j_credit")
        j_doc = st.file_uploader("신용 증빙 서류 첨부 (선택: NICE/KCB 리포트 또는 토스 캡처)", type=["jpg", "png", "pdf"], key="j_doc")

        st.markdown("##### 🎯 나와 맞는 친구를 위한 5가지 질문")
        a1 = st.radio(CORE_QUESTIONS_5060[1]["text"], CORE_QUESTIONS_5060[1]["options"], key="jq_1")
        a2 = st.radio(CORE_QUESTIONS_5060[2]["text"], CORE_QUESTIONS_5060[2]["options"], key="jq_2")
        a3 = st.radio(CORE_QUESTIONS_5060[3]["text"], CORE_QUESTIONS_5060[3]["options"], key="jq_3")
        a4 = st.radio(CORE_QUESTIONS_5060[4]["text"], CORE_QUESTIONS_5060[4]["options"], key="jq_4")
        a5 = st.radio(CORE_QUESTIONS_5060[5]["text"], CORE_QUESTIONS_5060[5]["options"], key="jq_5")

        with st.expander("📄 수집 항목과 이용 안내 (눌러서 읽어 보세요)"):
            st.markdown("""
            **수집 항목(필수)**: 성명, 휴대폰 번호, 비밀번호(암호화 저장), 성별, 나이, 지역, 직업, 취미, 소개글, 질문 5가지 답변, 이메일(이메일 가입 시 필수, 카카오 가입 시 선택), 카카오 계정 식별번호·프로필 사진(카카오로 가입 시)
            **이용 목적**: 회원 가입과 본인 확인, 대화 신청 서비스 제공, 인증번호·이용 안내 발송, 부정 이용 방지
            **보유 기간**: 탈퇴 시까지. 단, 결제·환불 기록은 전자상거래법에 따라 5년 보관합니다.
            **선택 항목**: 신용점수와 증빙서류(인증 배지용). 확인 후 서류는 파기하며, 배지를 받지 않아도 이용에 불이익이 없습니다.
            동의를 거부할 수 있으나, 필수 항목은 거부하면 가입이 어렵습니다.
            """)
        agree_terms = st.checkbox("[필수] 노블레스 라온 이용약관에 동의합니다.", key="agree_terms")
        agree_privacy = st.checkbox("[필수] 개인정보 수집·이용에 동의합니다. (위 안내 참고)", key="agree_privacy")
        agree_credit = st.checkbox("[선택] 신용점수·증빙서류 수집·이용에 동의합니다. (인증 배지를 받을 때만)", key="agree_credit")

        if st.button("신원 검증 신청 및 가입 완료", key="btn_submit_join"):
            if not agree_terms or not agree_privacy:
                st.error("필수 항목(이용약관, 개인정보 수집·이용)에 동의해 주세요.")
            elif j_doc and not agree_credit:
                st.error("서류를 올리시려면 [선택] 신용정보 수집·이용에 동의해 주세요. (배지가 필요 없으면 서류를 지워 주세요)")
            elif not j_name.strip() or len(j_name.strip()) > 30:
                st.error("성명을 입력해 주세요. (30자 이내)")
            elif not valid_phone(clean_jp):
                st.error("올바른 휴대폰 번호(010 등으로 시작하는 숫자 10~11자리)를 입력해 주세요.")
            elif not is_kakao_join and (not st.session_state.sms_is_verified or st.session_state.sms_verified_phone != j_email_clean):
                st.error("이메일 인증을 완료해 주세요. (카카오로 시작하면 인증번호 없이 가입됩니다)")
            elif is_kakao_join and j_email_clean and not valid_email(j_email_clean):
                st.error("이메일 주소 형식이 올바르지 않습니다. (비워 두셔도 됩니다)")
            elif supabase.table("users").select("id").eq("phone", clean_jp).execute().data:
                st.error("이미 등록된 휴대폰 번호입니다.")
            elif not valid_pwd(j_pwd):
                st.error(f"비밀번호는 {PWD_MIN}자리 이상 {PWD_MAX}자리 이하로 입력해 주세요.")
            elif j_doc and j_credit <= 0:
                st.error("서류를 올리셨다면 신용점수도 함께 입력해 주세요. (배지가 필요 없으면 서류를 지워 주세요)")
            elif len(j_job) > 60 or len(j_hobbies) > 100 or len(j_intro) > 500:
                st.error("직업은 60자, 취미는 100자, 소개글은 500자 이내로 적어 주세요.")
            elif j_doc and check_doc_upload(j_doc):
                st.error(check_doc_upload(j_doc))
            else:
                has_doc = bool(j_doc)
                doc_name = ""
                try:
                    if has_doc:
                        doc_bytes = j_doc.getvalue()
                        doc_ext = detect_doc_type(doc_bytes)  # 파일 이름이 아니라 내용으로 판별 (위에서 이미 검사 통과)
                        doc_name = f"verify_{uuid.uuid4().hex}.{doc_ext}"  # 파일 이름에 전화번호 등 개인정보를 넣지 않음
                        supabase.storage.from_("credit-docs").upload(
                            doc_name,
                            doc_bytes,
                            {"content-type": {"pdf": "application/pdf", "jpg": "image/jpeg", "png": "image/png"}[doc_ext]}
                        )
                    now_utc = datetime.now(timezone.utc).isoformat()

                    kakao_id_val = str(st.session_state.kakao_user["id"]) if st.session_state.kakao_user else None
                    kakao_photo_val = st.session_state.kakao_user.get("profile_image") if st.session_state.kakao_user else None

                    user_data = {
                        "name": j_name.strip(),
                        "phone": clean_jp,
                        "password": hash_password(j_pwd),
                        "gender": j_gender,
                        "age": int(j_age),
                        "region": j_region,
                        "credit_score": int(j_credit) if has_doc else 0,
                        "credit_doc_url": doc_name if has_doc else "",
                        "credit_status": "PENDING" if has_doc else "NONE",
                        "is_verified": False,
                        "ticket_count": WELCOME_TICKETS,
                        "is_vip": False,
                        "blocked_phones": [],
                        "last_login_at": now_utc,
                        "job": j_job.strip() if j_job else "개인사업/전문직",
                        "hobbies": j_hobbies.strip() if j_hobbies else "여가 생활",
                        "intro": (j_intro.strip() or "인생의 후반전을 서로 존중하며 함께 이야기 나눌 좋은 친구를 찾습니다."),
                        "is_admin": False,
                        "is_suspended": False
                    }
                    if kakao_id_val:
                        user_data["kakao_id"] = kakao_id_val
                    if kakao_photo_val:
                        user_data["photo_url"] = kakao_photo_val

                    try:
                        new_u = supabase.table("users").insert(user_data).execute().data[0]
                    except Exception as ins_err:
                        # DB가 'NONE' 값을 허용하지 않는 경우(제약조건 오류)에만 다시 시도합니다
                        if user_data.get("credit_status") == "NONE" and "credit_status" in str(ins_err).lower():
                            user_data["credit_status"] = "PENDING"  # 서류 없는 PENDING은 심사함에서 걸러냅니다
                            new_u = supabase.table("users").insert(user_data).execute().data[0]
                        else:
                            raise

                    uid = new_u["id"]
                    supabase.table("user_answers").insert([
                        {"user_id": uid, "question_num": 1, "answer_value": a1},
                        {"user_id": uid, "question_num": 2, "answer_value": a2},
                        {"user_id": uid, "question_num": 3, "answer_value": a3},
                        {"user_id": uid, "question_num": 4, "answer_value": a4},
                        {"user_id": uid, "question_num": 5, "answer_value": a5}
                    ]).execute()

                    if j_email_clean and valid_email(j_email_clean):
                        try:
                            supabase.table("user_answers").insert({"user_id": uid, "question_num": EMAIL_QNUM, "answer_value": j_email_clean}).execute()
                        except Exception as e:
                            log_error("email_save", e)

                    # 친구 추천: 가입 때는 "누가 초대했는지"만 기록합니다. 티켓은 친구가 첫 유료 티켓을 산 뒤에 지급합니다.
                    ref_msg = ""
                    ref_id = st.session_state.get("ref_id")
                    if ref_id and str(ref_id) != str(uid):
                        try:
                            ref_rows = supabase.table("users").select("id").eq("id", ref_id).execute().data
                            if ref_rows:
                                supabase.table("user_answers").insert({"user_id": uid, "question_num": REFERRAL_QNUM, "answer_value": f"ref:{ref_id}"}).execute()
                                ref_msg = f" 첫 유료 티켓을 구매하시면 초대해 주신 분과 함께 티켓 {REFERRAL_BONUS}장씩 드립니다."
                        except Exception:
                            pass  # 추천 기록 실패가 가입을 막지 않도록 함

                    record_free_grant(uid, WELCOME_TICKETS)
                    st.session_state.user_id = uid
                    st.session_state.user_info = new_u
                    st.success(f"🎉 서류 제출 및 가입이 완료되었습니다! 가입 선물 티켓 {WELCOME_TICKETS}장이 지급되었습니다.{ref_msg}")
                    st.rerun()
                except Exception as e:
                    if doc_name:  # 가입이 실패했으면 올라간 서류도 남기지 않음
                        try:
                            supabase.storage.from_("credit-docs").remove([doc_name])
                        except Exception:
                            pass
                    st.error(friendly_error("join", e, "가입 처리 중"))

# --- 2. 메인 대시보드 화면 ---
else:
    me = st.session_state.user_info
    # 매 화면마다 DB의 최신 티켓 수·제재·관리자 여부를 다시 읽습니다 (관리자가 충전해도 화면에 0장으로 남아 신청이 막히던 문제 방지)
    try:
        _fr = supabase.table("users").select("ticket_count,is_suspended,is_admin").eq("id", me["id"]).execute().data
    except Exception:
        _fr = None
    if _fr is not None:
        if not _fr or _fr[0].get("is_suspended"):
            st.session_state.user_id = None
            st.session_state.user_info = None
            st.session_state.kakao_user = None
            st.session_state.withdrawn_msg_5060 = "계정 상태가 변경되어 로그아웃되었습니다. 문의는 고객센터로 연락해 주세요."
            st.rerun()
        me["ticket_count"] = _fr[0].get("ticket_count") or 0
        me["is_admin"] = bool(_fr[0].get("is_admin"))
        st.session_state.user_info = me
    if not st.session_state.get("expiry_checked_5060"):
        st.session_state.expiry_checked_5060 = True
        lost = expire_free_tickets(me)
        if lost > 0:
            st.session_state.user_info = me
            st.warning(f"⏳ 지급 후 {FREE_TICKET_DAYS}일이 지난 무료 티켓 {lost}장이 소멸했습니다. (유료 티켓은 소멸하지 않았습니다)")
    my_tickets = me.get('ticket_count', 0)

    h_col1, h_col2 = st.columns([2.5, 1.5])
    with h_col1:
        st.markdown(f'<div class="app-brand">🌟 {BRAND_NAME_KR}</div>', unsafe_allow_html=True)
    with h_col2:
        st.markdown(f"""
            <div style="text-align:right; margin-top:4px;">
                <span style="font-size:1.05rem; font-weight:900; color:#7A4A00;">🎟️ {my_tickets}장</span>
            </div>
        """, unsafe_allow_html=True)

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

    tabs_main = st.tabs(["✨ 추천 피드", "📬 신청 보관함", "💳 티켓 충전", "👤 내 프로필"])

    my_ans_data = supabase.table("user_answers").select("question_num, answer_value").eq("user_id", me["id"]).execute().data
    my_answers = {item["question_num"]: item["answer_value"] for item in my_ans_data if 1 <= item["question_num"] <= 5}

    # --- TAB 1: 추천 피드 ---
    with tabs_main[0]:
        # 성별로 상대를 정하지 않습니다. 본인을 제외한 모든 회원이 최근 접속순으로 나옵니다.
        # 비밀번호 등 불필요한 정보는 가져오지 않고, 최근 접속자 위주로 최대 300명만 불러옵니다.
        raw_candidates = supabase.table("users")\
            .select("id,name,phone,gender,age,region,job,intro,photo_url,credit_score,credit_status,blocked_phones")\
            .neq("id", me["id"])\
            .gte("age", 48)\
            .lte("age", 75)\
            .eq("is_suspended", False)\
            .order("last_login_at", desc=True)\
            .limit(300)\
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
            st.info("현재 활동 중인 추천 동반자가 없습니다.")
        else:
            cand_scores = []
            # 후보 전원의 답변을 한 번에 가져옵니다 (후보마다 따로 조회하면 느려집니다).
            all_ans = supabase.table("user_answers").select("user_id, question_num, answer_value")\
                .in_("user_id", [c["id"] for c in candidates]).execute().data
            ans_by_user = {}
            for item in all_ans:
                if 1 <= item["question_num"] <= 5:  # 장부용 행(90~92번)은 궁합 계산에서 제외
                    ans_by_user.setdefault(item["user_id"], {})[item["question_num"]] = item["answer_value"]
            for cand in candidates:
                c_answers = ans_by_user.get(cand["id"], {})
                
                common_keys = set(my_answers.keys()).intersection(set(c_answers.keys()))
                score = int((sum(1 for k in common_keys if my_answers[k] == c_answers[k]) / len(common_keys)) * 100) if common_keys else 0
                cand_scores.append((cand, c_answers, common_keys, score))

            # 점수 순 정렬을 하지 않습니다(최근 접속순 유지). 비교 점수는 참고용 표시입니다.

            for cand, c_answers, common_keys, score in cand_scores:
                c_img = esc(blur_photo_url(cand.get("photo_url"), cand["gender"]))
                intro_txt = esc(cand.get("intro") or "서로를 존중하며 함께 시간을 나눌 좋은 친구를 기다립니다.")

                st.markdown(flat_html(f"""
                    <div class="senior-card">
                        <div class="senior-img-box">
                            <img src="{c_img}" class="senior-img-blur">
                            <div class="senior-overlay"></div>
                            <div class="senior-blind-tag">🔒 안심 비공개 보호</div>
                            <div class="senior-match-badge">관심사 {score}% 비슷</div>
                        </div>
                        <div class="senior-content">
                            <div class="senior-name-row">
                                <span class="senior-name">{esc(cand['name'][0])}*님</span>
                                <span class="senior-age">{esc(cand['age'])}세 · {esc(cand['region'].split()[0])}</span>
                            </div>
                            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px;">
                                <span class="badge-pill-gold">💼 {esc(cand.get('job') or '경력 인증')}</span>
                                {'<span class="badge-pill-credit">🛡️ 인증 회원</span>' if cand.get('credit_status') == 'VERIFIED' else ''}
                            </div>
                            <div class="senior-intro">"{intro_txt}"</div>
                        </div>
                    </div>
                """), unsafe_allow_html=True)

                with st.expander("🔍 5가지 질문 상세 비교"):
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
                    st.button(f"⏳ 수락 대기중 ({cand['name'][0]}*님)", key=f"feed_btn_{cand['id']}", disabled=True)
                elif req_status == "ACCEPTED":
                    st.success("🎉 서로 수락했어요! 보관함에서 선명한 사진과 연락처를 확인하세요.")
                else:
                    if st.button(f"💌 대화 신청하기 (티켓 1장)", key=f"feed_btn_{cand['id']}"):
                        if my_tickets <= 0:
                            st.error("🚨 보유 티켓이 부족합니다. 상단의 [💳 티켓 충전] 탭에서 충전 후 이용해 주세요.")
                        elif supabase.table("match_requests").select("id").eq("sender_id", me["id"]).eq("receiver_id", cand["id"]).in_("status", ["PENDING", "ACCEPTED"]).execute().data:
                            st.warning("이미 대화를 신청한 분입니다.")
                        else:
                            new_bal = adjust_tickets(me["id"], -1)  # 최신 잔액 기준으로 안전하게 차감
                            if new_bal is None:
                                st.error("티켓이 부족하거나 처리 중 문제가 생겼습니다. 화면을 새로고침한 뒤 다시 시도해 주세요.")
                            else:
                                me["ticket_count"] = new_bal
                                st.session_state.user_info = me
                                try:
                                    supabase.table("match_requests").insert({
                                        "sender_id": me["id"],
                                        "receiver_id": cand["id"],
                                        "status": "PENDING",
                                        "payment_status": "PAID"
                                    }).execute()
                                except Exception as e:
                                    back = adjust_tickets(me["id"], 1)  # 신청 기록이 실패하면 티켓을 되돌림
                                    if back is not None:
                                        me["ticket_count"] = back
                                        st.session_state.user_info = me
                                    st.error(friendly_error("send_request", e, "신청 처리 중"))
                                else:
                                    send_aligo_notice_sms(cand["phone"], f"{me['name'][0]}* 님으로부터 대화 신청이 도착했습니다.")
                                    st.rerun()

                st.caption(f"ℹ️ 대화 신청 시 티켓 1장이 사용되며, 상대방 거절/72시간 미응답 시 티켓은 자동 반환됩니다. (미사용 티켓 7일 이내 100% 환불) · 가입·추천 선물 티켓은 지급일부터 {FREE_TICKET_DAYS}일 후 소멸합니다.")
                st.write("")

    # --- TAB 2: 신청 보관함 ---
    with tabs_main[1]:
        pending_sent = supabase.table("match_requests")\
            .select("*")\
            .eq("sender_id", me["id"])\
            .eq("status", "PENDING")\
            .execute().data
            
        now_dt = datetime.now(timezone.utc)
        restored_count = 0
        
        for req in pending_sent:
            created_str = req.get("created_at")
            if created_str:
                try:
                    clean_ts = created_str.split(".")[0].replace("Z", "")
                    created_dt = datetime.fromisoformat(clean_ts).replace(tzinfo=timezone.utc)
                    if now_dt - created_dt > timedelta(hours=72):
                        # 아직 '대기중'인 것만 바꾸고, 실제로 바뀐 건수만 티켓을 돌려줍니다 (두 화면에서 동시에 열어도 이중 반환 방지)
                        if supabase.table("match_requests").update({"status": "EXPIRED"}).eq("id", req["id"]).eq("status", "PENDING").execute().data:
                            restored_count += 1
                except Exception:
                    continue

        if restored_count > 0:
            new_ticket_val = adjust_tickets(me["id"], restored_count)
            if new_ticket_val is not None:
                me["ticket_count"] = new_ticket_val
                st.session_state.user_info = me
            st.info(f"💡 72시간 동안 응답이 없는 신청 {restored_count}건이 자동 취소되어 티켓 {restored_count}장이 정상 반환되었습니다.")

        inbox_1, inbox_2 = st.tabs(["내가 보낸 신청", "나에게 온 신청"])
        
        with inbox_1:
            sent_list = supabase.table("match_requests").select("*").eq("sender_id", me["id"]).execute().data
            if not sent_list:
                st.caption("보낸 신청이 없습니다.")
            else:
                for req in sent_list:
                    _rr = supabase.table("users").select("id,name,phone,gender,photo_url,job").eq("id", req["receiver_id"]).execute().data
                    if not _rr:
                        continue  # 탈퇴한 회원의 기록은 건너뜁니다
                    rcv = _rr[0]
                    if req["status"] == "ACCEPTED":
                        st.success(f"🎉 **{md_esc(rcv['name'])}** 님과 서로 연결되었습니다!")
                        r_img = esc(clear_photo_url(rcv.get("photo_url"), rcv["gender"]))
                        st.markdown(f"""
                            <div class="senior-card">
                                <div class="senior-img-box">
                                    <img src="{r_img}" class="senior-img-clear">
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        st.write(f"📞 안심 연락처: **{only_digits(rcv['phone'])}** | 💼 경력: **{md_esc(rcv.get('job'))}**")
                        st.markdown(f'<a href="tel:{only_digits(rcv["phone"])}">📞 바로 전화 걸기</a>', unsafe_allow_html=True)
                    elif req["status"] == "REJECTED":
                        st.write(f"• **{rcv['name'][0]}*님**이 신청을 정중히 사양하여 **티켓 1장이 즉시 반환**되었습니다.")
                    elif req["status"] == "EXPIRED":
                        st.write(f"• **{rcv['name'][0]}*님**의 72시간 미응답으로 자동 취소되어 **티켓 1장이 반환**되었습니다.")
                    else:
                        st.write(f"• **{rcv['name'][0]}*님**에게 보낸 신청 | 상태: `수락 대기중`")

        with inbox_2:
            rcv_list = supabase.table("match_requests").select("*").eq("receiver_id", me["id"]).execute().data
            if not rcv_list:
                st.caption("도착한 신청이 없습니다.")
            else:
                for req in rcv_list:
                    _sr = supabase.table("users").select("id,name,phone,gender,age,photo_url,job").eq("id", req["sender_id"]).execute().data
                    if not _sr:
                        continue  # 탈퇴한 회원의 기록은 건너뜁니다
                    snd = _sr[0]
                    st.markdown(f"**{snd['name'][0]}*님** ({snd['gender']} · {snd['age']}세 · {md_esc(snd.get('job'))})")
                    if req["status"] == "ACCEPTED":
                        st.success("🤝 대화 수락 완료! 연락처가 공개되었습니다.")
                        s_img = esc(clear_photo_url(snd.get("photo_url"), snd["gender"]))
                        st.markdown(f"""
                            <div class="senior-card">
                                <div class="senior-img-box">
                                    <img src="{s_img}" class="senior-img-clear">
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        st.write(f"📞 안심 연락처: **{only_digits(snd['phone'])}**")
                    elif req["status"] == "PENDING":
                        col_ac, col_re = st.columns(2)
                        with col_ac:
                            if st.button("수락 및 연락처 공유", key=f"ac_{req['id']}"):
                                _u = supabase.table("match_requests").update({"status": "ACCEPTED"}).eq("id", req["id"]).eq("status", "PENDING").execute().data
                                if _u:  # 아직 대기중일 때만 수락 처리 (이미 취소·만료된 신청은 무시)
                                    send_aligo_notice_sms(snd["phone"], f"{me['name'][0]}* 님이 대화를 수락했습니다. 안심 연락처를 확인하세요.")
                                st.rerun()
                        with col_re:
                            if st.button("거절", key=f"re_{req['id']}"):
                                _u = supabase.table("match_requests").update({"status": "REJECTED"}).eq("id", req["id"]).eq("status", "PENDING").execute().data
                                if _u:  # 아직 대기중일 때만 거절 처리 + 티켓 1장 반환 (중복 반환 방지)
                                    adjust_tickets(snd["id"], 1)
                                    send_aligo_notice_sms(snd["phone"], "보내신 대화 신청이 정중히 사양되었으며, 사용하신 티켓 1장이 정상 복구되었습니다.")
                                st.rerun()
                    st.divider()

    # --- TAB 3: 티켓 충전소 ---
    with tabs_main[2]:
        st.markdown(f"""
            <div style="text-align:center; padding: 10px 0 16px 0;">
                <h3 style="color:#1A1A1A; margin-bottom:4px;">👑 대화 신청 티켓 충전</h3>
                <div style="font-size:1rem; color:#3A3A3A;">현재 회원님의 보유 티켓: <strong style="color:#7A4A00; font-size:1.05rem;">{my_tickets}장</strong></div>
            </div>
        """, unsafe_allow_html=True)

        d3 = round((1 - TICKET_PRICE_3 / (TICKET_PRICE_1 * 3)) * 100)
        d5 = round((1 - TICKET_PRICE_5 / (TICKET_PRICE_1 * 5)) * 100)
        st.markdown(f"""
            <div class="shop-card">
                <div>
                    <div class="shop-title">🎟️ 1회 대화 신청권</div>
                    <div class="shop-desc">마음에 드는 동반자 1명에게 신청</div>
                </div>
                <div class="shop-price">{won(TICKET_PRICE_1)}</div>
            </div>
            
            <div class="shop-card featured">
                <div>
                    <span class="shop-badge">⭐ 가장 많은 선택</span>
                    <div class="shop-title">🌟 3회 실속 패키지</div>
                    <div class="shop-desc">3회 신청 (회당 약 {won(round(TICKET_PRICE_3 / 3))} / {d3}% 할인)</div>
                </div>
                <div class="shop-price">{won(TICKET_PRICE_3)}</div>
            </div>

            <div class="shop-card">
                <div>
                    <span class="shop-badge" style="background:#854D0E;">👑 VIP 추천</span>
                    <div class="shop-title">👑 5회 VIP 전담 패키지</div>
                    <div class="shop-desc">5회 신청 (회당 약 {won(round(TICKET_PRICE_5 / 5))} / {d5}% 할인)</div>
                </div>
                <div class="shop-price">{won(TICKET_PRICE_5)}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="bank-box">
                <div style="font-size:1rem; color:#1A1A1A; font-weight:700;">🏦 무통장 안심 입금 계좌</div>
                <div style="font-size:1.15rem; font-weight:900; color:#7A4A00; margin:6px 0;">{BANK_INFO['bank']} {BANK_INFO['account']}</div>
                <div style="font-size:0.95rem; color:#3A3A3A;">예금주: {esc(BANK_INFO['holder'])} (입금자명: <strong>{esc(me['name'])}</strong>)</div>
            </div>
        """, unsafe_allow_html=True)

        st.info("💡 입금 후 아래 **[카카오톡 1:1 입금 확인]** 버튼을 누르시고 성함을 남겨주시면, 담당 매니저가 즉시 확인 후 티켓을 충전해 드립니다.")
        
        st.markdown(f"""
            <a href="{KAKAO_CHAT_URL}" target="_blank" style="text-decoration:none;">
                <div style="background:#FEE500; color:#191919; text-align:center; padding:15px; border-radius:12px; font-weight:900; font-size:1.05rem; box-shadow:0 4px 14px rgba(254, 229, 0, 0.3); margin-bottom:18px;">
                    💬 카카오톡 1:1 입금 확인 및 환불 문의
                </div>
            </a>
        """, unsafe_allow_html=True)

        with st.expander("⚖️ 전자상거래법에 따른 티켓 환불 및 안심 이용 규정 안내"):
            st.markdown(f"""
            **0. 서비스 제공 방식과 이용 기간**
            * 구매한 이용권(티켓)은 결제(입금 확인) 후 즉시 내 계정에 충전되며, 별도 배송은 없습니다. 유료 티켓은 구매일부터 1년간 사용할 수 있고, 가입·추천 선물 티켓은 지급일부터 {FREE_TICKET_DAYS}일 후 소멸합니다.

            **1. 미사용 티켓 100% 청약철회 (환불)**
            * 구매 후 **7일 이내에 전혀 사용하지 않은 티켓**은 전자상거래법 제17조에 따라 별도의 수수료 없이 **결제 금액 전액(100%) 환불**됩니다.

            **2. 사용한 티켓의 환불 제한**
            * 상대방 프로필에 대화 신청을 전송하여 **이미 사용(차감)된 티켓은 디지털 용역 제공이 완료된 것으로 간주되어 환불이 불가**합니다.
            * 패키지 상품 중 일부만 사용한 경우, 미사용 잔여 티켓은 전체 결제액에서 사용한 횟수만큼 단품 정가(회당 {won(TICKET_PRICE_1)})를 차감한 후 잔여액을 반환합니다.

            **3. 대화 신청 거절 및 72시간 미응답 시 티켓 보호**
            * 신청을 받은 상대방이 정중히 '거절'하거나 72시간 이내 응답이 없을 경우, **차감된 티켓은 보유 수량으로 100% 자동 반환**됩니다.
            """)

    # --- TAB 4: 프로필 관리 ---
    with tabs_main[3]:
        my_avatar = esc(me.get("photo_url") or DEFAULT_AVATARS.get(me["gender"]))
        st.markdown(f"""
            <div style="text-align:center; padding:10px 0 20px 0;">
                <img src="{my_avatar}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border:3px solid #B7791F;">
                <h3 style="margin:10px 0 4px 0; color:#1A1A1A;">{esc(me['name'])} ({esc(me['gender'])} · {esc(me['age'])}세)</h3>
                <div style="font-size:1rem; color:#222222;">📍 {esc(me['region'])} | 💼 {esc(me.get('job'))}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🎁 친구 초대하고 티켓 받기")
        try:
            invited = len(supabase.table("user_answers").select("user_id").eq("question_num", REFERRAL_QNUM).eq("answer_value", f"ref:{me['id']}").execute().data)
        except Exception:
            invited = 0
        st.caption(f"아래 링크로 친구가 가입하고 첫 유료 티켓을 구매하면 두 분 모두 티켓 {REFERRAL_BONUS}장을 받습니다. (보상 최대 {REFERRAL_MAX_REWARDS}명 · 현재 {invited}명이 링크로 가입)")
        st.code(f"{SHARE_URL}/?ref={me['id']}", language=None)
        st.markdown("---")

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
            if len(edit_job) > 60 or len(edit_hobbies) > 100 or len(edit_intro) > 500:
                st.error("직업은 60자, 취미는 100자, 소개글은 500자 이내로 적어 주세요.")
            else:
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
        st.caption("등록된 사진은 서로 수락하기 전까지 흐리게 처리되어 안전하게 보호되며, 상호 수락 시에만 상대방에게 선명하게 공개됩니다.")
        new_avatar = st.file_uploader("사진 파일 선택 (JPG, PNG)", type=["jpg", "png", "jpeg"], key="up_avatar")
        if new_avatar and st.button("사진 등록 및 저장"):
            av_err = check_image_upload(new_avatar)
            if av_err:
                st.error(av_err)
            else:
                try:
                    clean_jpg = sanitize_image(new_avatar.getvalue())  # JPEG로 다시 저장 (위치정보 등 숨은 정보 제거, 크기 축소)
                    fname = f"avatar_5060_{me['id']}_{uuid.uuid4().hex}.jpg"  # 32자 무작위 꼬리: 주소를 추측할 수 없음
                    supabase.storage.from_("avatars").upload(fname, clean_jpg, {"content-type": "image/jpeg"})
                    try:
                        supabase.storage.from_("avatars").upload(blur_fname_for(fname), make_blurred_copy(clean_jpg), {"content-type": "image/jpeg"})
                    except Exception:
                        st.warning("흐림 처리 사본을 만들지 못해 피드에는 기본 이미지가 표시됩니다.")
                    url = f"{SUPABASE_URL}/storage/v1/object/public/avatars/{fname}"
                    old_url = me.get("photo_url")
                    supabase.table("users").update({"photo_url": url}).eq("id", me["id"]).execute()
                    remove_avatar_files(None, old_url)  # 예전 사진 원본·흐린 사본 삭제 (남겨두면 개인정보가 계속 보관됨)
                    me["photo_url"] = url
                    st.session_state.user_info = me
                except Exception as e:
                    st.error(friendly_error("avatar_upload", e, "사진 등록 중"))
                else:
                    st.success("사진이 등록되었습니다. 서로 수락하기 전에는 사진 보호가 자동 적용됩니다.")
                    st.rerun()

        # ---- 회원 탈퇴 (개인정보 보호법: 정보주체가 동의를 철회할 수 있어야 함) ----
        st.markdown("---")
        with st.expander("⚠️ 회원 탈퇴"):
            if me.get("is_admin"):
                st.info("관리자 계정은 이 화면에서 탈퇴할 수 없습니다.")
            else:
                st.markdown(f"""
                탈퇴하면 아래 정보가 **바로 삭제되며 되돌릴 수 없습니다.**
                - 이름, 휴대폰 번호, 비밀번호, 프로필 사진(원본·흐린 사본), 소개글, 질문 답변, 차단 목록
                - 주고받은 대화 신청 기록 (대기 중인 신청을 받으신 상대방에게는 티켓이 반환됩니다)

                **보관되는 정보**: 유료 티켓을 충전하신 적이 있다면, 전자상거래법에 따라 **결제 기록(충전 날짜·수량·금액)만 5년간** 따로 보관한 뒤 파기합니다. 이름·연락처는 남기지 않습니다.

                현재 보유 티켓은 **{my_tickets}장**이며, 탈퇴하면 소멸합니다. 환불이 필요하시면 탈퇴 전에 카카오톡 1:1 상담으로 먼저 문의해 주세요. (미사용 티켓은 7일 이내 100% 환불)
                """)
                w_pwd = st.text_input("비밀번호 재확인", type="password", key="w_pwd_5060")
                w_ok1 = st.checkbox("위 내용을 모두 확인했으며, 탈퇴에 동의합니다.", key="w_ok1_5060")
                w_ok2 = st.checkbox("남은 티켓이 소멸하고 삭제된 정보는 복구할 수 없음을 이해했습니다.", key="w_ok2_5060")
                if st.button("회원 탈퇴 진행", key="w_btn_5060"):
                    wk = "withdraw_" + str(me["id"])
                    if not (w_ok1 and w_ok2):
                        st.error("두 가지 확인 항목에 모두 체크해 주세요.")
                    elif rl_count(wk, 900) >= 5:
                        st.error("비밀번호를 여러 번 틀리셨습니다. 15분 뒤에 다시 시도해 주세요.")
                    else:
                        try:
                            fresh = supabase.table("users").select("password,is_admin").eq("id", me["id"]).execute().data
                            if not fresh:
                                st.error("회원 정보를 찾을 수 없습니다.")
                            elif fresh[0].get("is_admin"):
                                st.error("관리자 계정은 탈퇴할 수 없습니다.")
                            elif not verify_password(w_pwd, fresh[0].get("password", "")):
                                rl_hit(wk, 900)
                                st.error("비밀번호가 일치하지 않습니다.")
                            else:
                                w_ok, w_msg = withdraw_member(me["id"])
                                if w_ok:
                                    for _k in ("expiry_checked_5060", "login_fail_5060", "ref_id"):
                                        st.session_state.pop(_k, None)
                                    st.session_state.user_id = None
                                    st.session_state.user_info = None
                                    st.session_state.kakao_user = None
                                    st.session_state.withdrawn_msg_5060 = w_msg
                                    st.rerun()
                                else:
                                    st.error(w_msg)
                        except Exception as e:
                            st.error(friendly_error("withdraw", e, "탈퇴 처리 중") + " (일부 정보만 삭제되었을 수 있으니 고객센터에 알려 주세요.)")

    # 👑 [관리자 전용] 5060 서류 심사 및 즉시 파기 센터
    if me.get("is_admin"):
        st.markdown("---")
        st.caption(f"🔐 현재 앱이 쓰는 DB 키 종류: {detect_key_role()} (키 값은 표시하지 않습니다)")
        with st.expander("💳 [관리자 전용] 입금 확인 후 티켓 충전"):
            st.caption("법인 계좌 입금을 확인한 뒤에만 사용하세요. 충전 내역이 기록되고, 친구 추천으로 가입한 분의 첫 충전이면 추천 보상이 자동 지급됩니다.")
            ch_phone = st.text_input("충전할 회원 휴대폰 번호 (숫자만)", key="adm_ch_phone")
            ch_qty = st.selectbox("충전 티켓 수", [1, 3, 5], key="adm_ch_qty")
            ch_ok = st.checkbox("입금(금액·입금자명)을 확인했습니다.", key="adm_ch_ok")
            if st.button("티켓 충전 실행", key="adm_ch_btn"):
                cp = re.sub(r"[^0-9]", "", ch_phone or "")
                tgt = supabase.table("users").select("id,name,ticket_count").eq("phone", cp).execute().data if cp else []
                if not ch_ok:
                    st.error("입금 확인 체크를 먼저 해 주세요.")
                elif not tgt:
                    st.error("해당 번호의 회원을 찾지 못했습니다.")
                else:
                    t = tgt[0]
                    price = {1: TICKET_PRICE_1, 3: TICKET_PRICE_3, 5: TICKET_PRICE_5}[ch_qty]
                    purchases, p_exists = _ledger_get(t["id"], PURCHASE_QNUM)
                    first_purchase = len(purchases) == 0
                    purchases.append({"qty": ch_qty, "price": price, "at": datetime.now(timezone.utc).isoformat()})
                    _ledger_put(t["id"], PURCHASE_QNUM, purchases, p_exists)  # 기록을 먼저 남김
                    if adjust_tickets(t["id"], ch_qty) is None:
                        st.error("티켓 충전에 실패했습니다. 충전 기록은 남았을 수 있으니 회원 티켓 수를 확인한 뒤 다시 시도해 주세요.")
                        st.stop()
                    msg = f"{md_esc(t['name'])} 님에게 티켓 {ch_qty}장({won(price)})을 충전했습니다."
                    if first_purchase:
                        try:
                            inv = supabase.table("user_answers").select("answer_value").eq("user_id", t["id"]).eq("question_num", REFERRAL_QNUM).execute().data
                            rid = inv[0]["answer_value"].split("ref:")[1] if inv and "ref:" in inv[0]["answer_value"] else None
                            if rid:
                                paid_cnt = len(supabase.table("user_answers").select("user_id").eq("question_num", REFERRAL_PAID_QNUM).eq("answer_value", f"rewarded:{rid}").execute().data)
                                if paid_cnt < REFERRAL_MAX_REWARDS:
                                    supabase.table("user_answers").insert({"user_id": t["id"], "question_num": REFERRAL_PAID_QNUM, "answer_value": f"rewarded:{rid}"}).execute()
                                    r_rows = supabase.table("users").select("id,ticket_count").eq("id", rid).execute().data
                                    if r_rows:
                                        adjust_tickets(rid, REFERRAL_BONUS)
                                        record_free_grant(rid, REFERRAL_BONUS)
                                        adjust_tickets(t["id"], REFERRAL_BONUS)
                                        record_free_grant(t["id"], REFERRAL_BONUS)
                                        msg += f" 친구 추천 보상으로 두 분께 티켓 {REFERRAL_BONUS}장씩 추가 지급했습니다."
                        except Exception:
                            msg += " (추천 보상 처리 중 오류 — 수동 확인 필요)"
                    st.success(msg)
        st.markdown("---")
        with st.expander("👑 [관리자 전용] 5060 서류 심사 및 즉시 파기 센터"):
            pending_users = [u for u in supabase.table("users").select("*").eq("credit_status", "PENDING").execute().data if u.get("credit_doc_url")]
            if not pending_users:
                st.success("현재 심사 대기 중인 회원이 없습니다.")
            else:
                st.caption(f"총 {len(pending_users)}명의 서류 검토 대기자가 있습니다.")
                for pu in pending_users:
                    st.markdown(f"**신청자:** {md_esc(pu['name'])} ({pu['gender']} · {pu['age']}세 · {md_esc(pu.get('job'))} · 신용 {pu['credit_score']}점)")
                    st.caption(f"연락처: {only_digits(pu['phone'])}")
                    
                    doc_path = pu.get("credit_doc_url", "")
                    if doc_path and not doc_path.startswith("["):
                        try:
                            raw_path = doc_path.split("/")[-1]
                            signed = supabase.storage.from_("credit-docs").create_signed_url(raw_path, 60)
                            s_url = signed.get("signedURL") or signed.get("signedUrl")
                            if s_url:
                                st.markdown(f'<a href="{s_url}" target="_blank">📄 [안심 열람] 증빙서류 1회용 링크 열기 (60초 후 만료)</a>', unsafe_allow_html=True)
                        except Exception as err:
                            st.caption(f"서류 링크를 만들지 못했습니다. (문의번호 {log_error('doc_link', err)})")

                    col_ap, col_rj = st.columns(2)
                    with col_ap:
                        if st.button(f"✅ 승인 및 서류 영구 파기", key=f"btn_ap_5060_{pu['id']}"):
                            raw_fname = doc_path.split("/")[-1]
                            try:
                                supabase.storage.from_("credit-docs").remove([raw_fname])
                            except Exception:
                                pass
                            
                            supabase.table("users").update({
                                "is_verified": True,
                                "credit_status": "VERIFIED",
                                "credit_doc_url": "[심사 완료 후 안전 파기됨]"
                            }).eq("id", pu["id"]).execute()

                            send_aligo_notice_sms(pu["phone"], "노블레스 라온 신원 및 신용 검증이 완료되었습니다. 제출 서류는 안전하게 영구 파기되었습니다.")
                            st.success(f"{md_esc(pu['name'])} 님이 정회원으로 승인되었습니다.")
                            st.rerun()

                    with col_rj:
                        if st.button(f"🚫 반려 및 서류 파기", key=f"btn_rj_5060_{pu['id']}"):
                            raw_fname = doc_path.split("/")[-1]
                            try:
                                supabase.storage.from_("credit-docs").remove([raw_fname])
                            except Exception:
                                pass
                            
                            supabase.table("users").update({
                                "is_verified": False,
                                "credit_status": "REJECTED",
                                "credit_doc_url": "[반려 후 안전 파기됨]"
                            }).eq("id", pu["id"]).execute()

                            send_aligo_notice_sms(pu["phone"], "제출하신 증빙 서류가 기준에 미달하여 반려되었습니다. 다시 등록해 주세요.")
                            st.warning(f"{md_esc(pu['name'])} 님의 신청이 반려되었습니다.")
                            st.rerun()
                    st.divider()

    st.markdown("---")
    if st.button("로그아웃"):
        st.session_state.user_id = None
        st.session_state.user_info = None
        st.session_state.kakao_user = None
        for _k in ("expiry_checked_5060", "login_fail_5060", "ref_id"):
            st.session_state.pop(_k, None)
        st.rerun()

# --- 자주 묻는 질문 (로그인 전·후 모두 하단에 표시) ---
FAQ_ITEMS = [
    ("노블레스 라온은 어떤 서비스인가요?",
     "만 48세~75세 성인이 **동반자·친구**를 만나도록 돕는 온라인 서비스입니다. 회원이 직접 프로필을 보고 대화를 신청합니다. 노블레스 라온은 동반자·친구 만남만 돕습니다."),
    ("가입은 어떻게 하나요?",
     "**카카오로 시작하기**를 누르신 뒤 이름, 휴대폰 번호, 간단한 정보를 적으시면 됩니다. 카카오를 쓰지 않으실 때는 이메일로 받은 6자리 인증번호를 입력해 주세요. 신용점수와 서류는 **선택**이라 건너뛰셔도 됩니다."),
    ("가입비가 있나요? 무료로 써 볼 수 있나요?",
     "가입은 무료입니다. 가입하시면 대화 신청 티켓 **1장**을 드립니다. 이 무료 티켓은 지급일부터 **90일 안에** 쓰셔야 하며, 기간이 지나면 사라집니다."),
    ("티켓은 무엇이고 얼마인가요?",
     f"마음에 드는 분께 대화를 신청할 때 티켓 1장이 쓰입니다. 1회 {won(TICKET_PRICE_1)}, 3회 {won(TICKET_PRICE_3)}, 5회 {won(TICKET_PRICE_5)}입니다."),
    ("입금했는데 티켓이 안 들어왔어요.",
     "입금 확인 후 티켓을 넣어 드립니다. 확인에 시간이 걸릴 수 있습니다. 카카오톡 1:1 상담창이나 대표전화로 **입금자명, 입금 날짜, 금액**을 알려 주시면 더 빨리 확인합니다. 안내된 법인 계좌 외에는 입금하지 마세요."),
    ("환불받고 싶어요.",
     f"구매 후 **7일 안에** 티켓을 하나도 쓰지 않으셨다면 전액 환불해 드립니다. 일부 쓰셨다면 결제 금액에서 쓰신 횟수만큼 1회 정가({won(TICKET_PRICE_1)})를 뺀 금액을 돌려 드립니다. 환불은 카카오톡 1:1 상담창이나 대표전화로 요청해 주세요. 확인 후 3영업일 안에 처리합니다. 이미 쓴 티켓은 환불되지 않지만, 아래 거절·미응답 반환은 별도입니다."),
    ("상대가 거절하면 티켓은 어떻게 되나요?",
     "상대가 거절하거나 **72시간 안에 답이 없으면** 티켓 1장이 자동으로 돌아옵니다. [신청 보관함]에서 상태를 확인해 주세요. 화면에 안 보이면 새로고침해 주세요."),
    ("72시간이 지났는데 티켓이 안 돌아왔어요.",
     "72시간이 지난 신청은 회원님이 앱을 열었을 때 정리되어 티켓이 돌아옵니다. 앱에서 [신청 보관함]을 한 번 눌러 보세요. 그래도 돌아오지 않으면 알려 주세요."),
    ("사진이 왜 흐리게 보이나요?",
     "회원님 보호를 위해 **서로 수락하기 전까지는 사진이 흐리게** 보입니다. 서로 수락하시면 선명한 사진과 연락처가 공개됩니다. 대화 신청을 하시면 수락 시 내 이름·연락처·사진이 상대에게 공개됩니다."),
    ("사진을 올렸는데 안 바뀌어요.",
     "JPG, PNG 사진만 올릴 수 있습니다. [내 프로필] 탭에서 사진을 고른 뒤 **'사진 등록 및 저장'** 버튼까지 눌러 주세요. 그래도 안 되면 사진 크기를 줄여서 다시 올려 보세요."),
    ("비밀번호를 잊었어요. 로그인이 안 돼요.",
     "로그인 화면의 **'비밀번호를 잊으셨나요?'** 를 눌러 가입한 이름과 이메일을 넣으면 이메일로 숫자가 갑니다(스팸함도 확인해 주세요). 그 숫자를 넣으면 새 비밀번호를 정할 수 있습니다. 이름은 가입 때 적으신 그대로(띄어쓰기 포함) 넣어 주세요. 이메일을 등록하지 않으셨다면 카카오톡 상담창으로 문의해 주세요. 여러 번 틀리면 잠시 로그인이 막힐 수 있습니다."),
    ("카카오로 들어왔는데 가입이 안 돼요.",
     "이미 같은 휴대폰 번호로 가입하셨다면 카카오로 새로 가입되지 않습니다. 로그인 화면의 **'정회원 로그인'** 탭에서 이름, 휴대폰 번호, 비밀번호로 들어와 주세요."),
    ("이상한 사람(돈 요구 등)이 있어요. 신고는 어떻게 하나요?",
     "불편을 드려 죄송합니다. 상대방의 보이는 정보(이름 첫 글자, 나이, 지역, 신청 시기)를 **카카오톡 1:1 상담창이나 이메일**로 알려 주세요. 확인 후 조치합니다. **돈을 보내셨다면 먼저 경찰(112)과 은행에 알려 주세요.** 돈, 계좌번호, 투자를 요구하는 분은 응하지 않으시는 것이 안전합니다."),
    ("특정 사람에게 내 정보가 안 보이게 하고 싶어요.",
     "프로필 화면의 **아는 분 번호 차단**에 그분 휴대폰 번호를 넣으시면 서로 보이지 않습니다. (차단 번호는 목록을 거른 용도로만 쓰입니다.)"),
    ("신용점수와 서류는 꼭 내야 하나요?",
     "**선택**입니다. 내지 않으셔도 이용에 불이익이 없습니다. 내시면 확인 후 '인증 회원' 표시가 붙고, 제출한 서류는 확인 후 파기합니다. 주민등록번호 등은 가리고 올려 주세요."),
    ("친구를 초대하면 어떤 혜택이 있나요?",
     "[내 프로필]의 초대 링크로 친구가 가입하고 **첫 유료 티켓을 구매하면** 두 분 모두 티켓 1장을 받습니다. 한 분이 보상받을 수 있는 초대는 최대 5명입니다. 연락처를 모아서 보내는 것은 하지 말아 주세요."),
    ("탈퇴하고 싶어요.",
     "[내 프로필] 맨 아래 **'회원 탈퇴'** 에서 비밀번호를 확인하면 탈퇴할 수 있습니다. 개인정보는 지체 없이 지우며, 결제·환불 기록은 법에 따라 일정 기간 별도로 보관합니다. 남은 티켓은 탈퇴 전에 환불 가능한지 상담해 주세요."),
    ("문의는 어디로 하나요?",
     "카카오톡 1:1 상담창, 대표전화 050-6798-3349, 이메일 equivisionai@gmail.com 으로 문의해 주세요. 상담 내용에 비밀번호나 주민등록번호는 적지 마세요."),
]

def render_faq():
    st.markdown("---")
    st.markdown("### ❓ 자주 묻는 질문")
    for _i, (_q, _a) in enumerate(FAQ_ITEMS, 1):
        with st.expander(f"Q{_i}. {_q}"):
            st.markdown(_a)

render_faq()

# --- 이용약관·개인정보 처리방침 (누구나 로그인 없이 읽을 수 있음) ---
from legal_text import TERMS_MD, PRIVACY_MD
with st.expander("📜 이용약관"):
    st.markdown(TERMS_MD)
with st.expander("🔒 개인정보 처리방침"):
    st.markdown(PRIVACY_MD)

# --- [법적 필수 표기] 플랫폼 하단 사업자 정보 푸터 ---
st.markdown("""
    <div style="margin-top: 50px; padding: 22px 14px; border-top: 2px solid #D9C48F; font-size: 0.92rem; color: #4A4A4A; line-height: 1.7; word-break: keep-all;">
        <div style="font-weight: 800; color: #222222; margin-bottom: 6px;">(주)이퀴비젼에이아이 사업자 정보</div>
        <div><strong>상호명:</strong> 이퀴비젼에이아이 주식회사 | <strong>대표자:</strong> 오성수</div>
        <div><strong>사업자등록번호:</strong> 302-88-04351 | <strong>통신판매업신고번호:</strong> 제2026-서울금천-2071호 (2026.10.15 신고)</div>
        <div><strong>사업장 주소:</strong> 서울특별시 금천구 벚꽃로 30, 206동 318호(독산동, 금천 롯데캐슬 골드파크 2차)</div>
        <div><strong>대표전화:</strong> 050-6798-3349 | <strong>고객센터:</strong> 카카오톡 1:1 상담창 | <strong>이메일:</strong> equivisionai@gmail.com</div>
        <div style="margin-top: 8px; font-size: 0.85rem; color: #555555;">
            © 2026 EQUIVISION AI Inc. All rights reserved. 본 플랫폼은 전자상거래법 및 개인정보보호법을 준수합니다.
        </div>
    </div>
""", unsafe_allow_html=True)
        

