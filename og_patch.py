"""카카오톡 등 공유 미리보기용 메타 태그를 Streamlit 기본 index.html에 넣습니다. (실패해도 서비스에는 영향 없음)"""
import os

OG = """<title>노블레스 라온 - 5060 동반자·친구 만남</title>
<meta name="description" content="가입 무료 · 카카오 로그인으로 2분 만에 시작하는 5060 동반자·친구 만남">
<meta property="og:type" content="website">
<meta property="og:site_name" content="노블레스 라온">
<meta property="og:title" content="노블레스 라온 - 5060 동반자·친구 만남">
<meta property="og:description" content="가입 무료 · 카카오 로그인으로 2분 만에 시작하는 5060 동반자·친구 만남">
<meta property="og:image" content="https://noblesseraon.com/app/static/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="https://noblesseraon.com/">
"""

def patch():
    try:
        import streamlit, re
        p = os.path.join(os.path.dirname(streamlit.__file__), "static", "index.html")
        h = open(p, encoding="utf-8").read()
        if "og:image" in h:
            return
        h = re.sub(r"<title>.*?</title>", "", h, flags=re.S)
        h = h.replace("<head>", "<head>\n" + OG, 1)
        open(p, "w", encoding="utf-8").write(h)
    except Exception:
        pass

if __name__ == "__main__":
    patch()
