import streamlit as st
from google import genai
from rss_collector import fetch_rss_feeds # 인자 없는 함수를 불러옴

# --- Gemini 요약 함수 --- #
def analyze_news_gemini(api_key, title, summary):
    try:
        client = genai.Client(api_key=api_key.strip())
        prompt = f"투자 전문가로서 뉴스 분석: {title}\n내용: {summary}. 핵심요약, 시장영향, 투자포인트 작성."
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 분석 실패: {str(e)}"

# --- 개별 뉴스 카드 렌더링 함수 (중복 코드 방지) --- #
def display_news_cards(df, market_key):
    if df.empty:
        st.info("표시할 뉴스가 없습니다.")
        return

    for idx, row in df.head(10).iterrows():
        with st.container():
            st.markdown(
                f'<div class="news-card">'
                f'<h3>{row["title"]}</h3>'
                f'<p>{row["published"]} | '
                f'<a href="{row["link"]}" target="_blank" style="color:#3B82F6;">기사 원문</a></p>'
                f'</div>',
                unsafe_allow_html=True
            )
            # key값에 market_key를 추가하여 탭 간 버튼 충돌 방지
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

# --- 메인 뉴스 화면 렌더링 함수 --- #
def render_news_section():
    st.markdown("""
            <style>
                /* 1. 탭 버튼 전체 너비 및 1:1 비율 설정 */
                button[data-baseweb="tab"] {
                    flex: 1 !important;
                    text-align: center !important;
                }

                /* 2. 탭 글씨 크기 및 스타일 설정 */
                button[data-baseweb="tab"] p {
                    font-size: 1.5rem !important;  /* 기존보다 약 1.5배 크게 설정 */
                    font-weight: 700 !important;   /* 아주 굵게 */
                    color: #333333 !important;      /* 진한 회색 */
                }

                /* 3. 활성화된(클릭한) 탭의 글씨 색상 강조 (파란색) */
                button[aria-selected="true"] p {
                    color: #3B82F6 !important;     /* 선택된 탭은 강조색 적용 */
                }

                /* 4. 탭 내부 정렬 보정 */
                button[data-baseweb="tab"] > div {
                    justify-content: center !important;
                    width: 100%;
                }
            </style>
        """, unsafe_allow_html=True)

    st.title("📈 오늘의 증시 핵심 요약")

    # 탭 생성: 국내장, 미국장
    tab_kor, tab_usa = st.tabs(["🇰🇷 국내장", "🇺🇸 미국장"])

    with tab_kor:
        st.subheader("국내 증시 주요 뉴스")
        if st.button("🔄 국내 뉴스 새로고침", key="refresh_kor"):
            st.cache_data.clear()
            st.rerun()

        news_df_kor = fetch_rss_feeds("KOREA")
        display_news_cards(news_df_kor, "KOR")

    with tab_usa:
        st.subheader("미국 증시 및 글로벌 뉴스")
        if st.button("🔄 미국 뉴스 새로고침", key="refresh_usa"):
            st.cache_data.clear()
            st.rerun()

        news_df_usa = fetch_rss_feeds("USA")
        display_news_cards(news_df_usa, "USA")