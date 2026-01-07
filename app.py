import streamlit as st
import pandas as pd
from datetime import datetime
from rss_collector import fetch_rss_feeds
from streamlit_gsheets import GSheetsConnection
import bcrypt
from google import genai
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# --- 앱 설정 --- #
st.set_page_config(page_title="증시 핵심 요약", layout="wide")

# --- CSS 스타일 (메인 테마) --- #
st.markdown("""
<style>
    /* 전체 배경 흰색 */
    .stApp { 
        background-color: #FFFFFF !important; 
        color: #111827 !important; 
    }
    
    /* 사이드바 스타일 유지 */
    [data-testid="stSidebar"] { background-color: #E3F2FD !important; }
    [data-testid="stSidebar"] .stMarkdown p { color: #0D47A1 !important; font-weight: bold; }

    /* 뉴스 카드 (흰색 배경 + 연한 테두리) */
    .news-card { 
        background-color: #FFFFFF; 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .news-card h3 { color: #111827 !important; }
    .news-card p { color: #6B7280 !important; }

    /* AI 결과창 (연한 파랑 배경) */
    .ai-result { 
        background-color: #F0F7FF; 
        color: #1E3A8A !important; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #3B82F6; 
        line-height: 1.7;
    }

    /* 버튼 스타일 */
    div.stButton > button:first-child { background-color: #3B82F6; color: white !important; border: none; }
    div.stButton > button[key^="ai_"] { background-color: #10B981 !important; color: white !important; border: none; }
</style>
""", unsafe_allow_html=True)

# --- 데이터 로드 및 시트 연결 --- #
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def load_user_data():
    try:
        return conn.read(worksheet="Users")
    except:
        return pd.DataFrame(columns=['username', 'hashed_password', 'openai_api_key', 'gemini_api_key', 'created_at'])

# --- 세션 로직 (쿠키 로직 제거) --- #
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 
        'username': None, 
        'user_keys': {'GEMINI': None, 'OPENAI': None}
    })

# --- Gemini 요약 함수 --- #
def analyze_news_gemini(api_key, title, summary):
    try:
        client = genai.Client(api_key=api_key.strip())
        prompt = f"투자 전문가로서 뉴스 분석: {title}\n내용: {summary}. 핵심요약, 시장영향, 투자포인트 작성."
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 분석 실패: {str(e)}"

# --- 사이드바 (로그인/회원가입) --- #
with st.sidebar:
    st.title("👤 멤버십")
    if not st.session_state.logged_in:
        menu = st.radio("메뉴 선택", ["로그인", "회원가입"])
        if menu == "로그인":
            with st.form("login"):
                uid = st.text_input("아이디")
                upw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인"):
                    df = load_user_data()
                    if uid in df['username'].values:
                        user = df[df['username'] == uid].iloc[0]
                        if bcrypt.checkpw(upw.encode('utf-8'), str(user['hashed_password']).encode('utf-8')):
                            # 세션 데이터만 업데이트
                            st.session_state.update({
                                'logged_in': True, 
                                'username': uid, 
                                'user_keys': {'GEMINI': user.get('gemini_api_key'), 'OPENAI': user.get('openai_api_key')}
                            })
                            st.rerun()
                        else: st.error("비밀번호 불일치")
                    else: st.error("아이디 없음")
        else:
            with st.form("signup"):
                nid = st.text_input("아이디")
                npw = st.text_input("비밀번호", type="password")
                nge = st.text_input("Gemini API Key")
                noa = st.text_input("GPT API Key (선택)")
                if st.form_submit_button("가입하기"):
                    df = load_user_data()
                    if nid in df['username'].values: st.error("중복 아이디")
                    else:
                        hashed = bcrypt.hashpw(npw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        new_row = pd.DataFrame([{
                            "username": nid, 
                            "hashed_password": hashed, 
                            "gemini_api_key": nge, 
                            "openai_api_key": noa, 
                            "created_at": datetime.now().isoformat()
                        }])
                        conn.update(worksheet="Users", data=pd.concat([df, new_row], ignore_index=True))
                        st.success("가입 완료!")
    else:
        st.success(f"반가워요, {st.session_state.username}님!")
        st.info("👈 사이드바 위의 메뉴에서 정보를 수정하세요.")
        if st.button("로그아웃"):
            # 세션 정보 초기화 후 리런
            st.session_state.update({'logged_in': False, 'username': None, 'user_keys': {'GEMINI': None, 'OPENAI': None}})
            st.rerun()

# --- 메인 뉴스 화면 --- #
st.title("📈 오늘의 증시 핵심 요약")

if st.button("🔄 뉴스 새로고침"):
    st.cache_data.clear()
    st.rerun()

news_df = fetch_rss_feeds(["https://www.mk.co.kr/rss/30100001/", "https://www.hankyung.com/feed/economy"])

if not news_df.empty:
    for idx, row in news_df.head(10).iterrows():
        with st.container():
            st.markdown(f'<div class="news-card"><h3>{row["title"]}</h3><p style="color:#6B7280;">{row["published"]} | <a href="{row["link"]}" target="_blank" style="color:#3B82F6;">기사 원문</a></p></div>', unsafe_allow_html=True)
            if st.button(f"🤖 AI 분석 실행", key=f"ai_{idx}"):
                if st.session_state.logged_in:
                    if st.session_state.user_keys['GEMINI']:
                        with st.spinner("AI 분석 중..."):
                            res = analyze_news_gemini(st.session_state.user_keys['GEMINI'], row['title'], row['summary'])
                            st.markdown(f'<div class="ai-result">{res}</div>', unsafe_allow_html=True)
                    else: st.error("API 키를 등록해주세요.")
                else: st.warning("로그인이 필요합니다.")