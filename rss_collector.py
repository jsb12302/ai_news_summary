import feedparser
import pandas as pd
from datetime import datetime

# --- 뉴스 출처를 언론사별로 세분화하여 관리 ---
SOURCES = {
    "KOREA": {
        "한국경제": "https://www.hankyung.com/feed/finance",
        "매일경제": "https://www.mk.co.kr/rss/50200011",
        "연합뉴스": "https://www.yna.co.kr/rss/economy.xml",
        "이데일리": "http://rss.edaily.co.kr/stock_news.xml",
        "뉴스핌": "http://rss.newspim.com/news/category/105",
        "인포맥스": "https://news.einfomax.co.kr/rss/S1N2.xml"
    },
    "USA": {
        "CNBC(속보)": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "Yahoo(시장)": "https://finance.yahoo.com/news/rssindex",
        "Investing": "https://www.investing.com/rss/news_25.rss",
        "한경국제": "https://www.hankyung.com/feed/international",
        "매경글로벌": "https://www.mk.co.kr/rss/40300001/"
    }
}

def fetch_rss_feeds(market_type="KOREA", source_name=None):
    """
    market_type: "KOREA" 또는 "USA"
    source_name: 특정 언론사 선택 (None일 경우 해당 시장 전체 수집)
    """
    market_data = SOURCES.get(market_type, SOURCES["KOREA"])

    if source_name:
        rss_urls = [market_data.get(source_name)]
    else:
        rss_urls = list(market_data.values())

    all_articles = []

    for url in rss_urls:
        if not url: continue
        feed = feedparser.parse(url)
        if not feed.entries:
            continue

        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6])
                published = dt + timedelta(hours=9)
            else:
                published = datetime.now()
        except Exception:
            published = datetime.now()

        for entry in feed.entries:
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '#')
            published_str = getattr(entry, 'published', None)
            summary = getattr(entry, 'summary', 'No Summary')

            all_articles.append({
                'title': title,
                'link': link,
                'published': published_str,
                'summary': summary
            })

    if not all_articles:
        return pd.DataFrame(columns=['title', 'link', 'published', 'summary'])

    df = pd.DataFrame(all_articles)
    # 날짜 정렬을 위해 datetime 형식 확정
    df['published'] = pd.to_datetime(df['published'])
    # 최신순 정렬
    df = df.sort_values(by='published', ascending=False).reset_index(drop=True)
    return df