
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from rss_collector import fetch_rss_feeds

# --- Streamlit 앱 시작 --- #
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# 다크 모드 및 금융 앱 스타일 UI 설정 (Streamlit 기본 테마 사용)
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stButton>button {
        color: #FFFFFF;
        background-color: #262730;
        border-radius: 5px;
        border: 1px solid #4F4F4F;
    }
    .stButton>button:hover {
        border-color: #00BFFF;
        color: #00BFFF;
    }
    .css-1d391kg {
        background-color: #1E2129; /* 사이드바 배경 */
    }
    .simple-news-card {
        background-color: #1E2129;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        border-left: 5px solid #00BFFF;
    }
    .simple-news-card h3 {
        color: #00BFFF;
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size:1.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("📈 오늘의 증시 핵심 요약")

st.markdown("--- ")

# --- 카테고리 탭 (미국주식/테크/초보자) --- #
tab1, = st.tabs(["모든 뉴스"])

def display_news_cards(news_data, category):
    if news_data.empty:
        st.info(f"{category} 관련 뉴스가 없습니다.")
        return

    for index, row in news_data.iterrows():
        with st.container():
            st.markdown(f"<div class='simple-news-card'>", unsafe_allow_html=True)
            st.markdown(f"### {row['title']}", unsafe_allow_html=True)
            st.markdown(f"<p>{row['summary']}</p>", unsafe_allow_html=True)
            st.link_button("원문 링크", row['link'])
            st.markdown(f"</div>", unsafe_allow_html=True)


# --- 사이드바 --- #
st.sidebar.header("뉴스 설정")

# RSS URL 리스트 (추후 설정 파일 등으로 분리 가능)
rss_urls = [
    "https://www.mk.co.kr/rss/30100001/", # 매일경제 주요뉴스
    "https://www.hankyung.com/feed/economy", # 한국경제 뉴스
    # 추가 경제지 RSS URL
]

# 뉴스 업데이트 버튼
if st.sidebar.button("뉴스 업데이트"):
    with st.spinner("최신 뉴스를 수집 중..."):
        collected_news_df = fetch_rss_feeds(rss_urls)

        if not collected_news_df.empty:
            st.session_state['news_data'] = collected_news_df
            st.success(f"{len(collected_news_df)}개의 뉴스를 업데이트 완료!")
        else:
            st.error("뉴스 수집에 실패했습니다. RSS URL을 확인해주세요.")

# 세션 상태에 뉴스 데이터가 없으면 초기화
if 'news_data' not in st.session_state:
    st.session_state['news_data'] = pd.DataFrame(columns=['title', 'link', 'published', 'summary'])

# 카테고리별 뉴스 필터링 및 표시
with tab1:
    st.header("모든 뉴스")
    display_news_cards(st.session_state['news_data'], "모든 뉴스")