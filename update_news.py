import feedparser
from datetime import datetime, timezone, timedelta

kst = timezone(timedelta(hours=9))
today_str = datetime.now(kst).strftime("%Y년 %m월 %d일 %H:%M KST")
date_badge = datetime.now(kst).strftime("%Y.%m.%d")

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
            # 기사 박스 테두리를 띠와 동일한 두께감(border-2)으로 업그레이드
            list_html += f"""
            <a href="{it['link']}" target="_blank" rel="noopener noreferrer nofollow" 
               class="block p-4 rounded-xl bg-[#141A28] border-2 border-yellow-400 hover:bg-[#1C2538] transition duration-200 group shadow-md">
              <div class="flex justify-between items-start gap-2">
                <span class="text-sm font-semibold text-gray-100 group-hover:text-yellow-300 leading-snug line-clamp-2">
                  {it['title']}
                </span>
                <span class="text-[11px] font-mono text-yellow-400 flex-shrink-0">↗</span>
              </div>
              <div class="mt-2 text-[11px] font-medium text-gray-400">
                {it['source']} • <span class="text-yellow-400/90 font-bold">오늘의 브리핑</span>
              </div>
            </a>
            """

        sections_html += f"""
        <div class="space-y-3">
          <h2 class="text-base font-bold text-white flex items-center gap-2 border-b border-gray-800 pb-2">
            <span class="w-2 h-2 rounded-full bg-yellow-400"></span> {category}
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
    <a href="{it['link']}" target="_blank" rel="noopener noreferrer nofollow" class="inline-flex items-center gap-2 mx-6 text-xs text-yellow-200 hover:text-white transition font-semibold">
      <span class="text-yellow-400 font-extrabold animate-pulse">⚡ BREAKING</span> {it['title']} <span class="text-[10px] text-emerald-300 font-mono">({it['source']})</span>
    </a>
    """


