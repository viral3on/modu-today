import feedparser
from datetime import datetime, timezone, timedelta

# 한국 표준시(KST) 기준 날짜
kst = timezone(timedelta(hours=9))
today_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
date_badge = datetime.now(kst).strftime("%Y.%m.%d")

# 1. 뉴스 RSS 피드 목록 (국내 증시 및 해외 증시)
FEEDS = {
    "국내 증시 / 금융 이슈": [
        "https://news.google.com/rss/search?q=%ED%95%9C%EA%B5%AD%EC%A6%9D%EC%8B%9C+%EC%BD%94%EC%8A%A4%ED%94%BC+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EB%B0%98%EB%8F%84%EC%B2%B4+%ED%95%98%EC%9D%B4%EB%8B%89%EC%8A%A4+%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ],
    "미국 증시 / 글로벌 매크로": [
        "https://news.google.com/rss/search?q=%EB%82%98%EC%8A%A4%EB%8B%A5+SP500+%EB%89%B4%EC%9A%95%EC%A6%9D%EC%8B%9C+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%ED%99%98%EC%9C%A8+%EA%B8%88%EB%A6%AC+%EC%97%B0%EC%A4%80+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ]
}

def fetch_news():
    sections_html = ""
    
    for category, urls in FEEDS.items():
        items = []
        for url in urls:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # 피드당 상위 5개 추출
                title = entry.title.replace('"', '&quot;')
                link = entry.link
                # 신문사 이름 분리 (Google News 형식: "기사제목 - 언론사")
                source = "주요 언론"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                items.append({"title": title, "link": link, "source": source})
        
        # 중복 기사 제거
        unique_items = []
        seen_titles = set()
        for it in items:
            clean_title = it['title'][:25]
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                unique_items.append(it)

        # HTML 카드 리스트 빌드
        list_html = ""
        for it in unique_items[:6]: # 카테고리당 최종 6개 선별
            list_html += f"""
            <a href="{it['link']}" target="_blank" rel="noopener noreferrer nofollow" 
               class="block p-4 rounded-xl bg-[#141A28] border border-gray-800/80 hover:border-blue-500/50 hover:bg-[#192234] transition duration-200 group">
              <div class="flex justify-between items-start gap-2">
                <span class="text-sm font-semibold text-gray-200 group-hover:text-blue-400 leading-snug line-clamp-2">
                  {it['title']}
                </span>
                <span class="text-[11px] font-mono text-gray-500 flex-shrink-0">↗</span>
              </div>
              <div class="mt-2 text-[11px] font-medium text-gray-400">
                {it['source']} • <span>오늘의 브리핑</span>
              </div>
            </a>
            """

        sections_html += f"""
        <div class="space-y-3">
          <h2 class="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <span class="w-2 h-2 rounded-full bg-rose-500"></span> {category}
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            {list_html}
          </div>
        </div>
        """
    return sections_html

news_content = fetch_news()

# 전체 HTML 조립 (불펌 방지 + 다크테마 + 애드센스)
html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>국내 및 미국 증시 주요 뉴스 브리핑 | 매일 자동 갱신</title>
  <meta name="description" content="코스피, 나스닥, 반도체, 환율 등 국내외 금융 시장의 핵심 뉴스를 매일 실시간 자동 브리핑합니다.">
  <meta name="robots" content="index, follow, noarchive">
  
  <!-- 구글 애드센스 -->
  <meta name="google-adsense-account" content="ca-pub-6122968996738347">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6122968996738347" crossorigin="anonymous"></script>

  <script src="https://cdn.tailwindcss.com"></script>

  <!-- 타 사이트 불펌 및 봇 크롤링 방지 스타일 -->
  <style>
    body {{
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
    }}
  </style>
</head>
<body class="bg-[#0B0E14] text-gray-100 font-sans antialiased pb-20" oncontextmenu="return false;">

  <!-- 상단 헤더 -->
  <header class="border-b border-gray-800/80 bg-[#111622]/95 backdrop-blur sticky top-0 z-40 px-4 py-3">
    <div class="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2.5">
        <span class="flex h-2.5 w-2.5 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
        </span>
        <span class="text-base font-black tracking-tight text-white">DAILY MARKET NEWS</span>
        <span class="text-[10px] bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded font-mono font-bold">자동 갱신</span>
      </div>
      <div class="text-xs font-mono text-gray-400">
        업데이트: <span class="text-gray-200 font-bold">{today_str}</span>
      </div>
    </div>
  </header>

  <!-- 메인 뉴스 컨테이너 -->
  <main class="max-w-5xl mx-auto p-4 md:p-6 space-y-8 mt-2">
    
    <div class="bg-[#141A28] border border-gray-800 rounded-2xl p-5 md:p-6 shadow-xl flex flex-wrap justify-between items-center gap-4">
      <div>
        <h1 class="text-xl md:text-2xl font-black text-white tracking-tight">오늘의 국내 & 글로벌 금융 핵심 뉴스</h1>
        <p class="text-xs text-gray-400 mt-1">국내외 주요 언론사의 핵심 이슈를 자동으로 선별하여 링크를 제공합니다.</p>
      </div>
      <div class="px-3 py-1.5 rounded-lg bg-gray-800/80 text-xs font-mono text-gray-300 border border-gray-700">
        발행 기준: {date_badge}
      </div>
    </div>

    <!-- 파이썬 자동 수집 기사 영역 -->
    {news_content}

    <!-- 안내 및 면책 공고 -->
    <article class="bg-[#141A28]/40 border border-gray-800/60 rounded-xl p-4 text-xs text-gray-500 leading-relaxed">
      ※ 본 페이지의 기사 링크 및 제목은 언론사 RSS를 통해 자동 수집된 정보이며, 기사 본문의 저작권은 각 언론사에 있습니다. 본 사이트는 투자 참고용 링크만을 제공하며 특정 종목에 대한 투자 권유를 하지 않습니다.
    </article>

  </main>

</body>
</html>
"""

with open("news.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Successfully generated news.html at {today_str}")