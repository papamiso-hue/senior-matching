import streamlit as st
import requests
import logging
import os

logger = logging.getLogger("raon")

# 카카오 REST API 키는 로그인 주소(브라우저 주소창)에 그대로 나타나는 '공개용' 값입니다. 비밀값이 아닙니다.
# (카카오 개발자 콘솔에서 'Client Secret'을 쓰고 있다면 그 값은 코드에 넣지 말고 Streamlit secrets에 두세요.)
KAKAO_REST_API_KEY = "53c242a5a25a23e264cd7e845b124a82"
# 로그인 후 돌아올 주소. Render 환경변수 KAKAO_REDIRECT_URI 가 있으면 그 값을 쓰고, 없으면 예전 주소를 씁니다.
# (새 주소 https://noblesseraon.com 은 카카오 개발자 콘솔 [카카오 로그인 > Redirect URI]에 먼저 등록해야 합니다.)
KAKAO_REDIRECT_URI = os.environ.get("KAKAO_REDIRECT_URI", "https://senior-matching-xtflgt6cnpp6q9o53z79pb.streamlit.app").rstrip("/")

def get_kakao_login_url(state=None):
    url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={KAKAO_REST_API_KEY}&"
        f"redirect_uri={KAKAO_REDIRECT_URI}&"
        f"response_type=code"
    )
    if state:
        url += f"&state={state}"  # 친구 추천 코드를 로그인 후에도 이어받기 위함
    return url

def get_kakao_user_info(auth_code):
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": auth_code,
    }
    headers = {"Content-type": "application/x-www-form-urlencoded;charset=utf-8"}

    try:
        res = requests.post(token_url, data=token_data, headers=headers, timeout=8)
        token_res = res.json()

        access_token = token_res.get("access_token")
        if not access_token:
            # 카카오가 돌려준 오류 원문은 화면에 보이지 않게 하고, 종류만 서버 로그에 남깁니다.
            logger.error("kakao token error: %s", str(token_res.get("error_code") or token_res.get("error") or "unknown")[:40])
            st.error("카카오 로그인에 실패했습니다. 처음 화면에서 다시 시도해 주세요.")
            return None

        user_url = "https://kapi.kakao.com/v2/user/me"
        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        user_res = requests.get(user_url, headers=auth_headers, timeout=8).json()

        kakao_id = user_res.get("id")
        if not kakao_id:
            logger.error("kakao user info missing id")
            st.error("카카오 로그인에 실패했습니다. 처음 화면에서 다시 시도해 주세요.")
            return None
        properties = user_res.get("properties", {})
        nickname = properties.get("nickname", "카카오 회원")
        profile_image = properties.get("profile_image", "")

        return {
            "id": kakao_id,
            "nickname": nickname,
            "profile_image": profile_image
        }
    except Exception as e:
        logger.error("kakao comm error: %s", type(e).__name__)
        st.error("카카오와 통신하는 중 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.")
        return None
