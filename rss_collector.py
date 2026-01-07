
import feedparser
import pandas as pd
from datetime import datetime

def fetch_rss_feeds(rss_urls):
    all_articles = []

    for url in rss_urls:
        print(f"[RSS Collector] Processing URL: {url}")
        feed = feedparser.parse(url)
        if not feed.entries:
            print(f"[RSS Collector] No entries found for {url}")
            continue

        for entry in feed.entries:
            # 필요한 정보 추출 및 기본값 설정
            title = getattr(entry, 'title', 'No Title')
            link = getattr(entry, 'link', '#')
            published_str = getattr(entry, 'published', None)
            summary = getattr(entry, 'summary', 'No Summary')

            # 발행 시간 파싱 및 일관된 형식으로 변환
            published = None
            if published_str:
                try:
                    # feedparser는 RFC 822 형식을 사용하므로 파싱 시도
                    published = datetime.strptime(published_str, '%a, %d %b %Y %H:%M:%S %z')
                except ValueError:
                    try:
                        # 다른 일반적인 형식 시도 (ISO 8601 등)
                        published = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
                    except ValueError:
                        # 파싱 실패 시 None
                        pass

            all_articles.append({
                'title': title,
                'link': link,
                'published': published,
                'summary': summary
            })
    
    if not all_articles:
        print("[RSS Collector] No articles collected from any URL.")
        return pd.DataFrame(columns=['title', 'link', 'published', 'summary'])

    # Pandas DataFrame으로 변환
    df = pd.DataFrame(all_articles)

    if df.empty:
        # 빈 데이터프레임일 경우, 필요한 컬럼들을 가진 빈 데이터프레임 반환
        return pd.DataFrame(columns=['title', 'link', 'published', 'summary'])

    # 'published' 컬럼이 datetime 객체인지 확인하고, None 값은 필터링 또는 적절히 처리
    df = df[df['published'].notna()]
    df['published'] = pd.to_datetime(df['published'])

    # 최신순으로 정렬
    df = df.sort_values(by='published', ascending=False).reset_index(drop=True)

    return df

if __name__ == '__main__':
    # 매일경제, 한국경제 RSS 피드 예시
    # 실제 RSS URL은 해당 언론사 웹사이트에서 확인해야 합니다.
    # 여기서는 예시 URL을 사용합니다.
    rss_urls = [
        "https://www.mk.co.kr/rss/30100001/", # 매일경제 주요뉴스
        "https://www.hankyung.com/feed/economy", # 한국경제 뉴스
        # 추가 경제지 RSS URL
    ]

    news_df = fetch_rss_feeds(rss_urls)

    if not news_df.empty:
        print("뉴스 수집 및 정렬 완료:")
        print(news_df.head())
        print(f"총 {len(news_df)}개의 뉴스 기사 수집.")
    else:
        print("뉴스를 수집하지 못했습니다. RSS URL을 확인해주세요.")
