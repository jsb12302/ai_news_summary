
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import bcrypt

# Google Sheets 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_users_df():
    try:
        # Google Sheets에서 사용자 데이터 불러오기
        # 캐시를 사용하면 여러 번 호출해도 시트에서 데이터를 한 번만 로드합니다.
        return conn.read(worksheet="users", usecols=list(range(4)), ttl=5) # ttl=5s 캐싱
    except Exception as e:
        st.error(f"Google Sheets에서 사용자 데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame(columns=['id', 'password', 'openai_api_key', 'gemini_api_key'])

def save_user_df(df):
    try:
        conn.update(worksheet="users", data=df)
    except Exception as e:
        st.error(f"Google Sheets에 사용자 데이터를 저장하는 중 오류 발생: {e}")

def register_user(username, password, openai_api_key=None, gemini_api_key=None):
    users_df = get_users_df()
    if username in users_df['id'].values:
        return False, "이미 존재하는 사용자 ID입니다."

    # 비밀번호 암호화
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_user = pd.DataFrame([{
        'id': username,
        'password': hashed_password,
        'openai_api_key': openai_api_key,
        'gemini_api_key': gemini_api_key
    }])
    
    updated_df = pd.concat([users_df, new_user], ignore_index=True)
    save_user_df(updated_df)
    return True, "회원가입이 성공적으로 완료되었습니다."

def verify_user(username, password):
    users_df = get_users_df()
    user_data = users_df[users_df['id'] == username]
    if user_data.empty:
        return False, "존재하지 않는 사용자입니다.", None
    
    stored_password = user_data.iloc[0]['password']
    if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
        user_api_keys = {
            'OPENAI': user_data.iloc[0]['openai_api_key'] if pd.notna(user_data.iloc[0]['openai_api_key']) else None,
            'GEMINI': user_data.iloc[0]['gemini_api_key'] if pd.notna(user_data.iloc[0]['gemini_api_key']) else None,
        }
        return True, "로그인 성공!", user_api_keys
    else:
        return False, "비밀번호가 일치하지 않습니다.", None

def update_user_api_keys(username, openai_api_key=None, gemini_api_key=None):
    users_df = get_users_df()
    user_index = users_df[users_df['id'] == username].index
    if not user_index.empty:
        if openai_api_key is not None:
            users_df.loc[user_index[0], 'openai_api_key'] = openai_api_key
        if gemini_api_key is not None:
            users_df.loc[user_index[0], 'gemini_api_key'] = gemini_api_key
        save_user_df(users_df)
        return True, "API 키가 업데이트되었습니다."
    return False, "사용자를 찾을 수 없습니다."
