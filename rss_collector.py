import feedparser
import pandas as pd
from datetime import datetime

# # --- 뉴스 출처(RSS URL)를 여기서 관리합니다 --- #
# RSS_SOURCES = [
# #     "https://www.hankyung.com/feed/stock",   # 한국경제 증시
# #     "https://www.mk.co.kr/rss/30100001/",   # 매일경제 증권
# #     "http://rss.edaily.co.kr/stock_news.xml", # 이데일리 증권
# #     "https://www.yonhapnewstv.co.kr/browse/feed/" # 연합뉴스 속보
#     "https://www.hankyung.com/feed/finance"
# https://www.hankyung.com/feed/finance
# https://www.mk.co.kr/rss/50200011/
# https://www.yonhapnewstv.co.kr/browse/feed/
# http://rss.edaily.co.kr/stock_news.xml
# http://rss.newspim.com/news/category/105
# https://news.einfomax.co.kr/rss/S1N2.xml
# # ]

SOURCES = {
    "KOREA": [
        "https://www.hankyung.com/feed/finance"
        "https://www.mk.co.kr/rss/50200011",   # 한국경제 증시
        "https://www.yonhapnewstv.co.kr/browse/feed",    # 매일경제 증권
        "http://rss.edaily.co.kr/stock_news.xml"  # 이데일리 증권
        "http://rss.newspim.com/news/category/105"  # 이데일리 증권
        "https://news.einfomax.co.kr/rss/S1N2.xml"  # 이데일리 증권
    ],
    "USA": [
        "https://www.hankyung.com/feed/international", # 한국경제 국제/미국
        "https://www.mk.co.kr/rss/40300001/"           # 매일경제 글로벌
    ]
}

def fetch_rss_feeds(market_type="KOREA"):
    # market_type에 따라 SOURCES에서 URL 리스트를 가져옵니다.
    rss_urls = SOURCES.get(market_type, SOURCES["KOREA"])

    all_articles = []

    for url in rss_urls:
        feed = feedparser.parse(url)
        if not feed.entries:
            continue

        for entry in feed.entries:
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '#')
            published_str = getattr(entry, 'published', None)
            summary = getattr(entry, 'summary', 'No Summary')

            published = None
            if published_str:
                try:
                    # RFC 822 형식 시도
                    published = datetime.strptime(published_str, '%a, %d %b %Y %H:%M:%S %z')
                except ValueError:
                    try:
                        # ISO 8601 형식 시도
                        published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    except ValueError:
                        pass

            all_articles.append({
                'title': title,
                'link': link,
                'published': published,
                'summary': summary
            })

    if not all_articles:
        return pd.DataFrame(columns=['title', 'link', 'published', 'summary'])

    df = pd.DataFrame(all_articles)
    df = df[df['published'].notna()]
    df['published'] = pd.to_datetime(df['published'])

    # 최신순 정렬
    df = df.sort_values(by='published', ascending=False).reset_index(drop=True)

    return df