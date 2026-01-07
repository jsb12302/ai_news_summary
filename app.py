import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from rss_collector import fetch_rss_feeds
from streamlit_gsheets import GSheetsConnection
import bcrypt
from google import genai  # 최신 SDK: google-genai 패키지 필요

# .env 로드
load_dotenv()

# --- 앱 설정 --- #
st.set_page_config(page_title="증시 핵심 요약", layout="wide")

# CSS 스타일 (금융 대시보드 느낌)
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .news-card {
        background-color: #1E2129; padding: 20px; border-radius: 10px;
        margin-bottom: 20px; border-left: 5px solid #00BFFF;
    }
    .ai-result {
        background-color: #2D3748; padding: 15px; border-radius: 8px; 
        margin-top: 10px; border: 1px solid #4A5568; line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 구글 시트 연결 --- #
conn = st.connection("gsheets", type=GSheetsConnection)

# --- [최신 SDK 방식] Gemini 요약 함수 --- #
def analyze_news_gemini(api_key, title, summary):
    try:
        # 1. 클라이언트 생성 (보내주신 예시 방식)
        client = genai.Client(api_key=api_key.strip())
        
        prompt = f"""
        당신은 주식 투자 전문가입니다. 다음 뉴스를 분석하여 투자자를 위한 인사이트를 마크다운 형식으로 제공하세요.
        제목: {title}
        내용: {summary}
        
        결과에 포함할 내용:
        1. 🔑 핵심 요약 (3줄)
        2. 📊 시장 영향 (호재/악재 평가)
        3. 💡 투자 포인트
        """
        
        # 2. 콘텐츠 생성 (보내주신 예시 구조 적용)
        response = client.models.generate_content(
            model="gemini-3-flash-preview", # preview 모델보다 안정적인 flash 권장
            contents=prompt,
        )
        
        return response.text

    except Exception as e:
        return f"⚠️ 분석 중 오류 발생: {str(e)}"

# --- 데이터 로드 및 세션 관리 --- #
@st.cache_data(ttl=2)
def load_user_data():
    try:
        return conn.read(worksheet="Users")
    except:
        return pd.DataFrame(columns=['username', 'hashed_password', 'openai_api_key', 'gemini_api_key', 'created_at'])

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'username': None, 'user_keys': {'OPENAI': None, 'GEMINI': None}})

# --- 사이드바: 로그인/회원가입 --- #
with st.sidebar:
    st.title("👤 멤버십")
    if not st.session_state.logged_in:
        menu = st.radio("메뉴", ["로그인", "회원가입"])
        
        if menu == "로그인":
            with st.form("login"):
                uid = st.text_input("아이디")
                upw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인"):
                    df = load_user_data()
                    if uid in df['username'].values:
                        user = df[df['username'] == uid].iloc[0]
                        if bcrypt.checkpw(upw.encode('utf-8'), str(user['hashed_password']).encode('utf-8')):
                            st.session_state.update({
                                'logged_in': True, 'username': uid,
                                'user_keys': {'OPENAI': user.get('openai_api_key'), 'GEMINI': user.get('gemini_api_key')}
                            })
                            st.rerun()
                        else: st.error("비밀번호 불일치")
                    else: st.error("존재하지 않는 아이디")
        else:
            with st.form("signup"):
                nid = st.text_input("아이디")
                npw = st.text_input("비밀번호", type="password")
                nge = st.text_input("Gemini API Key")
                if st.form_submit_button("가입 완료"):
                    df = load_user_data()
                    if nid in df['username'].values: st.error("이미 있는 아이디")
                    else:
                        hashed = bcrypt.hashpw(npw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        new_data = pd.DataFrame([{"username": nid, "hashed_password": hashed, "gemini_api_key": nge, "created_at": datetime.now().isoformat()}])
                        conn.update(worksheet="Users", data=pd.concat([df, new_data], ignore_index=True))
                        st.success("가입 성공! 로그인 해주세요.")
    else:
        st.success(f"✅ {st.session_state.username}님")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()

# --- 메인 뉴스 화면 --- #
st.title("📈 오늘의 증시 핵심 요약")
rss_urls = ["https://www.mk.co.kr/rss/30100001/", "https://www.hankyung.com/feed/economy"]

if st.button("🔄 뉴스 새로고침"):
    st.cache_data.clear()
    st.rerun()

news_df = fetch_rss_feeds(rss_urls)

if not news_df.empty:
    for idx, row in news_df.head(10).iterrows():
        with st.container():
            st.markdown(f"""
            <div class="news-card">
                <h3>{row['title']}</h3>
                <p style="color:gray;">{row['published']} | <a href="{row['link']}" target="_blank">기사 원문</a></p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🤖 AI 요약 분석", key=f"ai_{idx}"):
                if st.session_state.logged_in:
                    user_gemini_key = st.session_state.user_keys.get('GEMINI')
                    if user_gemini_key:
                        with st.spinner("최신 Gemini SDK 분석 중..."):
                            result = analyze_news_gemini(user_gemini_key, row['title'], row['summary'])
                            st.markdown(f'<div class="ai-result">{result}</div>', unsafe_allow_html=True)
                    else:
                        st.error("등록된 Gemini API 키가 없습니다.")
                else:
                    st.warning("로그인 후 이용 가능합니다.")