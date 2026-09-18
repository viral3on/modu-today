"""Maintain understated, nonduplicated information links on generated site pages.

Run after news, lotto, and SEO generators; never alter application JS or content.
"""
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parent
START = '<!-- MODU_SITE_LINKS_START -->'
END = '<!-- MODU_SITE_LINKS_END -->'
LINKS = (('/about/', '소개'), ('/contact/', '문의'),
         ('/privacy/', '개인정보처리방침'), ('/terms/', '이용안내'))
MARKED = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)
REMOVE_MARKED_LINE = re.compile(
    r'\n[ \t]*' + re.escape(START) + r'.*?' + re.escape(END) + r'[ \t]*\n?', re.S)
FOOTER_BLOCK = re.compile(r'<footer\b[^>]*>.*?</footer\s*>', re.I | re.S)
FOOTER_CLOSE = re.compile(r'</footer\s*>', re.I)
VISUAL_FOOTER = re.compile(r'<div\s+class=[\'\"]footer[\'\"]\s*>(?P<body>.*?)</div\s*>', re.I | re.S)
BODY_END = re.compile(r'</body\s*>\s*</html\s*>\s*\Z', re.I)
INFO_LINK = re.compile(
    r'<a\b[^>]*\bhref\s*=\s*[\'\"](?P<href>/(?:about|contact|privacy|terms)/)[\'\"][^>]*>.*?</a>',
    re.I | re.S)
SKIP_DIRS = {'.git', '.github', 'docs', 'tests', 'node_modules', '.venv', 'venv'}


def published_pages(root=ROOT):
    for page in sorted(root.rglob('*.html')):
        rel = page.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if len(rel.parts) == 1 and rel.name.lower().startswith(('google', 'naver')):
            continue
        yield page


def link_row(links):
    """Small, muted inline links without background, border, or pill buttons."""
    return (START + '\n'
            '<nav aria-label="사이트 안내 및 문의" '
            'style="box-sizing:border-box;max-width:980px;margin:8px auto 0;'
            'padding:2px 8px;display:flex;flex-wrap:wrap;justify-content:center;'
            'align-items:center;gap:4px 14px;'
            'font:400 12px/1.7 Arial,\'Noto Sans KR\',sans-serif">\n'
            + '\n'.join(
                f'  <a href="{href}" style="color:#8190a5;text-decoration:underline;'
                f'text-underline-offset:2px;white-space:nowrap">{label}</a>'
                for href, label in links)
            + '\n</nav>\n' + END)


def native_hrefs(footer):
    return [m.group('href') for m in INFO_LINK.finditer(footer)]


def contiguous(footer):
    hits = list(INFO_LINK.finditer(footer))
    return len(hits) >= 2 and all(
        re.fullmatch(r'\s*(?:·\s*)?', footer[a.end():b.start()])
        for a, b in zip(hits, hits[1:]))


def normalize_native(footer):
    """Only consolidate adjacent native footer links, preserving other markup."""
    if not contiguous(footer):
        return footer, False
    hits = list(INFO_LINK.finditer(footer))
    canonical = ' · '.join(f'<a href="{href}">{label}</a>' for href, label in LINKS)
    footer = footer[:hits[0].start()] + canonical + footer[hits[-1].end():]
    footer = re.sub(r'[ \t\r\n]+(?=</footer\s*>)', '', footer, count=1, flags=re.I)
    return footer, True


