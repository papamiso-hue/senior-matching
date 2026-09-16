import streamlit as st
import requests

KAKAO_REST_API_KEY = "53c242a5a25a23e264cd7e845b124a82"
KAKAO_REDIRECT_URI = "https://senior-matching-xtflgt6cnpp6q9o53z79pb.streamlit.app"

def get_kakao_login_url():
    return (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={KAKAO_REST_API_KEY}&"
        f"redirect_uri={KAKAO_REDIRECT_URI}&"
        f"response_type=code"
    )

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
        res = requests.post(token_url, data=token_data, headers=headers)
        token_res = res.json()
        
        access_token = token_res.get("access_token")
        if not access_token:
            st.error(f"🚨 토큰 발급 에러 응답: {token_res}")
            return None

        user_url = "https://kapi.kakao.com/v2/user/me"
        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        user_res = requests.get(user_url, headers=auth_headers).json()
        
        kakao_id = user_res.get("id")
        properties = user_res.get("properties", {})
        nickname = properties.get("nickname", "카카오 회원")
        profile_image = properties.get("profile_image", "")

        return {
            "id": kakao_id,
            "nickname": nickname,
            "profile_image": profile_image
        }
    except Exception as e:
        st.error(f"🚨 카카오 통신 예외 발생: {e}")
        return None
