import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import secrets  # 보안 토큰 생성용
from streamlit_gsheets import GSheetsConnection
import bcrypt
from dotenv import load_dotenv

# [중요] 방금 만든 파일에서 함수 불러오기
from news_dashboard import render_news_section

load_dotenv()

# --- 앱 설정 --- #
st.set_page_config(page_title="증시 핵심 요약", layout="wide")

# --- CSS 스타일 (전역 적용) --- #
st.markdown("""
<style>
    /* 1. 상단 헤더 영역 투명화 및 높이 조정 */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 2. Deploy 버튼 및 관련 컨테이너 완전 삭제 (mypage 포함 전역) */
    .stAppDeployButton,
    div[data-testid="stAppDeployButton"],
    button[kind="header"] {
        display: none !important;
    }

    /* 3. 메인 메뉴(점 세개) 및 관련 컨테이너 완전 삭제 */
    #MainMenu,
    [data-testid="stMainMenu"],
    .st-emotion-cache-czk5ss {
        display: none !important;
    }

    /* 4. 하단 푸터 삭제 */
    footer {
        display: none !important;
    }

    /* 5. 사이드바 열기/닫기 버튼(왼쪽)만 살리기 */
    /* 위에서 버튼을 지웠으므로 왼쪽 버튼은 명시적으로 보이게 설정 */
    [data-testid="stHeader"] button[data-testid="stBaseButton-headerNoPadding"] {
        display: inline-flex !important;
    }

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

# --- 데이터 연결 --- #
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def load_user_data():
    try:
        return conn.read(worksheet="Users", ttl=0)
    except:
        return pd.DataFrame(columns=['username', 'hashed_password', 'openai_api_key', 'gemini_api_key', 'session_token', 'created_at'])

# --- 세션 초기화 --- #
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'username': None,
        'user_keys': {'GEMINI': None, 'OPENAI': None}
    })

# ---------------------------------------------------------
# [수정 핵심] URL 파라미터를 이용한 자동 로그인 로직
# ---------------------------------------------------------
# 주소창에 ?token=... 이 있는지 확인
query_params = st.query_params
url_token = query_params.get("token")

if url_token and not st.session_state.logged_in:
    df = load_user_data()
    # 시트에서 해당 토큰을 가진 유저 검색
    user_match = df[df['session_token'] == url_token]

    if not user_match.empty:
        user = user_match.iloc[0]
        st.session_state.update({
            'logged_in': True,
            'username': user['username'],
            'user_keys': {'GEMINI': user.get('gemini_api_key'), 'OPENAI': user.get('openai_api_key')}
        })
        # 자동 로그인 성공 후 화면 유지

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
                            # 1. 고유 세션 토큰 생성 (보안 강화)
                            new_token = secrets.token_urlsafe(32)

                            # 2. [DB 업데이트] 토큰과 마지막 로그인 시간 저장
                            df.loc[df['username'] == uid, 'session_token'] = new_token
                            df.loc[df['username'] == uid, 'last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            conn.update(worksheet="Users", data=df)

                            # 3. 세션 업데이트
                            st.session_state.update({
                                'logged_in': True, 'username': uid,
                                'user_keys': {'GEMINI': user.get('gemini_api_key'), 'OPENAI': user.get('openai_api_key')}
                            })

                            # 4. 주소창에 토큰 심기 및 강제 새로고침
                            st.query_params.token = new_token
                            st.success("로그인 성공!")
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
                            "username": nid,
                            "hashed_password": hashed,
                            "gemini_api_key": nge,
                            "openai_api_key": noa,
                            "session_token": "", # 초기 토큰은 비어있음
                            "created_at": datetime.now().isoformat()
                        }])
                        conn.update(worksheet="Users", data=pd.concat([df, new_row], ignore_index=True))
                        st.success("가입 완료!")
    else:
        st.success(f"반가워요, {st.session_state.username}님!")
        if st.button("로그아웃"):
            # 로그아웃 시 시트의 토큰 무효화 (보안)
            df = load_user_data()
            df.loc[df['username'] == st.session_state.username, 'session_token'] = ""
            conn.update(worksheet="Users", data=df)

            # 세션 및 URL 파라미터 초기화
            st.session_state.update({'logged_in': False, 'username': None, 'user_keys': {'GEMINI': None, 'OPENAI': None}})
            st.query_params.clear()
            st.rerun()

# --- 메인 화면 호출 --- #
render_news_section()