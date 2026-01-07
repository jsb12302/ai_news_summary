import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import bcrypt

# --- 페이지 설정 ---
st.set_page_config(page_title="마이페이지", layout="wide")

# --- CSS 스타일 (바깥쪽 테두리 완전 제거 및 라이트 모드 최적화) ---
st.markdown("""
<style>
    /* 1. 전체 앱 배경 흰색 */
    .stApp { 
        background-color: #FFFFFF !important; 
        color: #111827 !important;
    }

    /* 2. 가장 바깥쪽 파란색 테두리 및 기본 컨테이너 선 제거 */
    [data-testid="stVerticalBlock"] > div {
        border: none !important;
        box-shadow: none !important;
    }
    
    /* 3. 사이드바 스타일 유지 (하늘색 배경) */
    [data-testid="stSidebar"] { 
        background-color: #E3F2FD !important; 
    }
    [data-testid="stSidebar"] .stMarkdown p { 
        color: #0D47A1 !important; 
        font-weight: bold; 
    }

    /* 4. Gemini 전용 섹션 (파란색 박스 강조) */
    div[data-testid="stVerticalBlock"]:has(div.gemini-container-marker) {
        background-color: #F0F7FF !important; 
        border-radius: 15px !important;
        padding: 30px !important;
        margin-bottom: 30px !important;
        border: 2px solid #3B82F6 !important; /* 안쪽 박스 테두리만 유지 */
    }
    
    /* 5. 텍스트 가독성 설정 */
    h1, h3 { color: #111827 !important; }
    p, span, b { color: #374151 !important; }
    
    /* 파란 박스 내부 텍스트는 좀 더 진한 파란색으로 */
    div[data-testid="stVerticalBlock"]:has(div.gemini-container-marker) h3,
    div[data-testid="stVerticalBlock"]:has(div.gemini-container-marker) p,
    div[data-testid="stVerticalBlock"]:has(div.gemini-container-marker) b {
        color: #1E3A8A !important;
    }

    /* 6. 입력창 디자인 */
    input[type="password"] {
        background-color: #FFFFFF !important;
        color: #111827 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }

    /* 7. 버튼 디자인 (하단 배치 및 전체 너비) */
    div.stButton > button {
        width: 100% !important;
        margin-top: 15px !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        height: 45px !important;
        border: none !important;
    }
    
    button[key="btn_gemini"] { background-color: #2563EB !important; color: white !important; }
    button[key="btn_gpt"] { background-color: #10B981 !important; color: white !important; }
    button[key="btn_pw"] { background-color: #EF4444 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 로그인 체크 ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요한 페이지입니다. 메인 홈에서 로그인해 주세요.")
    st.stop()

# --- 데이터 및 업데이트 함수 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def update_info(field, value):
    try:
        df = conn.read(worksheet="Users")
        idx = df.index[df['username'] == st.session_state.username].tolist()[0]
        if field == 'password':
            df.at[idx, 'hashed_password'] = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        elif field == 'gemini':
            df.at[idx, 'gemini_api_key'] = value
            st.session_state.user_keys['GEMINI'] = value
        elif field == 'gpt':
            df.at[idx, 'openai_api_key'] = value
            st.session_state.user_keys['OPENAI'] = value
        conn.update(worksheet="Users", data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return False

# --- 메인 레이아웃 ---
st.title("⚙️ 계정 설정")

# === 1. Gemini 섹션 (파란색 배경 박스) ===
with st.container():
    st.markdown('<div class="gemini-container-marker"></div>', unsafe_allow_html=True)
    st.markdown('<h3>💎 Gemini API 설정</h3>', unsafe_allow_html=True)
    st.markdown('<p>Google AI Studio에서 발급받은 키를 입력하세요.</p>', unsafe_allow_html=True)
    st.markdown('<b>Gemini API Key</b>', unsafe_allow_html=True)
    new_gemini = st.text_input("g_key", value=st.session_state.user_keys.get('GEMINI', ''), type="password", key="edit_gemini", label_visibility="collapsed")
    if st.button("수정", key="btn_gemini"):
        if update_info('gemini', new_gemini):
            st.toast("✅ Gemini 키 업데이트 완료!")

st.divider()

# === 2. GPT 섹션 (투명 배경) ===
with st.container():
    st.markdown('<div class="gemini-container-marker"></div>', unsafe_allow_html=True)
    st.markdown('<h3>🤖 GPT API 설정</h3>', unsafe_allow_html=True)
    st.markdown('<p>OpenAI API 키를 입력하세요. (선택사항)</p>', unsafe_allow_html=True)
    st.markdown('<b>GPT API Key</b>', unsafe_allow_html=True)
    new_gpt = st.text_input("o_key", value=st.session_state.user_keys.get('OPENAI', ''), type="password", key="edit_gpt", label_visibility="collapsed")
    if st.button("수정", key="btn_gpt"):
        if update_info('gpt', new_gpt):
            st.toast("✅ GPT 키 업데이트 완료!")

st.divider()

# === 3. 비밀번호 섹션 (투명 배경) ===
with st.container():
    st.markdown('<div class="gemini-container-marker"></div>', unsafe_allow_html=True)
    st.markdown('<h3>🔒 비밀번호 변경</h3>', unsafe_allow_html=True)
    st.markdown('<p>새로운 비밀번호를 입력하세요. (4자 이상)</p>', unsafe_allow_html=True)
    st.markdown('<b>New Password</b>', unsafe_allow_html=True)
    new_pw = st.text_input("p_key", type="password", key="edit_pw", label_visibility="collapsed")
    if st.button("저장", key="btn_pw"):
        if len(new_pw) >= 4:
            if update_info('password', new_pw):
                st.toast("✅ 비밀번호 변경 완료!")
        else:
            st.error("비밀번호는 4자 이상이어야 합니다.")