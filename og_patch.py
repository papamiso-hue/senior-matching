"""Streamlit 기본 index.html 머리말(head)에 (1) 카카오톡 공유 미리보기 태그, (2) 홈 화면 설치(PWA) 태그를 넣습니다.
이미 들어 있으면 다시 넣지 않습니다. 실패해도 서비스에는 영향 없습니다."""
import os
import re

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

# 홈 화면 설치(PWA): 설치 정보 파일 연결 + '설치 가능' 신호를 잡아 두는 작은 스크립트(개인정보 수집 없음)
PWA_MARK = "pwa-install-v1"
PWA = """<!-- pwa-install-v1 -->
<link rel="manifest" href="/app/static/manifest.json">
<meta name="theme-color" content="#14213D">
<meta name="application-name" content="노블레스 라온">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="노블레스 라온">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/app/static/apple-touch-icon.png">
<script>
window.addEventListener('beforeinstallprompt', function (e) {
  e.preventDefault();
  window.__pwaPrompt = e;
  try { window.dispatchEvent(new Event('pwaready')); } catch (_) {}
});
window.addEventListener('appinstalled', function () {
  window.__pwaPrompt = null;
  window.__pwaInstalled = true;
  try { window.dispatchEvent(new Event('pwainstalled')); } catch (_) {}
});
</script>
"""


def patch(path=None):
    try:
        if path is None:
            import streamlit
            path = os.path.join(os.path.dirname(streamlit.__file__), "static", "index.html")
        h = open(path, encoding="utf-8").read()
        changed = False
        if "og:image" not in h:
            h = re.sub(r"<title>.*?</title>", "", h, flags=re.S)
            h = h.replace("<head>", "<head>\n" + OG, 1)
            changed = True
        if PWA_MARK not in h:
            h = h.replace("<head>", "<head>\n" + PWA, 1)
            changed = True
        if changed:
            open(path, "w", encoding="utf-8").write(h)
    except Exception:
        pass


if __name__ == "__main__":
    patch()
