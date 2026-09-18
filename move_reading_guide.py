"""Keep the market-reading guide immediately below the homepage stock scanner.

The news build regenerates index.html, so this runs after the existing quality and
market-brief scripts on every scheduled update. No news or stock data is changed.
"""
from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen
import sys
import time

HOME = Path(__file__).resolve().parent / 'index.html'
GUIDE = '<section class="section" id="reading-guide">'
STOCK_HEADING = '<h2>KRX 증시 조건검색 스캐너</h2>'
YOUTUBE_HEADING = '<h2>YouTube 인기 순위</h2>'


def positions(text: str):
    if text.count(GUIDE) != 1 or text.count(STOCK_HEADING) != 1 or text.count(YOUTUBE_HEADING) != 1:
        raise ValueError('Missing or duplicated homepage guide/section markers')
    guide_start = text.index(GUIDE)
    guide_end = text.find('</section>', guide_start)
    stock_heading = text.index(STOCK_HEADING)
    stock_end = text.find('</section>', stock_heading)
    youtube_heading = text.index(YOUTUBE_HEADING)
    if guide_end < 0 or stock_end < 0 or not stock_heading < youtube_heading:
        raise ValueError('Unexpected homepage section structure')
    return guide_start, guide_end + len('</section>'), stock_heading, stock_end + len('</section>'), youtube_heading


def move(text: str) -> str:
    guide_start, guide_end, _, stock_end, youtube_heading = positions(text)
    guide = text[guide_start:guide_end].replace('아래 뉴스는', '상단 뉴스는')
    if stock_end <= guide_start < youtube_heading:
        return text[:guide_start] + guide + text[guide_end:]
    without = text[:guide_start] + text[guide_end:]
    _, _, _, new_stock_end, _ = positions_without_guide(without)
    result = without[:new_stock_end] + '\n\n  ' + guide + '\n' + without[new_stock_end:]
    verify(result)
    return result


def positions_without_guide(text: str):
    stock_heading = text.index(STOCK_HEADING)
    stock_end = text.find('</section>', stock_heading)
    youtube_heading = text.index(YOUTUBE_HEADING)
    if stock_end < 0 or not stock_heading < stock_end < youtube_heading:
        raise ValueError('Cannot locate scanner section boundary')
    return None, None, stock_heading, stock_end + len('</section>'), youtube_heading


def verify(text: str) -> None:
    guide_start, _, stock_heading, stock_end, youtube_heading = positions(text)
    if not stock_heading < stock_end < guide_start < youtube_heading:
        raise AssertionError('Market guide is not below the complete scanner section')
    if text.count('id="reading-guide"') != 1:
        raise AssertionError('Duplicate reading guide')


def check_live() -> None:
    last = None
    for attempt in range(10):
        try:
            req = Request('https://modu.today/', headers={'Cache-Control': 'no-cache', 'User-Agent': 'MODU-layout-check/1.0'})
            with urlopen(req, timeout=20) as response:
                if response.status != 200:
                    raise AssertionError(f'Unexpected HTTP {response.status}')
                html = response.read().decode('utf-8', errors='replace')
            verify(html)
            print('LIVE OK: scanner section → market-reading guide → YouTube section')
            return
        except (OSError, ValueError, AssertionError) as exc:
            last = exc
            if attempt < 9:
                time.sleep(8)
    raise RuntimeError(f'Live homepage placement not verified: {last}')


def main():
    if '--check-live' in sys.argv:
        check_live()
        return
    before = HOME.read_text(encoding='utf-8')
    after = move(before)
    verify(after)
    assert move(after) == after, 'The guide mover must be idempotent'
    if before != after:
        HOME.write_text(after, encoding='utf-8')
    print('Homepage guide placed below KRX stock scanner:', 'updated' if before != after else 'already correct')


if __name__ == '__main__':
    main()
