import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
from streamlit_gsheets import GSheetsConnection
import bcrypt
import extra_streamlit_components as stx
from dotenv import load_dotenv

# [중요] 방금 만든 파일에서 함수 불러오기
from news_dashboard import render_news_section

load_dotenv()

# --- 앱 설정 --- #
st.set_page_config(page_title="증시 핵심 요약", layout="wide")

# --- CSS 스타일 (전역 적용) --- #
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF !important; color: #111827 !important; }
    [data-testid="stSidebar"] { background-color: #E3F2FD !important; }
    [data-testid="stSidebar"] .stMarkdown p { color: #0D47A1 !important; font-weight: bold; }

    /* 뉴스 카드 스타일 */
    .news-card {
        background-color: #FFFFFF; padding: 20px; border-radius: 12px;
        margin-bottom: 15px; border: 1px solid #E5E7EB; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .news-card h3 { color: #111827 !important; }
    .news-card p { color: #6B7280 !important; }

    /* AI 결과창 스타일 */
    .ai-result {
        background-color: #F0F7FF; color: #1E3A8A !important; padding: 20px;
        border-radius: 10px; border: 1px solid #3B82F6; line-height: 1.7;
    }

    /* 버튼 스타일 */
    div.stButton > button:first-child { background-color: #3B82F6; color: white !important; border: none; }
    div.stButton > button[key^="ai_"] { background-color: #10B981 !important; color: white !important; border: none; }
</style>
""", unsafe_allow_html=True)

# --- 쿠키 매니저 초기화 --- #
def get_manager():
    return stx.CookieManager(key="main_cookie_handler")

cookie_manager = get_manager()

# --- 데이터 연결 --- #
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def load_user_data():
    try:
        return conn.read(worksheet="Users", ttl=0)
    except:
        return pd.DataFrame(columns=['username', 'hashed_password', 'openai_api_key', 'gemini_api_key', 'created_at'])

# --- 세션 초기화 --- #
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'username': None,
        'user_keys': {'GEMINI': None, 'OPENAI': None}
    })

# ---------------------------------------------------------
# [수정 핵심] 배포 환경용 쿠키 재시도 로직
# ---------------------------------------------------------
def get_auth_cookie(manager):
    """배포 환경의 지연을 극복하기 위해 최대 5번까지 쿠키 확인"""
    for i in range(5):
        try:
            val = manager.get('auth_user')
            if val:
                return val
        except:
            pass
        time.sleep(0.5)  # 0.5초 대기 후 다시 시도
    return None

# 자동 로그인 로직 (세션이 로그아웃 상태일 때만 실행)
if not st.session_state.logged_in:
    saved_user = get_auth_cookie(cookie_manager)

    if saved_user:
        df = load_user_data()
        user_data = df[df['username'] == saved_user]
        if not user_data.empty:
            user = user_data.iloc[0]
            st.session_state.update({
                'logged_in': True,
                'username': saved_user,
                'user_keys': {'GEMINI': user.get('gemini_api_key'), 'OPENAI': user.get('openai_api_key')}
            })
            st.rerun()

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
                            # 세션 업데이트
                            st.session_state.update({
                                'logged_in': True, 'username': uid,
                                'user_keys': {'GEMINI': user.get('gemini_api_key'), 'OPENAI': user.get('openai_api_key')}
                            })
                            # 쿠키 저장
                            cookie_manager.set('auth_user', uid, expires_at=datetime.now() + timedelta(minutes=30))
                            st.success("로그인 성공!")
                            time.sleep(0.5)
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
                    if nid in df['username'].values: st.error("중복 아이디 입니다.")
                    else:
                        hashed = bcrypt.hashpw(npw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        new_row = pd.DataFrame([{
                            "username": nid, "hashed_password": hashed,
                            "gemini_api_key": nge, "openai_api_key": noa,
                            "created_at": datetime.now().isoformat()
                        }])
                        conn.update(worksheet="Users", data=pd.concat([df, new_row], ignore_index=True))
                        st.success("가입 완료!")
    else:
        st.success(f"반가워요, {st.session_state.username}님!")
        if st.button("로그아웃"):
            cookie_manager.delete('auth_user')
            st.session_state.update({'logged_in': False, 'username': None, 'user_keys': {'GEMINI': None, 'OPENAI': None}})
            time.sleep(0.5)
            st.rerun()

# --- 메인 화면 호출 --- #
render_news_section()