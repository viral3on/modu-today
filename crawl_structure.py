"""Generate visible crawl links, preserving existing cards and theme classes."""
import re
from html import escape
from seo_catalog import ROOT, BASE_URL, Metadata, calculators, related, pages, exclusion, html_to_url


def label(meta):
    return meta.title.split("|")[0].split(" - MODU")[0].strip()


def link(path, meta):
    return f'<a href="{html_to_url(path)[len(BASE_URL):]}">{escape(label(meta))} →</a>'


def write(path, text):
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def insert(path, content):
    text = path.read_text(encoding="utf-8")
    start, end = "<!-- CRAWL_LINKS_START -->", "<!-- CRAWL_LINKS_END -->"
    block = start + content + end
    if start in text:
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)
    else:
        pos = text.lower().rfind("<footer")
        if pos < 0:
            pos = text.lower().rfind("</body>")
        if pos < 0:
            raise ValueError(f"Missing insertion point: {path}")
        text = text[:pos] + block + text[pos:]
    write(path, text)


def main():
    catalog = calculators()
    hub = ROOT / "calculator/index.html"
    text = hub.read_text(encoding="utf-8")
    match = re.search(r'(<section class="calc-grid">)(.*?)(</section>)', text, re.S)
    if not match:
        raise ValueError("Calculator card grid missing")
    cards = re.findall(r'<a\b[^>]*class="calc-card".*?</a>', match[2], re.S)
    eligible = {html_to_url(p)[len(BASE_URL):] for p, _ in catalog}
    cards = [c for c in cards if Metadata(c).links[0] in eligible]
    existing = {Metadata(c).links[0] for c in cards}
    for path, meta in catalog:
        url = html_to_url(path)[len(BASE_URL):]
        if url not in existing:
            cards.append(f'<a class="calc-card" href="{url}"><div class="calc-card-art">🧮</div>'
                         f'<div class="calc-card-body"><span class="calc-tag">계산 도구</span>'
                         f'<h2>{escape(label(meta))}</h2><p>{escape(meta.description)}</p>'
                         '<span class="calc-go">계산하기 →</span></div></a>')
    text = text[:match.start(2)] + "\n" + "".join(cards) + text[match.end(2):]
    text = re.sub(r'계산기 \d+종', f'계산기 {len(catalog)}종', text)
    text = re.sub(r'총 \d+개의 계산기', f'총 {len(catalog)}개의 계산기', text)
    write(hub, text)
    for path, meta in catalog:
        links = "".join(link(p, m) for p, m in related(path, catalog))
        insert(path, '<section class="modu-related" data-static-related="1">'
               '<h2>함께 많이 사용하는 계산기</h2><div class="modu-related-grid">' + links +
               '</div><p><a href="/calculator/">계산기 전체보기</a></p></section>')

    game_pages = [(p, m) for p, m in pages() if p.parent.parent == ROOT / "games"
                  and p.name == "index.html" and not exclusion(p, m)]
    for path, _ in game_pages:
        insert(path, '<nav aria-label="관련 게임"><p><a href="/games/">게임 전체보기</a> · ' +
               " · ".join(link(p, m) for p, m in game_pages if p != path) + '</p></nav>')
    game_hub = ROOT / "games/index.html"
    # Existing game cards are already static. Only newly discovered games need fallback links.
    original = re.sub(r'<!-- CRAWL_LINKS_START -->.*?<!-- CRAWL_LINKS_END -->', '',
                      game_hub.read_text(encoding="utf-8"), flags=re.S)
    missing = [(p, m) for p, m in game_pages if html_to_url(p)[len(BASE_URL):] not in Metadata(original).links]
    if missing or '<!-- CRAWL_LINKS_START -->' in game_hub.read_text(encoding="utf-8"):
        insert(game_hub, '<nav aria-label="추가 게임">' + " · ".join(link(p, m) for p, m in missing) + '</nav>')

    for name, slugs in {"stock": ["stock-return", "average-price", "dividend"],
                        "apt": ["realtor", "registration-tax", "area"]}.items():
        selected = [(p, m) for p, m in catalog if p.stem in slugs]
        insert(ROOT / name / "index.html", '<nav class="seo-static-links" aria-label="관련 계산기"><p>' +
               " · ".join(link(p, m) for p, m in selected) + '</p></nav>')
    inventory = ['# URL 분류 목록', '', '자동 생성: crawl_structure.py. 분류 근거는 crawl-policy.md 참고.', '',
                 '| URL | 분류 | 사이트맵 | 비고 |', '|---|---|---|---|']
    detail_paths = {p for p, _ in catalog + game_pages}
    for path, meta in pages():
        rel = path.relative_to(ROOT)
        reason = exclusion(path, meta)
        if reason == 'verification file':
            category, note = '보호', '인증 파일 수정 금지'
        elif path in detail_paths:
            category, note = '①', '검색 의도가 명확한 계산/게임 도구'
        elif (len(rel.parts) == 3 and rel.parts[0] == 'lotto' and rel.parts[1].isdigit()) or reason:
            category, note = '③', reason or '고유 회차 데이터: 기록 허브에 연결된 회차 유지'
        else:
            category, note = '②', '서비스/탐색/신뢰 정보'
        inventory.append(f'| {html_to_url(path)} | {category} | {"제외" if reason else "포함"} | {note} |')
    (ROOT / 'docs').mkdir(exist_ok=True)
    write(ROOT / 'docs/url-inventory.md', '\n'.join(inventory) + '\n')
    print(f"Crawl links: {len(catalog)} calculators, {len(game_pages)} games")


if __name__ == "__main__":
    main()
