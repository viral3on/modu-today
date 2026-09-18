"""Keep four unobtrusive site-information links unique after HTML rebuilds.

Run after news, lotto, and SEO generators. Reuse any existing footer links;
replace previously injected dark navigation without touching unrelated content.
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
    r'\n[ \t]*' + re.escape(START) + r'.*?' + re.escape(END) + r'[ \t]*\n?', re.S
)
FOOTER_BLOCK = re.compile(r'<footer\b[^>]*>.*?</footer\s*>', re.I | re.S)
FOOTER_CLOSE = re.compile(r'</footer\s*>', re.I)
BODY_END = re.compile(r'</body\s*>\s*</html\s*>\s*\Z', re.I)
INFO_LINK = re.compile(
    r'<a\b[^>]*\bhref\s*=\s*[\'\"](?P<href>/(?:about|contact|privacy|terms)/)[\'\"][^>]*>.*?</a>',
    re.I | re.S,
)
SKIP_DIRS = {'.git', '.github', 'docs', 'tests', 'node_modules', '.venv', 'venv'}


def published_pages(root=ROOT):
    for page in sorted(root.rglob('*.html')):
        relative = page.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts[:-1]):
            continue
        if len(relative.parts) == 1 and relative.name.lower().startswith(('google', 'naver')):
            continue
        yield page


def link_row(links):
    """Quiet text links, without a banner, border, pill, or background."""
    return (START + '\n'
            '<nav aria-label="사이트 안내 및 문의" '
            'style="box-sizing:border-box;max-width:980px;margin:8px auto 0;'
            'padding:2px 8px;display:flex;flex-wrap:wrap;justify-content:center;'
            'align-items:center;gap:4px 14px;'
            'font:400 12px/1.7 Arial,\'Noto Sans KR\',sans-serif">\n'
            + '\n'.join(
                f'  <a href="{href}" style="color:#8190a5;text-decoration:underline;'
                f'text-underline-offset:2px;white-space:nowrap">{label}</a>'
                for href, label in links
            )
            + '\n</nav>\n' + END)


def adjacent_native_links(footer):
    matches = list(INFO_LINK.finditer(footer))
    return (len(matches) >= 2 and all(
        re.fullmatch(r'\s*(?:·\s*)?', footer[a.end():b.start()])
        for a, b in zip(matches, matches[1:])
    ))


def normalize_native_links(footer):
    """Replace only a contiguous cluster of footer links; preserve other HTML."""
    if not adjacent_native_links(footer):
        return footer, False
    matches = list(INFO_LINK.finditer(footer))
    canonical = ' · '.join(f'<a href="{href}">{label}</a>' for href, label in LINKS)
    footer = footer[:matches[0].start()] + canonical + footer[matches[-1].end():]
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
        if START in html:
            return MARKED.sub(lambda _: link_row(LINKS), html, count=1)
        return html[:body.start()] + '\n<footer>\n' + link_row(LINKS) + '\n</footer>\n' + html[body.start():]

    match = footers[-1]
    footer = match.group()
    if START in html and START not in footer:
        raise ValueError('Site navigation marker is outside the last footer')
    without_nav = MARKED.sub('', footer, count=1)
    native_before = [m.group('href') for m in INFO_LINK.finditer(without_nav)]

    # Keep the exact whitespace/position of an existing marked navigation if
    # there is no native info-link cluster to consolidate. This also makes a
    # second run byte-for-byte identical to the first.
    if START in footer and not adjacent_native_links(without_nav):
        missing = [(href, label) for href, label in LINKS if href not in native_before]
        if missing:
            return html[:match.start()] + MARKED.sub(
                lambda _: link_row(missing), footer, count=1
            ) + html[match.end():]
        return html[:match.start()] + REMOVE_MARKED_LINE.sub(
            '\n', footer, count=1
        ) + html[match.end():]

    stripped = REMOVE_MARKED_LINE.sub('\n', footer, count=1)
    if START in stripped:
        stripped = MARKED.sub('', stripped, count=1)
    normalized, consolidated = normalize_native_links(stripped)
    native = [m.group('href') for m in INFO_LINK.finditer(normalized)]
    if consolidated or (len(native) == len(LINKS) and len(set(native)) == len(LINKS)):
        new_footer = normalized
    else:
        missing = [(href, label) for href, label in LINKS if href not in native]
        if not missing:
            new_footer = normalized
        else:
            end = list(FOOTER_CLOSE.finditer(normalized))[-1]
            new_footer = (normalized[:end.start()] + '\n' + link_row(missing)
                          + '\n' + normalized[end.start():])
    return html[:match.start()] + new_footer + html[match.end():]


def check(html):
    footers = list(FOOTER_BLOCK.finditer(html))
    if not footers:
        raise ValueError('Footer missing')
    footer = footers[-1].group()
    if html.count(START) != html.count(END) or html.count(START) > 1:
        raise ValueError('Broken or duplicated navigation markers')
    if 'background:#112a44' in footer or 'border:1px solid #35516d' in footer:
        raise ValueError('Old dark navigation banner still present')
    hrefs = [m.group('href') for m in INFO_LINK.finditer(footer)]
    if sorted(hrefs) != sorted(href for href, _ in LINKS):
        raise ValueError('Footer must contain each information link exactly once')


def test():
    generic = '<html><body><main>기능</main><footer>기존 안내</footer></body></html>'
    homepage = ('<html><body><main>뉴스</main><footer><div class="footer-box">'
                '<span>© MODU</span><span>뉴스 · 계산기</span></div></footer></body></html>')
    contact = ('<html><body><main>문의</main><footer>© MODU · '
               '<a href="/about/">소개</a> · <a href="/privacy/">개인정보처리방침</a> · '
               '<a href="/terms/">이용안내</a></footer></body></html>')
    already = ('<html><body><footer>© MODU · '
               + ' · '.join(f'<a href="{href}">{name}</a>' for href, name in LINKS)
               + '</footer></body></html>')
    nofooter = '<html><body><main>게임</main></body></html>'
    for sample in (generic, homepage, contact, already, nofooter):
        once = apply(sample)
        check(once)
        assert apply(once) == once, 'Footer transformation must be idempotent'
        assert '<main>' not in sample or sample[sample.index('<main>'):sample.index('</main>')+7] in once
    assert START not in apply(contact), 'Native footer must not grow another row'
    assert 'background:#112a44' not in apply(generic)
    old_band = link_row(LINKS).replace('padding:2px 8px;', 'padding:15px 16px;background:#112a44;')
    old_contact = contact.replace('</footer>', '\n' + old_band + '\n</footer>')
    assert apply(old_contact) == apply(contact), 'Old band must disappear without duplicates'
    assert apply(apply(old_contact)) == apply(contact)
    try:
        apply('<html><body>' + START + '</body></html>')
    except ValueError:
        pass
    else:
        raise AssertionError('Unbalanced markers must fail safely')
    print('Site footer fixture tests passed (native, old band, home, fallback, idempotence)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Verify four unique links per page')
    parser.add_argument('--test', action='store_true', help='Run deterministic regression fixtures')
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
