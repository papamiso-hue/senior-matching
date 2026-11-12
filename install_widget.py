"""홈 화면 설치 버튼 (PWA). 아이콘 같은 큰 버튼 하나만 누르면 설치 창이 뜹니다.
- 안드로이드 크롬: '설치 가능' 신호가 잡히면 바로 설치 창을 띄웁니다.
- 신호가 아직 없거나 아이폰: 같은 자리에서 '홈 화면에 추가' 순서를 크게 보여 줍니다.
- 카카오톡 안: 설치가 안 되므로 '다른 브라우저로 열기' 버튼을 보여 줍니다.
- 이미 설치된 앱 화면에서는 아무것도 보이지 않습니다.
개인정보는 수집·저장하지 않습니다."""
import streamlit.components.v1 as components

_HTML = """
<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html,body{margin:0;padding:0;background:transparent;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;}
  #wrap{padding:2px 0 6px 0;}
  #btn{width:100%;min-height:104px;border:0;border-radius:16px;cursor:pointer;
       background:linear-gradient(135deg,#F7C948,#E8A317);color:#2B1B00;
       font-size:26px;font-weight:900;letter-spacing:-0.3px;
       box-shadow:0 3px 10px rgba(122,74,0,.28);display:flex;align-items:center;justify-content:center;gap:10px;}
  #btn:active{transform:scale(.99);}
  #icon{width:50px;height:50px;border-radius:9px;flex:0 0 50px;}
  #sub{margin:8px 2px 0 2px;font-size:18px;line-height:1.5;color:#5C4A1E;text-align:center;}
  #done{display:none;margin-top:8px;padding:12px 14px;border-radius:12px;background:#E7F6EC;color:#14532D;font-size:21px;font-weight:700;text-align:center;line-height:1.5;}
</style></head>
<body>
<div id="wrap">
  <button id="btn" type="button"><img id="icon" alt="" src="/app/static/icon-192.png"><span id="label">앱 설치하기</span></button>
  <div id="sub"></div>
  <div id="done"></div>
</div>
<script>
(function () {
  var P = null;
  try { P = window.parent; void P.document; } catch (e) { P = null; }
  var ua = navigator.userAgent || "";
  var isKakao = /KAKAOTALK/i.test(ua);
  var isIOS = /iPhone|iPad|iPod/i.test(ua) || (/Macintosh/i.test(ua) && (navigator.maxTouchPoints || 0) > 1);
  var $ = function (id) { return document.getElementById(id); };
  var btn = $("btn"), label = $("label"), sub = $("sub"), done = $("done");
  var mode = "";

  function resize() { /* 칸 높이는 고정입니다. 안내는 팝업으로 띄웁니다. */ }
  function hideAll() {
    try { window.frameElement.style.display = "none"; } catch (e) {}
    document.body.style.display = "none";
  }
  function isStandalone() {
    try {
      var W = P || window;
      return W.matchMedia("(display-mode: standalone)").matches || W.navigator.standalone === true || !!(P && P.__pwaInstalled);
    } catch (e) { return false; }
  }
  function openExternal() {
    // 카카오톡 안에서 현재 주소를 기본 브라우저(크롬/사파리)로 엽니다.
    var url = "https://noblesseraon.com/";
    try { if (P && P.location && P.location.href) url = P.location.href; } catch (e) {}
    var target = "kakaotalk://web/openExternal?url=" + encodeURIComponent(url);
    try {
      var d = (P && P.document) || document;
      var a = d.createElement("a");
      a.href = target; a.style.display = "none";
      d.body.appendChild(a); a.click(); d.body.removeChild(a);
    } catch (e) { window.location.href = target; }
  }
  function showSteps(html) {
    // 화면 위에 뜨는 안내 창 (아래 내용과 겹치지 않고, 닫기 버튼으로 닫습니다)
    try {
      var d = (P && P.document) || document;
      var old = d.getElementById("pwa-help-overlay");
      if (old) old.remove();
      var ov = d.createElement("div");
      ov.id = "pwa-help-overlay";
      ov.setAttribute("style", "position:fixed;left:0;top:0;right:0;bottom:0;z-index:2147483000;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box;");
      var card = d.createElement("div");
      card.setAttribute("style", "background:#FFF9E8;border:3px solid #D9C48F;border-radius:18px;max-width:460px;width:100%;max-height:86vh;overflow:auto;padding:20px 20px 16px;box-sizing:border-box;color:#2B2B2B;font-size:18px;line-height:1.75;font-family:-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR',sans-serif;");
      card.innerHTML = "<div style='font-size:21px;font-weight:900;color:#7A4A00;margin-bottom:6px;'>👑 홈 화면에 앱 아이콘 만들기</div>" + html +
        "<button id='pwa-help-close' type='button' style='margin-top:14px;width:100%;min-height:52px;border:0;border-radius:14px;background:#7A4A00;color:#fff;font-size:19px;font-weight:800;cursor:pointer;'>닫기</button>";
      ov.appendChild(card);
      d.body.appendChild(ov);
      var close = function () { var o = d.getElementById("pwa-help-overlay"); if (o) o.remove(); };
      d.getElementById("pwa-help-close").addEventListener("click", close);
      ov.addEventListener("click", function (e) { if (e.target === ov) close(); });
    } catch (e) {}
  }

  var isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(ua) || isIOS;
  var ANDROID_STEPS = "<b>크롬에서 이렇게 하세요 (약 10초)</b><ol style='margin:6px 0 0;padding-left:22px;'>" +
    "<li>화면 <b>오른쪽 위 점 세 개 ⋮</b> 를 누릅니다.</li>" +
    "<li><b>'홈 화면에 추가'</b> 또는 <b>'앱 설치'</b> 를 누릅니다.</li>" +
    "<li>이름이 <b>노블레스 라온</b> 인지 보고 <b>'추가'</b> 를 누릅니다.</li>" +
    "<li>폰 홈 화면의 <b>👑 아이콘</b> 을 누르시면 됩니다.</li></ol>";
  var PC_STEPS = "<b>컴퓨터 크롬·엣지에서 이렇게 하세요</b><ol style='margin:6px 0 0;padding-left:22px;'>" +
    "<li>주소창 <b>오른쪽 끝</b>의 <b>설치 아이콘(⊕ 또는 모니터 모양)</b> 을 누릅니다.</li>" +
    "<li>안 보이면 오른쪽 위 <b>점 세 개 ⋮</b> → <b>'노블레스 라온 설치'</b>(또는 '앱 설치')를 누릅니다.</li>" +
    "<li><b>'설치'</b> 를 누르면 바탕화면에 아이콘이 생깁니다.</li></ol>" +
    "<div style='margin-top:6px;font-size:15px;color:#6B5A2A;'>※ 휴대폰에서 설치하시는 것을 권합니다.</div>";
  var IOS_STEPS = "<b>사파리에서 이렇게 하세요 (약 10초)</b><ol style='margin:6px 0 0;padding-left:22px;'>" +
    "<li>화면 <b>맨 아래(또는 위) 공유 버튼 ⬆️</b> 을 누릅니다.</li>" +
    "<li>메뉴를 위로 밀어 <b>'홈 화면에 추가'</b> 를 누릅니다.</li>" +
    "<li>오른쪽 위 <b>'추가'</b> 를 누릅니다.</li>" +
    "<li>폰 홈 화면의 <b>👑 아이콘</b> 을 누르시면 됩니다.</li></ol>" +
    "<div style='margin-top:6px;font-size:15px;color:#6B5A2A;'>※ 아이폰은 크롬이 아니라 <b>사파리</b>에서 열어야 합니다.</div>";

  function setMode() {
    if (isKakao) {
      mode = "kakao";
      label.textContent = "다른 브라우저로 열기";
      sub.textContent = "지금은 카카오톡 안이라 설치할 수 없어요. 버튼을 누르면 크롬(사파리)에서 열립니다.";
    } else if (!isIOS && P && P.__pwaPrompt) {
      mode = "install";
      label.textContent = "앱 설치하기 (홈 화면에 추가)";
      sub.textContent = "버튼 한 번이면 폰 홈 화면에 👑 아이콘이 생겨요. 비용은 없습니다.";
    } else {
      mode = "howto";
      label.textContent = "홈 화면에 앱 아이콘 만들기";
      sub.textContent = "누르시면 따라 하기 쉬운 순서가 화면에 나옵니다. 비용은 없습니다.";
    }
    resize();
  }

  btn.addEventListener("click", function () {
    if (mode === "kakao") { openExternal(); return; }
    if (mode === "install" && P && P.__pwaPrompt) {
      var ev = P.__pwaPrompt;
      P.__pwaPrompt = null;
      try {
        ev.prompt();
        ev.userChoice.then(function (r) {
          if (r && r.outcome === "accepted") {
            btn.style.display = "none"; sub.style.display = "none";
            done.textContent = "✅ 설치 중입니다. 잠시 뒤 폰 홈 화면의 👑 아이콘을 눌러 주세요.";
            done.style.display = "block";
          } else {
            sub.textContent = "괜찮아요. 필요하실 때 다시 눌러 주세요.";
            mode = "howto"; label.textContent = "홈 화면에 앱 아이콘 만들기";
          }
          resize();
        });
      } catch (e) { mode = "howto"; showSteps(isIOS ? IOS_STEPS : (isMobile ? ANDROID_STEPS : PC_STEPS)); }
      return;
    }
    // howto
    showSteps(isIOS ? IOS_STEPS : (isMobile ? ANDROID_STEPS : PC_STEPS));
  });

  if (isStandalone()) { hideAll(); return; }
  setMode();
  if (P) {
    P.addEventListener("pwaready", function () { if (mode === "howto") setMode(); });
    P.addEventListener("pwainstalled", function () {
      btn.style.display = "none"; sub.style.display = "none";
      done.textContent = "✅ 설치되었습니다. 폰 홈 화면의 👑 아이콘을 눌러 주세요.";
      done.style.display = "block"; resize();
    });
  }
  setTimeout(function () { if (mode === "howto") setMode(); }, 1500);
  window.addEventListener("load", resize);
})();
</script>
</body></html>
"""


def render_install_button():
    """큰 설치 버튼 한 줄을 화면에 그립니다. 실패해도 서비스에는 영향이 없습니다."""
    try:
        components.html(_HTML, height=166)
    except Exception:
        pass
