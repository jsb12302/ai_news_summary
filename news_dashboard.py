import streamlit as st
from google import genai
from rss_collector import fetch_rss_feeds, SOURCES

# --- Gemini 요약 함수 ---
def analyze_news_gemini(api_key, title, summary):
    try:
        client = genai.Client(api_key=api_key.strip())
        prompt = f"투자 전문가로서 뉴스 분석: {title}\n내용: {summary}. 핵심요약, 시장영향, 투자포인트 작성."
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 분석 실패: {str(e)}"

# --- 개별 뉴스 카드 렌더링 함수 ---
def display_news_cards(df, market_key):
    if df.empty:
        st.info("표시할 뉴스가 없습니다.")
        return

    for idx, row in df.head(10).iterrows():
        with st.container():
            pub_time = row["published"].strftime("%m/%d %H:%M")
            st.markdown(
                f'<div class="news-card">'
                f'<h3>{row["title"]}</h3>'
                f'<p style="color:#6B7280; font-size:0.9rem;">{row["published"].strftime("%Y-%m-%d %H:%M")} | '
                f'<a href="{row["link"]}" target="_blank" style="color:#3B82F6;">기사 원문</a></p>'
                f'</div>',
                unsafe_allow_html=True
            )

            if st.button(f"🤖 AI 분석 실행", key=f"ai_{market_key}_{idx}"):
                if st.session_state.logged_in:
                    if st.session_state.user_keys['GEMINI']:
                        with st.spinner("AI 분석 중..."):
                            res = analyze_news_gemini(st.session_state.user_keys['GEMINI'], row['title'], row['summary'])
                            st.markdown(f'<div class="ai-result">{res}</div>', unsafe_allow_html=True)
                    else:
                        st.error("API 키를 등록해주세요.")
                else:
                    st.warning("로그인이 필요합니다.")

# --- 메인 뉴스 화면 렌더링 함수 ---
def render_news_section():
    st.markdown("""
            <style>
                /* 메인 상단 탭 스타일 */
                button[data-baseweb="tab"] {
                    flex: 1 !important;
                    text-align: center !important;
                }
                button[data-baseweb="tab"] p {
                    font-size: 1.3rem !important;
                    font-weight: 700 !important;
                }
                /* 하위 탭(언론사별) 글씨 크기 조정 */
                .stTabs [data-baseweb="tab"] p {
                    font-size: 1rem !important;
                }
            </style>
        """, unsafe_allow_html=True)

    st.title("📈 증시 핵심 요약 대시보드")

    # 1단계 메인 탭: 국내장, 미국장
    tab_main_kor, tab_main_usa = st.tabs(["🇰🇷 국내장", "🇺🇸 미국장"])

    # --- 국내장 섹션 ---
    with tab_main_kor:
        kor_source_names = list(SOURCES["KOREA"].keys())
        # 2단계 하위 탭: 국내 언론사 6개
        sub_tabs_kor = st.tabs(kor_source_names)

        for i, name in enumerate(kor_source_names):
            with sub_tabs_kor[i]:
                st.subheader(f"🇰🇷 {name} 증시 뉴스")
                if st.button(f"🔄 {name} 새로고침", key=f"refresh_kor_{i}"):
                    st.cache_data.clear()
                    st.rerun()

                news_df = fetch_rss_feeds("KOREA", source_name=name)
                display_news_cards(news_df, f"KOR_{name}")

    # --- 미국장 섹션 ---
    with tab_main_usa:
        usa_source_names = list(SOURCES["USA"].keys())
        # 2단계 하위 탭: 미국 관련 소스 2개
        sub_tabs_usa = st.tabs(usa_source_names)

        for i, name in enumerate(usa_source_names):
            with sub_tabs_usa[i]:
                st.subheader(f"🇺🇸 {name} 뉴스")
                if st.button(f"🔄 {name} 새로고침", key=f"refresh_usa_{i}"):
                    st.cache_data.clear()
                    st.rerun()

                news_df = fetch_rss_feeds("USA", source_name=name)
                display_news_cards(news_df, f"USA_{name}")