def apply(html):
    if html.count(START) != html.count(END) or html.count(START) > 1:
        raise ValueError('Invalid site-link markers; refusing to modify page')
    body = BODY_END.search(html)
    if not body:
        raise ValueError('Missing final </body></html>; refusing to modify page')
    footers = list(FOOTER_BLOCK.finditer(html, 0, body.start()))
    if not footers:
        # The block game has a native <div class="footer"> inside its app.
        # Move the formerly outside-the-app navigation INTO that container,
        # giving it semantic footer markup without shifting the game layout.
        clean = REMOVE_MARKED_LINE.sub('\n', html, count=1)
        visual = VISUAL_FOOTER.search(clean, 0, BODY_END.search(clean).start())
        if visual:
            replacement = ('<footer class="footer">' + visual.group('body')
                           + '\n' + link_row(LINKS) + '\n</footer>')
            return clean[:visual.start()] + replacement + clean[visual.end():]
        if START in clean:
            raise ValueError('Unexpected marker placement outside a footer')
        end = BODY_END.search(clean)
        return clean[:end.start()] + '\n<footer>\n' + link_row(LINKS) + '\n</footer>\n' + clean[end.start():]

    match = footers[-1]
    footer = match.group()
    if START in html and START not in footer:
        raise ValueError('Site navigation marker is outside the last footer')
    base = MARKED.sub('', footer, count=1)
    present = native_hrefs(base)
    # Replacing an existing marked block in place avoids adding whitespace on
    # each generator run and guarantees byte-for-byte idempotence.
    if START in footer and not contiguous(base):
        missing = [(href, label) for href, label in LINKS if href not in present]
        new = (MARKED.sub(lambda _: link_row(missing), footer, count=1)
               if missing else REMOVE_MARKED_LINE.sub('\n', footer, count=1))
        return html[:match.start()] + new + html[match.end():]

    bare = REMOVE_MARKED_LINE.sub('\n', footer, count=1)
    bare, grouped = normalize_native(bare)
    present = native_hrefs(bare)
    if grouped or sorted(present) == sorted(href for href, _ in LINKS):
        new = bare
    else:
        missing = [(href, label) for href, label in LINKS if href not in present]
        if not missing:
            new = bare
        else:
            closing = list(FOOTER_CLOSE.finditer(bare))[-1]
            new = bare[:closing.start()] + '\n' + link_row(missing) + '\n' + bare[closing.start():]
    return html[:match.start()] + new + html[match.end():]


def check(html):
    footers = list(FOOTER_BLOCK.finditer(html))
    if not footers:
        raise ValueError('Footer missing')
    footer = footers[-1].group()
    if html.count(START) != html.count(END) or html.count(START) > 1:
        raise ValueError('Broken or duplicated navigation markers')
    if 'background:#112a44' in footer or 'border:1px solid #35516d' in footer:
        raise ValueError('Old dark navigation banner still present')
    if sorted(native_hrefs(footer)) != sorted(href for href, _ in LINKS):
        raise ValueError('Footer must contain each information link exactly once')


def test():
    samples = (
        '<html><body><main>기능</main><footer>기존 안내</footer></body></html>',
        '<html><body><main>뉴스</main><footer><div class="footer-box"><span>© MODU</span><span>뉴스 · 계산기</span></div></footer></body></html>',
        '<html><body><main>문의</main><footer>© MODU · <a href="/about/">소개</a> · <a href="/privacy/">개인정보처리방침</a> · <a href="/terms/">이용안내</a></footer></body></html>',
        '<html><body><footer>© MODU · ' + ' · '.join(f'<a href="{href}">{name}</a>' for href, name in LINKS) + '</footer></body></html>',
        '<html><body><main>게임</main></body></html>',
        '<html><body><div id="app"><div class="footer">© MODU BLOCKS</div></div><script>const game=1;</script></body></html>',
    )
    for sample in samples:
        result = apply(sample)
        check(result)
        assert apply(result) == result, 'Footer transformation must be idempotent'
        assert '<main>' not in sample or sample[sample.index('<main>'):sample.index('</main>')+7] in result
    native = samples[2]
    assert START not in apply(native), 'Do not add a second row on info pages'
    old_band = link_row(LINKS).replace('padding:2px 8px;', 'padding:15px 16px;background:#112a44;')
    old_native = native.replace('</footer>', '\n' + old_band + '\n</footer>')
    assert apply(old_native) == apply(native)
    old_game = samples[5].replace('</body>', '\n' + old_band + '\n</body>')
    fixed_game = apply(old_game)
    check(fixed_game)
    assert '<footer class="footer">' in fixed_game and '</script>' in fixed_game
    assert apply(fixed_game) == fixed_game
    try:
        apply('<html><body>' + START + '</body></html>')
    except ValueError:
        pass
    else:
        raise AssertionError('Unbalanced markers must fail safely')
    print('Footer tests passed: native links, duplicate removal, games, idempotence')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    if args.test:
        test()
        return
    pages = list(published_pages())
    if not pages:
        raise RuntimeError('No published HTML pages found')
    changed = 0
    for page in pages:
        old = page.read_text(encoding='utf-8')
        if args.check:
            try:
                check(old)
            except ValueError as exc:
                raise ValueError(f'{page.relative_to(ROOT)}: {exc}') from exc
        else:
            new = apply(old)
            if new != old:
                page.write_text(new, encoding='utf-8')
                changed += 1
    print(f'Site footer: {len(pages)} HTML pages checked, {changed} updated')


if __name__ == '__main__':
    main()
