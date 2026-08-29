import feedparser
from datetime import datetime, timezone, timedelta

kst = timezone(timedelta(hours=9))
today_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
date_badge = datetime.now(kst).strftime("%Y.%m.%d")

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
        "https://news.google.com/rss/search?q=%EC%95%BC%EA%B0%84%EC%84%A0%EC%AC%BC+%EC%84%A0%EB%AC%BC+%EC%98%B5%EC%85%98+when:1d&hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/search?q=%EC%A3%BC%EC%8B%9D+%EC%84%A0%EB%AC%BC+%EC%98%B5%EC%85%98+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    ]
}

def fetch_news():
    sections_html = ""
    ticker_items = []
    
    for category, urls in FEEDS.items():
        items = []
        for url in urls:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title.replace('"', '&quot;')
                link = entry.link
                source = "주요 언론"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    title = parts[0]
                    source = parts[1]
                items.append({"title": title, "link": link, "source": source})
        
        unique_items = []
        seen_titles = set()
        for it in items:
            clean_title = it['title'][:25]
            if clean_title not in seen_titles:
                seen_titles.add(clean_title)
                unique_items.append(it)
                ticker_items.append(it)

        list_html = ""
        for it in unique_items[:6]: 
            list_html += f"""
            <a href="{it['link']}" target="_blank" rel="noopener noreferrer nofollow" 
               class="block p-4 rounded-xl bg-[#141A28] border border-gray-800/80 hover:border-emerald-500/50 hover:bg-[#192234] transition duration-200 group">
              <div class="flex justify-between items-start gap-2">
                <span class="text-sm font-semibold text-gray-200 group-hover:text-emerald-400 leading-snug line-clamp-2">
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
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span> {category}
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            {list_html}
          </div>
        </div>
        """
        
    return sections_html, ticker_items

news_content, ticker_items = fetch_news()

ticker_html = ""
for it in ticker_items[:25]:
    ticker_html += f"""
    <a href="{it['link']}" target="_blank" rel="noopener noreferrer nofollow" class="inline-flex items-center gap-2 mx-6 text-xs text-emerald-300 hover:text-white transition font-medium">
      <span class="text-emerald-400 font-black animate-pulse">⚡ LIVE</span> {it['title']} <span class="text-[10px] text-gray-400 font-mono">({it['source']})</span>
    </a>
    """

html_template = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MODU.TODAY | 실시간 금융 및 정책 정보 대시보드</title>
  <meta name="description" content="코스피, 환율, 원자재, 공모주, 정부 지원금 등 매일 실시간 자동 브리핑합니다.">
  <meta name="robots" content="index, follow, noarchive">
  
  <meta name="google-adsense-account" content="ca-pub-6122968996738347">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6122968996738347" crossorigin="anonymous"></script>

  <script src="https://cdn.tailwindcss.com"></script>

  <style>
    body {{
      -webkit-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
    }}
    @keyframes marquee {{
      0% {{ transform: translateX(0%); }}
      100% {{ transform: translateX(-50%); }}
    }}
    .animate-marquee {{
      display: flex;
      width: max-content;
      /* 속도를 60초로 늦추어 천천히 읽기 쉽게 조정 */
      animation: marquee 60s linear infinite;
    }}
    .animate-marquee:hover {{
      animation-play-state: paused;
    }}
  </style>
</head>
<body class="bg-[#0B0E14] text-gray-100 font-sans antialiased pb-20" oncontextmenu="return false;">

  <!-- 상단 네비게이션 헤더 (고정) -->
  <header class="border-b border-gray-800/80 bg-[#111622]/95 backdrop-blur sticky top-0 z-40 px-4 py-3">
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2.5">
        <span class="flex h-2.5 w-2.5 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
        </span>
        <a href="/" class="text-base font-black tracking-tight text-white">MODU.TODAY</a>
      </div>
      
      <nav class="flex flex-wrap gap-1 text-[11px] font-medium">
        <a href="lotto.html" class="px-2 py-1 rounded bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600 hover:text-white transition">🍀로또</a>
        <a href="loan.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">대출</a>
        <a href="deposit.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">예적금</a>
        <a href="salary.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">연봉</a>
        <a href="realtor.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">복비</a>
        <a href="parttime.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">주휴수당</a>
        <a href="severance.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">퇴직금</a>
        <a href="counter.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">카운터</a>
        <a href="compound.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">복리</a>
        <a href="annual-leave.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">연차</a>
        <a href="unemployment.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">실업급여</a>
        <a href="average-price.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">평단가</a>
        <a href="rent-tax.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">임대세</a>
        <a href="dday.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">D-day</a>
        <a href="exchange.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">환율</a>
        <a href="car-tax.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">자동차세</a>
        <a href="bmi.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">BMI</a>
        <a href="electricity.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">전기요금</a>
        <a href="area.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">평형</a>
        <a href="dividend.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">배당금</a>
        <a href="customs.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">관세</a>
        <a href="registration-tax.html" class="px-2 py-1 rounded bg-[#141A28] border border-gray-700 text-gray-300 hover:text-white transition">취득세</a>
        <a href="yasun.html" class="px-2 py-1 rounded bg-amber-600/20 text-amber-400 border border-amber-500/30 hover:bg-amber-600 hover:text-white transition">🌙야간선물</a>
      </nav>
    </div>
  </header>

  <!-- 형광 네온 테두리 & 스크롤 시에도 상단 고정되는 속보 전광판 띠 -->
  <div class="sticky top-[49px] z-30 bg-[#061018] border-y-2 border-emerald-500 py-2.5 overflow-hidden whitespace-nowrap shadow-[0_0_15px_rgba(16,185,129,0.3)]">
    <div class="absolute left-0 top-0 bottom-0 w-16 bg-gradient-to-r from-[#061018] to-transparent z-10 pointer-events-none"></div>
    <div class="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-[#061018] to-transparent z-10 pointer-events-none"></div>
    <div class="animate-marquee">
      {ticker_html}
      {ticker_html}
    </div>
  </div>

  <main class="max-w-5xl mx-auto p-4 md:p-6 space-y-8 mt-4">
    
    <div class="bg-[#141A28] border border-gray-800 rounded-2xl p-5 md:p-6 shadow-xl flex flex-wrap justify-between items-center gap-4">
      <div>
        <h1 class="text-xl md:text-2xl font-black text-white tracking-tight">오늘의 금융, 원자재 및 정책 핵심 브리핑</h1>
        <p class="text-xs text-gray-400 mt-1">증시, 환율/원자재, 공모주 일정 및 정부 지원금 소식을 매일 실시간으로 자동 수집합니다.</p>
      </div>
      <div class="px-3 py-1.5 rounded-lg bg-gray-800/80 text-xs font-mono text-gray-300 border border-gray-700">
        업데이트: {today_str}
      </div>
    </div>

    {news_content}

    <article class="bg-[#141A28]/40 border border-gray-800/60 rounded-xl p-4 text-xs text-gray-500 leading-relaxed">
      ※ 본 페이지의 기사 링크 및 제목은 언론사 RSS를 통해 자동 수집된 정보이며, 기사 본문의 저작권은 각 언론사에 있습니다. 본 사이트는 투자 참고용 링크만을 제공하며 특정 종목에 대한 투자 권유를 하지 않습니다.
    </article>

  </main>

</body>
</html>
""".format(today_str=today_str, news_content=news_content, ticker_html=ticker_html)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Successfully generated index.html with sticky neon marquee at {today_str}")