html_template = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MODU.TODAY</title>
<meta name="description" content="뉴스, YouTube 순위, 계산기, 게임, 로또, 아파트 실거래가를 한곳에서 확인하세요.">
<style>
:root{{
  --bg:#f6f8fc;
  --card:#ffffff;
  --text:#101828;
  --muted:#667085;
  --line:#e8edf5;
  --brand1:#6d5dfc;
  --brand2:#8b5cf6;
  --brand3:#5b8def;
  --shadow:0 18px 45px rgba(35,45,80,.10);
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{
  margin:0;
  font-family:Pretendard,"Noto Sans KR","Apple SD Gothic Neo",Arial,sans-serif;
  color:var(--text);
  background:
    radial-gradient(circle at 12% 0%, rgba(113,97,255,.08), transparent 28rem),
    linear-gradient(180deg,#fbfcff 0,#f6f8fc 430px);
}}
a{{color:inherit;text-decoration:none}}
button{{font:inherit}}
.wrap{{width:min(1180px,calc(100% - 36px));margin:auto}}

/* top */
.topbar{{
  position:sticky;top:0;z-index:30;
  background:rgba(255,255,255,.82);
  backdrop-filter:blur(18px);
  border-bottom:1px solid rgba(229,233,242,.9);
}}
.nav{{height:68px;display:flex;align-items:center;gap:24px}}
.logo{{
  font-size:20px;font-weight:900;letter-spacing:-.8px;
  display:flex;align-items:center;gap:9px;white-space:nowrap
}}
.logo-mark{{
  width:30px;height:30px;border-radius:10px;
  background:linear-gradient(145deg,var(--brand1),var(--brand3));
  box-shadow:0 8px 20px rgba(100,92,246,.28);
}}
.menu{{display:flex;align-items:center;gap:5px;margin-left:auto}}
.menu a{{
  padding:10px 12px;border-radius:11px;color:#475467;
  font-size:14px;font-weight:700;transition:.18s ease
}}
.menu a:hover{{background:#f2f4f8;color:#111827}}

/* hero */
.hero{{padding:34px 0 24px}}
.hero-box{{
  overflow:hidden;position:relative;
  min-height:385px;border-radius:32px;
  padding:54px 58px;
  color:white;
  background:
    radial-gradient(circle at 82% 14%,rgba(255,255,255,.24),transparent 15rem),
    radial-gradient(circle at 66% 95%,rgba(255,255,255,.13),transparent 17rem),
    linear-gradient(125deg,#5547e9 0%,#7758f8 45%,#4f86ef 100%);
  box-shadow:0 24px 65px rgba(79,70,229,.24);
}}
.hero-box:before,.hero-box:after{{
  content:"";position:absolute;border-radius:50%;border:1px solid rgba(255,255,255,.18)
}}
.hero-box:before{{width:280px;height:280px;right:-70px;top:-95px}}
.hero-box:after{{width:185px;height:185px;right:115px;bottom:-118px}}
.eyebrow{{
  display:inline-flex;align-items:center;gap:8px;
  padding:8px 12px;border-radius:999px;
  background:rgba(255,255,255,.14);
  border:1px solid rgba(255,255,255,.18);
  font-size:13px;font-weight:800
}}
.hero h1{{
  max-width:710px;margin:22px 0 13px;
  font-size:clamp(34px,5vw,60px);line-height:1.06;
  letter-spacing:-2.8px
}}
.hero p{{
  margin:0;color:rgba(255,255,255,.86);
  font-size:17px;line-height:1.7
}}
.quick{{
  position:relative;z-index:2;
  display:grid;grid-template-columns:repeat(6,1fr);
  gap:10px;margin-top:35px
}}
.quick a{{
  min-height:112px;padding:14px 10px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;
  text-align:center;
  background:rgba(255,255,255,.13);
  border:1px solid rgba(255,255,255,.18);
  border-radius:18px;font-weight:800;font-size:13px;
  backdrop-filter:blur(8px);transition:.18s ease
}}
.quick strong{{font-size:13px;line-height:1.25}}
.quick small{{font-size:10.5px;line-height:1.35;color:rgba(255,255,255,.72);font-weight:600}}
.quick a:hover{{transform:translateY(-3px);background:rgba(255,255,255,.22)}}
.quick .ico{{font-size:24px}}

/* sections */
.section{{padding:24px 0}}
.section-head{{
  display:flex;justify-content:space-between;align-items:flex-start;gap:20px;
  margin-bottom:16px
}}
.section-head h2{{margin:0;font-size:24px;letter-spacing:-.7px}}
.section-head p{{margin:5px 0 0;color:var(--muted);font-size:14px}}
.more{{font-size:13px;font-weight:800;color:#6b63e8;white-space:nowrap;margin-top:4px;flex:0 0 auto}}
.grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.grid-2{{display:grid;grid-template-columns:1.15fr .85fr;gap:16px}}
.card{{
  background:var(--card);border:1px solid var(--line);
  border-radius:22px;box-shadow:0 6px 20px rgba(31,41,55,.035)
}}
.news-card{{padding:22px;min-height:204px}}
.tag{{
  display:inline-flex;padding:6px 9px;border-radius:999px;
  background:#f0efff;color:#6757e8;font-size:11px;font-weight:900
}}
.news-card h3{{
  margin:14px 0 8px;font-size:20px;line-height:1.42;letter-spacing:-.5px
}}
.news-card p{{margin:0;color:var(--muted);font-size:14px;line-height:1.6}}
.news-meta{{margin-top:18px;color:#98a2b3;font-size:12px}}

.rank-card{{padding:22px}}
.rank-item{{
  display:grid;grid-template-columns:36px 1fr auto;
  gap:12px;align-items:center;padding:13px 0;border-bottom:1px solid #eef1f6
}}
.rank-item:last-child{{border-bottom:0}}
.rank-num{{
  width:32px;height:32px;border-radius:10px;background:#f4f3ff;
  color:#6c5ce7;display:grid;place-items:center;font-weight:900
}}
.rank-title{{font-size:14px;font-weight:800}}
.rank-sub{{font-size:12px;color:var(--muted);margin-top:4px}}
.up{{font-size:12px;font-weight:900;color:#e5484d}}

.lotto{{
  padding:24px;
  background:linear-gradient(145deg,#151925,#242a3b);
  color:#fff;border:0
}}
.lotto-top{{display:flex;justify-content:space-between;align-items:center;gap:14px}}
.lotto h3{{margin:0;font-size:22px}}
.lotto small{{color:#aeb6c7}}
.balls{{display:flex;gap:9px;flex-wrap:wrap;margin:24px 0 18px}}
.ball{{
  width:46px;height:46px;border-radius:50%;
  display:grid;place-items:center;font-size:15px;font-weight:900;
  background:#fff;color:#111827;box-shadow:inset 0 -4px 9px rgba(0,0,0,.12)
}}
.ball.bonus{{background:#9ca3af;color:#fff}}
.lotto-bottom{{display:flex;justify-content:space-between;gap:12px;color:#d7dceb;font-size:13px}}

.toolbox{{padding:22px}}
.tools{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:13px}}
.tool{{
  border:1px solid #edf0f5;border-radius:16px;padding:15px;
  transition:.18s ease
}}
.tool:hover{{border-color:#cfcafc;transform:translateY(-2px)}}
.tool strong{{font-size:14px}}
.tool div{{margin-top:5px;color:var(--muted);font-size:12px}}

.bottom-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.service-card{{padding:23px;min-height:165px;position:relative;overflow:hidden}}
.service-icon{{
  width:46px;height:46px;border-radius:14px;
  display:grid;place-items:center;background:#f4f3ff;font-size:23px
}}
.service-card h3{{margin:18px 0 6px;font-size:18px}}
.service-card p{{margin:0;color:var(--muted);font-size:13px;line-height:1.55}}

footer{{padding:34px 0 48px;color:#98a2b3;font-size:12px}}
.footer-box{{
  border-top:1px solid var(--line);padding-top:25px;
  display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap
}}

@media(max-width:900px){{
  .menu{{display:none}}
  .hero-box{{padding:40px 28px;min-height:auto}}
  .quick{{grid-template-columns:repeat(3,1fr)}}
  .grid-3,.bottom-grid{{grid-template-columns:1fr}}
  .grid-2{{grid-template-columns:1fr}}
}}
@media(max-width:520px){{
  .wrap{{width:min(100% - 24px,1180px)}}
  .nav{{height:60px}}
  .hero{{padding-top:16px}}
  .hero-box{{border-radius:24px;padding:32px 20px}}
  .hero h1{{font-size:36px;letter-spacing:-1.8px}}
  .hero p{{font-size:14px}}
  .quick{{grid-template-columns:repeat(2,1fr);margin-top:26px}}
  .quick a{{min-height:76px}}
  .section{{padding:18px 0}}
}}

.news-live{{display:grid;gap:12px}}
.news-live a{{display:block}}
.news-live article,.news-live>div{{
  background:#fff;border:1px solid #e8edf5;border-radius:18px;
  padding:18px 20px;box-shadow:0 5px 18px rgba(31,41,55,.035)
}}
.news-live h2,.news-live h3,.news-live h4{{margin:0 0 8px;line-height:1.45}}
.news-live p{{margin:0;color:#667085;line-height:1.6}}


.fixed-ticker{{
  position:fixed;left:0;right:0;bottom:0;z-index:80;
  height:34px;background:#111827;color:#fff;
  border-top:1px solid rgba(255,255,255,.08);
  overflow:hidden;display:flex;align-items:center;
  box-shadow:0 -4px 14px rgba(15,23,42,.10)
}}
.fixed-ticker .label{{
  flex:0 0 auto;height:100%;display:flex;align-items:center;
  padding:0 14px;font-size:11px;font-weight:900;
  background:linear-gradient(135deg,#6d5dfc,#5b8def);
  letter-spacing:-.2px
}}
.fixed-ticker .track{{overflow:hidden;white-space:nowrap;flex:1}}
.fixed-ticker .marquee{{
  display:inline-block;padding-left:100%;
  animation:moduTicker 140s linear infinite;
  font-size:12px;font-weight:700
}}
.fixed-ticker .marquee:hover{{animation-play-state:paused}}
@keyframes moduTicker{{
  from{{transform:translateX(0)}}
  to{{transform:translateX(-100%)}}
}}
body{{padding-bottom:34px}}


.yt-home-card{{padding:18px}}
.yt-home-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.yt-loading{{grid-column:1/-1;padding:40px 10px;text-align:center;color:#98a2b3;font-size:13px}}
.yt-mini{{display:block;min-width:0}}
.yt-thumb{{position:relative;aspect-ratio:16/9;border-radius:14px;overflow:hidden;background:#eef1f6;margin-bottom:10px}}
.yt-thumb img{{width:100%;height:100%;object-fit:cover;display:block}}
.yt-badge{{position:absolute;left:8px;top:8px;width:30px;height:30px;border-radius:10px;background:rgba(17,24,39,.88);color:#fff;display:grid;place-items:center;font-weight:900;font-size:13px}}
.yt-mini strong{{display:block;font-size:13px;line-height:1.42;letter-spacing:-.25px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.yt-mini span{{display:block;margin-top:5px;font-size:11px;color:#667085;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.yt-all{{display:block;text-align:right;margin-top:14px;font-size:12px;font-weight:800;color:#6b63e8}}
#ytRankBridge{{position:fixed;width:1px;height:1px;left:-9999px;top:-9999px;opacity:0;pointer-events:none;border:0}}

.calc-thumb-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.calc-thumb{{overflow:hidden;transition:.18s ease}}
.calc-thumb:hover{{transform:translateY(-3px);box-shadow:var(--shadow)}}
.calc-art{{height:112px;display:grid;place-items:center;font-size:42px;background:linear-gradient(145deg,#eef2ff,#f8f7ff)}}
.calc-body{{padding:16px}}
.calc-body strong{{display:block;font-size:15px}}
.calc-body span{{display:block;margin-top:6px;font-size:12px;color:#667085;line-height:1.5}}

.apt-feature{{display:grid;grid-template-columns:34% 1fr;overflow:hidden;min-height:245px;transition:.18s ease}}
.apt-feature:hover{{transform:translateY(-3px);box-shadow:var(--shadow)}}
.feature-art{{display:flex;align-items:center;justify-content:center;gap:12px;min-height:245px}}
.apt-art{{background:linear-gradient(145deg,#e8efff,#f4f1ff);color:#665ee6}}
.apt-art span{{font-size:64px}} .apt-art b{{font-size:42px;letter-spacing:-2px}}
.feature-copy{{padding:34px;display:flex;flex-direction:column;justify-content:center}}
.feature-kicker{{font-size:10px;font-weight:900;letter-spacing:1.5px;color:#7068eb}}
.feature-copy h3{{margin:10px 0 8px;font-size:25px;letter-spacing:-.8px}}
.feature-copy p{{margin:0;color:#667085;font-size:13px;line-height:1.7}}
.feature-copy strong{{margin-top:19px;font-size:13px;color:#655de5}}

.game-home-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.game-home-card{{overflow:hidden;transition:.18s ease}}
.game-home-card:hover{{transform:translateY(-3px);box-shadow:var(--shadow)}}
.game-art{{height:130px;display:grid;place-items:center;font-size:46px;font-weight:900}}
.blocks-art{{background:linear-gradient(145deg,#e9e7ff,#dfe9ff);color:#645ce8}}
.mine-art-home{{background:linear-gradient(145deg,#fff1e8,#fff8f3)}}
.n2048-art{{background:linear-gradient(145deg,#f4ecdd,#fff8e9);color:#8b7046;font-size:36px}}
.game-home-card>div:last-child{{padding:16px}}
.game-home-card strong{{display:block;font-size:16px}}
.game-home-card span{{display:block;margin-top:6px;font-size:12px;color:#667085;line-height:1.5}}

@media(max-width:900px){{
  .yt-home-grid{{grid-template-columns:1fr}}
  .calc-thumb-grid{{grid-template-columns:repeat(2,1fr)}}
  .apt-feature{{grid-template-columns:1fr}}
  .feature-art{{min-height:160px}}
  .game-home-grid{{grid-template-columns:1fr}}
}}
@media(max-width:520px){{
  .calc-thumb-grid{{grid-template-columns:1fr}}
  .apt-art span{{font-size:48px}} .apt-art b{{font-size:32px}}
  .feature-copy{{padding:24px}}
}}

</style>
</head>
<body>

<header class="topbar">
  <div class="wrap nav">
    <a href="/" class="logo"><span class="logo-mark"></span>MODU.TODAY</a>
    <nav class="menu">
      <a href="/">뉴스</a>
      <a href="/youtube/">YouTube 순위</a>
      <a href="/calculator/">계산기</a>
      <a href="/games/">게임</a>
      <a href="/lotto/">로또</a>
      <a href="/apt/">아파트 실거래가</a>
    </nav>
  </div>
</header>

<main>
  <section class="hero">
    <div class="wrap">
      <div class="hero-box">
        <span class="eyebrow">● 오늘 필요한 정보를 한곳에</span>
        <h1>오늘 뭐 볼까?<br>MODU.TODAY에서 한 번에.</h1>
        <p>하루 6번 갱신되는 증시·정책 뉴스부터 YouTube 순위, 생활 계산기, 무료 게임,<br>
        로또 당첨정보와 전국 아파트 실거래가까지 자주 찾는 정보를 한곳에 모았습니다.</p>

        <div class="quick">
          <a href="/"><span class="ico">📰</span><strong>증시·정책 뉴스</strong><small>하루 6번 실시간 업데이트</small></a>
          <a href="/youtube/"><span class="ico">📺</span><strong>YouTube 순위</strong><small>일·주·월 조회수 상승 추적</small></a>
          <a href="/calculator/"><span class="ico">🧮</span><strong>생활 계산기</strong><small>복잡한 계산을 쉽고 빠르게</small></a>
          <a href="/games/"><span class="ico">🎮</span><strong>무료 웹게임</strong><small>설치 없이 바로 플레이</small></a>
          <a href="/lotto/"><span class="ico">🍀</span><strong>로또 당첨정보</strong><small>당첨번호 · 당첨자수 · 당첨지역 · 행운 로또 번호 무료 생성</small></a>
          <a href="/apt/"><span class="ico">🏠</span><strong>아파트 실거래가</strong><small>전국 실제 거래가격 검색</small></a>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2>실시간 증시·정책 뉴스 정보 대시보드</h2>
          <p>하루 6번 업데이트 · 국내 증시와 주요 경제·정책 이슈를 한 화면에서 빠르게 확인하세요.</p>
        </div>
        <span class="more">최종 갱신 {today_str}</span>
      </div>

      <div class="news-live">
{news_content}
      </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap grid-2">
      <div>
        <div class="section-head">
          <div>
            <h2>YouTube 인기 순위</h2>
            <p>매일 누적한 조회수 변화를 기준으로 일간·주간·월간 상승 흐름을 확인하세요.</p>
          </div>
          <a class="more" href="/youtube/">순위 보기 →</a>
        </div>

        <div class="card yt-home-card">
          <div id="ytHomeRank" class="yt-home-grid">
            <div class="yt-loading">YouTube 최신 순위를 불러오는 중...</div>
          </div>
          <a href="/youtube/" class="yt-all">일간 · 주간 · 월간 전체 순위 보기 →</a>
        </div>
        <iframe id="ytRankBridge" src="/youtube/" title="YouTube 순위 데이터" tabindex="-1" aria-hidden="true"></iframe>
      </div>

      <div>
        <div class="section-head">
          <div>
            <h2>로또 당첨정보</h2>
            <p>최신 당첨번호부터 등수별 당첨자수, 당첨금, 1등 당첨지역·판매점, 자동·수동 여부와 행운 로또 번호 무료 생성까지 한 번에 확인하세요.</p>
          </div>
          <a class="more" href="/lotto/">상세보기 →</a>
        </div>

        <div class="card lotto">
          <div class="lotto-top">
            <div><h3>1239회 당첨번호</h3><small>2026.08.29 추첨</small></div>
            <strong>1등 13명</strong>
          </div>
          <div class="balls">
            <span class="ball">11</span><span class="ball">13</span><span class="ball">22</span>
            <span class="ball">32</span><span class="ball">33</span><span class="ball">36</span>
            <span class="ball bonus">8</span>
          </div>
          <div class="lotto-bottom"><span>1등 당첨금</span><strong>약 22.1억원</strong></div>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2>생활에 바로 쓰는 계산기</h2>
          <p>연봉·대출·주식·세금·퍼센트 등 자주 필요한 계산을 회원가입 없이 즉시 이용하세요.</p>
        </div>
        <a class="more" href="/calculator/">계산기 전체보기 →</a>
      </div>

      <div class="calc-thumb-grid">
        <a class="card calc-thumb" href="/calculator/salary/">
          <div class="calc-art">💼</div><div class="calc-body"><strong>연봉 실수령액 계산기</strong><span>세전 연봉에서 예상 월 실수령액을 빠르게 계산</span></div>
        </a>
        <a class="card calc-thumb" href="/calculator/stock-return/">
          <div class="calc-art">📈</div><div class="calc-body"><strong>주식 수익률 계산기</strong><span>매수가·매도가 기준 수익금과 수익률 계산</span></div>
        </a>
        <a class="card calc-thumb" href="/calculator/average-price/">
          <div class="calc-art">📊</div><div class="calc-body"><strong>주식 평단가 계산기</strong><span>추가매수 후 새로운 평균 매입단가 확인</span></div>
        </a>
        <a class="card calc-thumb" href="/calculator/loan/">
          <div class="calc-art">🏦</div><div class="calc-body"><strong>대출 계산기</strong><span>상환방식별 월 납입액과 총 이자 계산</span></div>
        </a>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2>아파트 실거래가</h2>
          <p>국토교통부 공개 데이터를 바탕으로 전국 아파트의 실제 거래가격과 최근 거래내역을 검색하세요.</p>
        </div>
        <a class="more" href="/apt/">아파트 실거래가 검색 →</a>
      </div>
      <a class="card apt-feature" href="/apt/">
        <div class="feature-art apt-art"><span>🏢</span><b>APT</b></div>
        <div class="feature-copy">
          <span class="feature-kicker">REAL TRANSACTION PRICE</span>
          <h3>우리 아파트, 실제로 얼마에 거래됐을까?</h3>
          <p>지역과 아파트명을 검색하면 최근 거래가격·거래일·면적·층 등 실거래 정보를 한눈에 확인할 수 있습니다.</p>
          <strong>전국 아파트 실거래가 확인하기 →</strong>
        </div>
      </a>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head">
        <div>
          <h2>무료 웹게임</h2>
          <p>설치나 회원가입 없이 PC와 모바일에서 바로 즐기세요.</p>
        </div>
        <a class="more" href="/games/">게임 전체보기 →</a>
      </div>
      <div class="game-home-grid">
        <a class="card game-home-card" href="/games/block-game/">
          <div class="game-art blocks-art">▦</div><div><strong>MODU BLOCKS</strong><span>블록을 쌓고 줄을 완성하는 퍼즐게임</span></div>
        </a>
        <a class="card game-home-card" href="/games/minesweeper/">
          <div class="game-art mine-art-home">💣</div><div><strong>지뢰찾기</strong><span>숫자를 단서로 지뢰를 찾아내는 클래식 퍼즐</span></div>
        </a>
        <a class="card game-home-card" href="/games/2048/">
          <div class="game-art n2048-art">2048</div><div><strong>2048</strong><span>같은 숫자를 합쳐 2048 타일에 도전</span></div>
        </a>
      </div>
    </div>
  </section>

</main>

<footer>
  <div class="wrap footer-box">
    <span>© MODU.TODAY · Jae-Hyun Kim.</span>
    <span>뉴스 · YouTube · 계산기 · 게임 · 로또 · 실거래가</span>
  </div>
</footer>

<div class="fixed-ticker" aria-label="실시간 뉴스 속보">
  <div class="label">실시간 뉴스</div>
  <div class="track"><div class="marquee">{ticker_html}</div></div>
</div>


</body>
</html>
""".format(news_content=news_content, today_str=today_str, ticker_html=ticker_html)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_template)

print("Successfully generated MODU.TODAY gradient homepage")
