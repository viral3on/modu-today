"""Static, non-policy audit for MODU.TODAY. Never modifies published pages."""
from __future__ import annotations
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / 'docs' / 'content-audit.md'
SKIP_DIRS = {'.git', '.github', 'node_modules', 'tests', '__pycache__', '.vercel'}

class Page(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=True)
        self.ignored = 0
        self.title = ''
        self.description = ''
        self.canonical = ''
        self.robots = ''
        self.links: list[str] = []
        self.text: list[str] = []
        self.paragraphs: list[str] = []
        self._p: list[str] | None = None
        self._title = False
        self.feed(source)
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in ('script', 'style', 'svg', 'template'):
            self.ignored += 1
        if self.ignored:
            return
        if tag == 'title': self._title = True
        if tag == 'p': self._p = []
        if tag == 'a' and attrs.get('href'): self.links.append(attrs['href'])
        if tag == 'meta':
            if attrs.get('name', '').lower() == 'description': self.description = attrs.get('content', '')
            if attrs.get('name', '').lower() == 'robots': self.robots = attrs.get('content', '')
        if tag == 'link' and 'canonical' in attrs.get('rel', '').split(): self.canonical = attrs.get('href', '')
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'svg', 'template') and self.ignored: self.ignored -= 1
        if self.ignored: return
        if tag == 'title': self._title = False
        if tag == 'p' and self._p is not None:
            s = re.sub(r'\s+', ' ', ' '.join(self._p)).strip()
            if s: self.paragraphs.append(s)
            self._p = None
    def handle_data(self, data):
        if self.ignored: return
        s = data.strip()
        if s:
            if self._title: self.title += s
            else: self.text.append(s)
            if self._p is not None: self._p.append(s)

def pages(root=ROOT):
    for path in root.rglob('*.html'):
        if not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            yield path

def resolve_link(href: str, root=ROOT):
    parts = urlparse(href)
    if parts.scheme in ('mailto', 'tel', 'javascript') or href.startswith('#'):
        return None
    if parts.netloc and parts.netloc not in {'modu.today', 'www.modu.today'}:
        return None
    if not href.startswith('/') and not parts.netloc:
        return None
    name = unquote(parts.path)
    if name.startswith(('/api/', '/_vercel/')): return None
    if name in ('', '/'): return root / 'index.html'
    path = root / name.lstrip('/')
    if path.is_dir() or name.endswith('/'): return path / 'index.html'
    return path

def audit(root=ROOT):
    files = list(pages(root))
    stats = Counter()
    issues = []
    descriptions = {}
    per_area = Counter()
    for file in files:
        rel = file.relative_to(root).as_posix()
        area = rel.split('/')[0] if '/' in rel else 'root'
        per_area[area] += 1
        page = Page(file.read_text(encoding='utf-8', errors='replace'))
        visible = len(' '.join(page.text))
        meaningful = sum(len(p) >= 55 for p in page.paragraphs)
        if rel.startswith('lotto/') and re.fullmatch(r'lotto/\d+/index.html', rel):
            stats['lotto_draw_pages'] += 1
        else:
            if visible < 300 and 'noindex' not in page.robots:
                issues.append((rel, '본문 텍스트 300자 미만', str(visible)))
            if meaningful < 2 and 'noindex' not in page.robots:
                issues.append((rel, '충분한 길이의 설명 문단 2개 미만', str(meaningful)))
        if not page.title: issues.append((rel, 'title 누락', ''))
        if not page.description and not rel.startswith(('google','naver')):
            issues.append((rel, 'meta description 누락', ''))
        if page.description:
            descriptions.setdefault(page.description, []).append(rel)
        if page.canonical and not page.canonical.startswith('https://modu.today/'):
            issues.append((rel, 'canonical 도메인/주소 검토', page.canonical[:100]))
        if 'noindex' in page.robots: stats['noindex_pages'] += 1
        for href in page.links:
            target = resolve_link(href, root)
            if target is not None and not target.exists():
                issues.append((rel, '내부 링크 대상 파일 없음', href[:120]))
        stats['total_html'] += 1
    for description, paths in descriptions.items():
        if len(paths) > 1:
            for path in paths[:5]: issues.append((path, 'description 중복', f'{len(paths)}개 페이지'))
    stats['issues'] = len(issues)
    return stats, per_area, issues

def main():
    stats, areas, issues = audit()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines = ['# 사이트 콘텐츠 정적 점검', '', '저장소 HTML의 구조적 점검입니다. 구글 심사 결과, 실제 브라우저 표시, 검색 색인 상태 또는 정책 위반 판정이 아닙니다.', '',
             f"- 공개 HTML 후보: {stats['total_html']}개", f"- 로또 회차 기록: {stats['lotto_draw_pages']}개", f"- noindex: {stats['noindex_pages']}개", f"- 구조상 점검 항목: {stats['issues']}건", '',
             '## 영역별 HTML 파일', '', '| 영역 | 파일 수 |', '|---|---:|']
    lines.extend(f'| `{a}` | {n} |' for a, n in sorted(areas.items()))
    lines += ['', '## 점검 항목 (최대 150건 표시)', '', '| 파일 | 항목 | 내용 |', '|---|---|---|']
    lines.extend(f"| `{f.replace('|','')}` | {kind.replace('|','')} | {detail.replace('|','/')} |" for f,kind,detail in issues[:150])
    if len(issues)>150: lines += ['', f'나머지 {len(issues)-150}건은 스크립트를 로컬 실행하여 확인하세요.']
    lines += ['', '## 수동 확인', '', 'Search Console 실제 렌더링/색인, 애드센스 세부 사유, 모바일 UI, 데이터 갱신 실패, 원본 데이터의 정확성·사용권은 별도로 확인해야 합니다.', '']
    OUTPUT.write_text('\n'.join(lines), encoding='utf-8')
    print(f"HTML={stats['total_html']} lotto={stats['lotto_draw_pages']} issues={stats['issues']} report={OUTPUT}")

if __name__ == '__main__':
    main()
