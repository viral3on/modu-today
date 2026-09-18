"""Restore readable news cards, accurate homepage metadata and a sourced-data guide.

Run after update_news.py or on the SEO rebuild. The temporary KRX suspension
step subsequently removes the KRX-only guide; do not recreate old metadata.
"""
from pathlib import Path

HOME = Path(__file__).resolve().parent / "index.html"
CANONICAL = '<link rel="canonical" href="https://modu.today/">'
OLD_TITLE = '<title>MODU.TODAY</title>'
LEGACY_TITLE = '<title>MODU.TODAY | 국내 증시 스캐너·로또 기록·생활 계산기</title>'
NEW_TITLE = '<title>MODU.TODAY | 로또 기록·생활 계산기·웹게임</title>'
OLD_DESCRIPTION = '<meta name="description" content="증시 스캐너, 뉴스, YouTube 순위, 계산기, 게임, 로또, 아파트 실거래가를 한곳에서 확인하세요.">'
LEGACY_DESCRIPTION = '<meta name="description" content="KRX 일별 증시 데이터 스캐너와 지표 계산법, 로또 최근 100회 결과 및 과거 통계, 생활 계산기와 아파트 실거래가를 확인하세요. 뉴스는 외부 언론사의 원문 링크를 모아 제공합니다.">'
NEW_DESCRIPTION = '<meta name="description" content="로또 회차별 당첨 기록과 과거 통계, 생활 계산기, 웹게임, 아파트 실거래가와 외부 뉴스 원문 링크를 제공합니다. KRX 증시 스캐너는 데이터 이용 범위 확인을 위해 일시 중단 중입니다.">'
STYLE = '''
/* News feed fallback: update_news.py uses Tailwind class names, but home has no Tailwind CSS. */
.news-live .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.news-live .grid>a{display:block;min-width:0;padding:16px;border-radius:12px;
 background:#141a28;border:2px solid #eab308;color:#f9fafb;text-decoration:none}
.news-live .grid>a:hover{background:#1c2538}
.news-live .grid>a>div:first-child{display:flex;align-items:flex-start;justify-content:space-between;gap:8px}
.news-live .grid>a span{color:#f9fafb;font-size:14px;font-weight:700;line-height:1.5}
.news-live .grid>a span.text-yellow-400{color:#facc15}
.news-live .grid>a .text-gray-400{color:#cbd5e1;font-size:12px;margin-top:8px}
.news-live .grid>a .text-yellow-400\\/90{color:#facc15}
.news-live>div{min-width:0}
.news-live>div>h2{color:#172033;font-size:17px;margin:0 0 14px}
.fixed-ticker .marquee a{display:inline-block;margin:0 20px;color:#fef3c7;text-decoration:none}
@media(max-width:720px){.news-live .grid{grid-template-columns:1fr}}
'''
GUIDE = '''
  <section class="section" id="reading-guide">
    <div class="wrap">
      <div class="card" style="padding:24px 28px;line-height:1.8">
        <h2 style="margin:0 0 10px;font-size:22px">데이터를 읽기 전에</h2>
        <p style="margin:0 0 10px;color:#475467">뉴스 영역은 외부 언론사의 기사 제목과 원문 링크를 모아 보여줍니다. MODU.TODAY가 직접 취재하거나 기사 내용을 검증한 보도물이 아닙니다. 개별 사실과 보도 시점은 원문에서 확인해 주세요.</p>
        <p style="margin:0;color:#475467">증시 스캐너는 실시간 시세가 아닌 KRX 일별 데이터를 비교한 결과입니다. 거래량 배수, 신고가 판정, 자체 관심도의 <a href="/stock/guide/" style="color:#4f46e5;font-weight:800;text-decoration:underline">정확한 계산법과 해석상 한계</a>를 먼저 확인할 수 있습니다.</p>
      </div>
    </div>
  </section>
'''


def improve(text: str) -> str:
    if "</style>" not in text or "</head>" not in text or "<main>" not in text or '<section class="section">' not in text:
        raise ValueError("Unexpected homepage markup: nothing changed")
    if not any(title in text for title in (OLD_TITLE, LEGACY_TITLE, NEW_TITLE)):
        raise ValueError("Unknown homepage title; refusing to overwrite")
    if not any(description in text for description in (OLD_DESCRIPTION, LEGACY_DESCRIPTION, NEW_DESCRIPTION)):
        raise ValueError("Unknown homepage description; refusing to overwrite")
    text = text.replace(OLD_TITLE, NEW_TITLE, 1).replace(LEGACY_TITLE, NEW_TITLE, 1)
    text = text.replace(OLD_DESCRIPTION, NEW_DESCRIPTION, 1).replace(LEGACY_DESCRIPTION, NEW_DESCRIPTION, 1)
    if 'rel="canonical"' not in text:
        text = text.replace("</head>", CANONICAL + "\n</head>", 1)
    if "News feed fallback: update_news.py" not in text:
        text = text.replace("</style>", STYLE + "\n</style>", 1)
    if 'id="reading-guide"' not in text:
        text = text.replace('<section class="section">', GUIDE + '\n<section class="section">', 1)
    text = text.replace('오늘의 브리핑', '외부 기사')
    text = text.replace('aria-label="실시간 뉴스 속보"', 'aria-label="외부 언론 기사 제목 모음"')
    text = text.replace('<div class="label">실시간 뉴스</div>', '<div class="label">기사 모음</div>')
    text = text.replace('⚡ BREAKING', '기사 보기')
    return text

if __name__ == "__main__":
    original = HOME.read_text(encoding="utf-8")
    patched = improve(original)
    if original != patched:
        HOME.write_text(patched, encoding="utf-8")
    if (HOME.parent / 'KRX_PUBLIC_PAUSED').exists():
        from suspend_krx_public import apply as suspend
        suspend()
    print("Homepage readable news + descriptive metadata:", "updated" if original != patched else "already applied")
