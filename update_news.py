import feedparser
from datetime import datetime, timezone, timedelta

kst = timezone(timedelta(hours=9))
today_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
date_badge = datetime.now(kst).strftime("%Y.%m.%d")

# AdSense/검색 품질 보호: 도박·성인·스팸성 제목은 홈 뉴스에 노출하지 않음.
BLOCKED_NEWS_TERMS = (
    "토토", "토토사이트", "스포츠토토", "카지노", "바카라", "슬롯",
    "도박", "베팅", "먹튀", "성인사이트", "성인 사이트", "포르노",
    "porn", "casino", "betting", "gambling"
)
BLOCKED_NEWS_SOURCES = ("Histoire pour tous",)

def is_blocked_news(title, source=""):
    hay=(str(title)+" "+str(source)).lower().replace(" ", "")
    if any(term.lower().replace(" ", "") in hay for term in BLOCKED_NEWS_TERMS):
        return True
    return any(src.lower() in str(source).lower() for src in BLOCKED_NEWS_SOURCES)


# 모든 카테고리 쿼리 재점검 (기사가 안정적으로 꽉 차도록 구성)
FEEDS = {
    "국내 증시 / 코스피 코스닥": [
        "https://news.google.com/rss/search?q=%EC%BD%94%EC%8A%A4%ED%94%BC+%EC%BD%94%EC%8A%A4%EB%8B%A5+%EC%A6%9D%EC%8B%9C+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EA%B5%AD%EB%82%B0+%EC%A3%BC%EC%8B%9D+%ED%85%8c%EB%A7%88%EC%BC%80+%EC%A0%84%EB%A7%9D+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ],
    "환율 및 글로벌 원자재 시세": [
        "https://news.google.com/rss/search?q=%EC%9B%90%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8+%EC%A0%84%EB%A7%9D+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EA%B5%AC%EB%A6%AC+%EC%9C%A0%EA%B0%80+%EA%B8%88%EA%B0%92+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ],
    "공모주 청약 및 IPO 일정": [
        "https://news.google.com/rss/search?q=%EA%B3%B5%EB%AA%A8%EC%A3%BC+%EC%B2%AD%EC%95%BD+%EC%9D%BC%EC%A0%95+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EC%8B%A0%EA%B7%9C%EC%83%81%EC%9E%A5+IPO+%EC%B2%AD%EC%95%BD+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ],
    "정부 지원금 및 정책 소식": [
        "https://news.google.com/rss/search?q=%EC%A0%95%EB%B6%80+%EC%A7%80%EC%9B%90%EA%B8%88+%EC%B2%AD%EB%85%84+%EC%86%8C%EC%83%81%EA%B3%B5%EC%9D%B8+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EC%A7%80%EC%9E%90%EC%B2%98+%EC%A7%80%EC%9B%90%EA%B8%88+%EC%A3%BC%EA%B1%B0+%EC%A7%80%EC%9B%90+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ],
    "미국 증시 / 글로벌 매크로": [
        "https://news.google.com/rss/search?q=%EB%82%98%EC%8A%A4%EB%8B%A5+SP500+%EB%89%B4%EC%9A%95%EC%A6%9D%EC%8B%9C+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EB%AF%B8%EA%B5%AD+%EA%B8%88%EC%A6%AC+%EC%97%B0%EC%A4%80+%EB%A7%88%EA%B0%80+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ],
    "야간선물 / 파생 / 투자시황": [
        "https://news.google.com/rss/search?q=%EC%95%BC%EA%B0%84%EC%84%A0%EB%AC%BC+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EC%A3%BC%EC%8B%9D+%EC%84%A0%EB%AC%BC+%EC%98%B5%EC%85%98+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ]
}

def fetch_news():
    from urllib.request import Request, urlopen
    from urllib.parse import urlparse
    items, seen = [], set()
    for category, urls in FEEDS.items():
        category_items = []
        for url in urls:
            try:
                with urlopen(Request(url, headers={"User-Agent": "MODU-News/1.0"}), timeout=25) as response:
                    feed = feedparser.parse(response.read())
                for entry in feed.entries[:10]:
                    title = str(entry.get("title", "")).strip()
                    link = str(entry.get("link", ""))
                    source = str(entry.get("source", {}).get("title", "외부 언론"))
                    if " - " in title:
                        title, source = title.rsplit(" - ", 1)
                    if not title or is_blocked_news(title, source) or urlparse(link).scheme != "https":
                        continue
                    if title in seen:
                        continue
                    seen.add(title)
                    category_items.append({"title": title, "url": link, "source": source, "category": category})
            except Exception as error:
                print("News feed unavailable:", category, type(error).__name__)
        items.extend(category_items[:6])
    return items


def main():
    import json
    from pathlib import Path
    items = fetch_news()
    if not items:
        raise SystemExit("No valid news received; previous snapshot preserved")
    target = Path(__file__).resolve().parent / "news/data.json"
    target.parent.mkdir(exist_ok=True)
    data = {"updatedAt": datetime.now(timezone.utc).isoformat(), "updatedAtLabel": today_str, "items": items}
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(f"Updated {len(items)} external news links; homepage generated at deployment")


if __name__ == "__main__":
    main()
