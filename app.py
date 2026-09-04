import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="5060 안심 매칭", page_icon="💍", layout="centered")

# 상단 여백 및 가독성 최적화 스타일
st.markdown("""
    <style>
    .block-container { 
        padding-top: 3.5rem !important; 
        padding-bottom: 3rem !important; 
        max-width: 580px; 
    }
    .main-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.8rem;
        line-height: 1.35;
        letter-spacing: -0.5px;
    }
    .badge-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #F8FAFC;
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border: 1px solid #334155;
    }
    .badge-tag {
        display: inline-block;
        background-color: #E11D48;
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    .badge-text {
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.4;
    }
    .sub-desc {
        font-size: 0.92rem;
        color: #4B5563;
        margin-bottom: 1.3rem;
        line-height: 1.55;
    }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        height: 3rem;
    }
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

# [1. 로그인/가입 화면]
if not st.session_state.user_id:
    # 요청하신 문구 적용
    st.markdown('<div class="main-title">💍 5060 프리미엄 가치관·신용 매칭</div>', unsafe_allow_html=True)
    st.markdown("""
        <div class="badge-box">
            <span class="badge-tag">엄격한 입회 기준</span>
            <div class="badge-text">남성 800점 이상 · 여성 600점 이상 신용 인증 필수</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sub-desc">신용이 검증된 분들만 모시는 고품격 만남. 75가지 가치관 문답으로 깊이가 통하는 인연을 찾습니다.</div>', unsafe_allow_html=True)
    st.divider()

    tab_login, tab_join = st.tabs(["기존 회원 로그인", "신규 회원가입"])

    with tab_login:
        login_name = st.text_input("가입하신 성함", key="login_name")
        if st.button("내 계정 불러오기"):
            res = supabase.table("users").select("*").eq("name", login_name.strip()).execute()
            if res.data:
                st.session_state.user_id = res.data[0]["id"]
                st.session_state.user_info = res.data[0]
                st.rerun()
            else:
                st.error("일치하는 회원 정보를 찾을 수 없습니다.")

    with tab_join:
        with st.form("join_form"):
            name = st.text_input("성명 (실명)")
            gender = st.radio("성별", ["남", "여"], horizontal=True)
            age = st.number_input("나이 (만 나이)", 40, 85, 58)
            region = st.selectbox("활동 희망 지역", ["서울 강남/서초", "서울 강북/도심", "서울 서남/영등포", "경기 분당/판교", "경기 일산", "인천/부천", "기타"])
            credit_score = st.number_input("신용점수 입력 (남성 800+ / 여성 600+)", 0, 1000, 820)
            
            st.markdown("##### 🎯 3대 필수 가치관 문답")
            q1 = st.radio("1. 관계의 최종 형태?", ["법률혼 (서류상 정식 재혼 희망)", "사실혼 (합가 동거하되 서류 정리는 신중)", "LAT 동반자 (각자 주거를 유지하며 여행과 일상 공유)", "상황에 맞추어 유연하게 협의"])
            q38 = st.radio("2. 상대방 흡연 기준?", ["비흡연자만 가능 (전자담배 포함 절대 불가)", "전자담배까지는 양해 가능", "실외 흡연자라면 무관", "본인도 흡연자이므로 흡연 선호"])
            q56 = st.radio("3. 종교 차이 입장?", ["동일 종교 필수 (함께 신앙생활 희망)", "종교가 달라도 강요나 터치가 없다면 무관", "무교 선호", "상대방 종교를 존중하며 맞춰줄 의향 있음"])

            submit_join = st.form_submit_button("신용 검증 및 안심 가입")
            if submit_join:
                cutoff = 800 if gender == "남" else 600
                if credit_score < cutoff:
                    st.error(f"입회 기준 미달: {gender}성은 신용점수 {cutoff}점 이상만 승인됩니다.")
                else:
                    new_u = supabase.table("users").insert({
                        "name": name.strip(), "gender": gender, "age": int(age),
                        "region": region, "credit_score": int(credit_score), "is_verified": True
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

# [2. 메인 대시보드]
else:
    me = st.session_state.user_info
    st.markdown(f"#### 👤 {me['name']} 님 ({me['gender']}·{me['age']}세·{me['region']})")
    st.caption(f"🛡️ 신용 안심 인증 통과 ({me['credit_score']}점)")

    tab_feed, tab_survey, tab_inbox = st.tabs(["💖 추천 피드", "📝 가치관 문답 이어하기", "📬 매칭 보관함"])

    all_questions_raw = supabase.table("question_master").select("question_num, question_text, category, options").execute().data
    q_map = {q["question_num"]: q for q in all_questions_raw}

    my_ans_data = supabase.table("user_answers").select("question_num, answer_value").eq("user_id", me["id"]).execute().data
    my_answers = {item["question_num"]: item["answer_value"] for item in my_ans_data}

    # --- 탭 1: 이성 추천 피드 & 가치관 대조표 ---
    with tab_feed:
        st.markdown("##### 🌟 가치관 일치율 순 추천 리스트")
        target_gender = "여" if me["gender"] == "남" else "남"
        candidates = supabase.table("users").select("*").eq("gender", target_gender).execute().data

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
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{cand['name']}** ({cand['age']}세 / {cand['region']})")
                        st.caption(f"🛡️ 신용 안심 인증 ({cand['credit_score']}점)")
                    with col2:
                        st.metric("일치율", f"{score}%")

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
                        st.button(f"⏳ 대화 수락 대기 중 ({cand['name']})", key=f"btn_{cand['id']}", disabled=True)
                    elif req_status == "ACCEPTED":
                        st.success(f"🎉 대화가 성사되었습니다! (연락처 교환 가능)")
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
    with tab_survey:
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
    with tab_inbox:
        st.markdown("##### 📬 매칭 신청 현황")
        inbox_tab1, inbox_tab2 = st.tabs(["내가 보낸 신청", "나에게 온 신청"])

        with inbox_tab1:
            sent_list = supabase.table("match_requests").select("id, receiver_id, status, created_at").eq("sender_id", me["id"]).execute().data
            if not sent_list:
                st.caption("아직 보낸 대화 신청이 없습니다.")
            else:
                for req in sent_list:
                    rcv_user = supabase.table("users").select("name, age, region").eq("id", req["receiver_id"]).execute().data
                    rcv_name = rcv_user[0]["name"] if rcv_user else "회원"
                    st.write(f"• **{rcv_name}** 님에게 보낸 신청 | 상태: `{req['status']}`")

        with inbox_tab2:
            received_list = supabase.table("match_requests").select("id, sender_id, status, created_at").eq("receiver_id", me["id"]).execute().data
            if not received_list:
                st.caption("도착한 대화 신청이 없습니다.")
            else:
                for req in received_list:
                    snd_user = supabase.table("users").select("name, age, region, credit_score").eq("id", req["sender_id"]).execute().data
                    if snd_user:
                        u = snd_user[0]
                        st.markdown(f"**{u['name']}** ({u['age']}세 / {u['region']} / 신용 {u['credit_score']}점)")
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

    st.markdown("---")
    if st.button("로그아웃"):
        st.session_state.user_id = None
        st.session_state.user_info = None
        st.rerun()
