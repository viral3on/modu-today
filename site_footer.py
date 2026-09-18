"""Keep visitor-facing site information links reachable on every published HTML page.

Run after generators (news, lotto, and static SEO) because they rebuild HTML.
Only inserts our own marked navigation; preserves existing page content and footer.
"""
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parent
START = '<!-- MODU_SITE_LINKS_START -->'
END = '<!-- MODU_SITE_LINKS_END -->'
LINKS = (
    ('/about/', '소개'),
    ('/contact/', '문의'),
    ('/privacy/', '개인정보처리방침'),
    ('/terms/', '이용안내'),
)
NAV = (
    START + '\n'
    '<nav aria-label="사이트 안내 및 문의" '
    'style="box-sizing:border-box;max-width:980px;margin:18px auto 0;padding:15px 16px;'
    'border:1px solid #35516d;border-radius:12px;background:#112a44;'
    'display:flex;flex-wrap:wrap;justify-content:center;align-items:center;'
    'gap:9px 18px;font:600 13px/1.65 Arial,\'Noto Sans KR\',sans-serif">\n'
    + '\n'.join(
        f'  <a href="{href}" style="color:#f1f5f9;text-decoration:underline;'
        f'text-underline-offset:3px;white-space:nowrap">{label}</a>'
        for href, label in LINKS
    )
    + '\n</nav>\n' + END
)
MARKED = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)
FOOTER_END = re.compile(r'</footer\s*>', re.I)
BODY_END = re.compile(r'</body\s*>\s*</html\s*>\s*\Z', re.I)
SKIP_DIRS = {'.git', '.github', 'docs', 'tests', 'node_modules', '.venv', 'venv'}


def published_pages(root=ROOT):
    """Published HTML only; never touch verification tokens or test fixtures."""
    for page in sorted(root.rglob('*.html')):
        relative = page.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts[:-1]):
            continue
        if len(relative.parts) == 1 and relative.name.lower().startswith(('google', 'naver')):
            continue
        yield page


def apply(html):
    if html.count(START) != html.count(END) or html.count(START) > 1:
        raise ValueError('Invalid site-link markers; refusing to modify page')
    if START in html:
        return MARKED.sub(lambda _match: NAV, html, count=1)
    body = BODY_END.search(html)
    if not body:
        raise ValueError('Missing final </body></html>; refusing to modify page')
    footers = [m for m in FOOTER_END.finditer(html, 0, body.start())]
    pos = footers[-1].start() if footers else body.start()
    return html[:pos] + '\n' + NAV + '\n' + html[pos:]


def test():
    cases = [
        '<html><body><main>기능</main><footer>기존 안내</footer></body></html>',
        '<html><body><main>기능</main></body></html>',
        '<html><body><script>const x="</footer>";</script><footer>real</footer></body></html>',
    ]
    for sample in cases:
        once = apply(sample)
        assert apply(once) == once
        assert once.count(START) == once.count(END) == 1
        assert once.count('<nav aria-label="사이트 안내 및 문의"') == 1
        assert all(once.count('href="' + href + '"') == 1 for href, _ in LINKS)
        assert once.find(START) < once.lower().rfind('</body>')
        assert '<main>기능</main>' in once
    try:
        apply('<html><body>' + START + '</body></html>')
    except ValueError:
        pass
    else:
        raise AssertionError('Missing marker end must fail safely')
    print('Site footer fixture tests passed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Verify every published page has four links')
    parser.add_argument('--test', action='store_true', help='Run small deterministic regression fixtures')
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
            if old.count(START) != 1 or old.count(END) != 1:
                raise ValueError(f'{page.relative_to(ROOT)}: missing site footer')
            block = MARKED.search(old)
            if not block or any(f'href="{href}"' not in block.group() for href, _ in LINKS):
                raise ValueError(f'{page.relative_to(ROOT)}: missing one or more site links')
        else:
            new = apply(old)
            if new != old:
                page.write_text(new, encoding='utf-8')
                changed += 1
    print(f'Site footer: {len(pages)} HTML pages checked, {changed} updated')


if __name__ == '__main__':
    main()
