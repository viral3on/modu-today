"""Temporarily suspend public KRX displays pending clarification of data-use rights.

This is reversible from Git history. Never restore KRX API results while the
KRX_PUBLIC_PAUSED marker exists. Keep the remaining public services intact.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FLAG = ROOT / "KRX_PUBLIC_PAUSED"
HOME = ROOT / "index.html"
STOCK = ROOT / "stock/index.html"
GUIDE = ROOT / "stock/guide/index.html"

MAINTENANCE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,follow"><title>증시 스캐너 일시 중단 | MODU.TODAY</title>
<style>body{margin:0;background:#f6f8fc;color:#182334;font-family:Arial,'Noto Sans KR',sans-serif}.wrap{max-width:720px;margin:12vh auto;padding:0 20px}.box{padding:32px;border:1px solid #e2e8f0;border-radius:20px;background:#fff;line-height:1.8}a{color:#3459a8}h1{font-size:27px}</style></head><body>
<main class="wrap"><div class="box"><h1>증시 스캐너 일시 중단</h1><p>KRX 데이터 이용 범위를 확인하는 동안 증시 스캐너와 관련 데이터 제공을 잠시 중단합니다. 기존의 시장 수치 및 검색 결과를 제공하지 않습니다.</p><p>다른 서비스는 계속 이용할 수 있습니다. <a href="/">MODU.TODAY 홈으로 이동</a> · <a href="/contact/">문의하기</a></p></div></main>
</body></html>
"""


def replace_one(text: str, pattern: str, replacement: str, *, required: bool = False) -> str:
    output, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if required and count != 1:
        raise ValueError("KRX suspension failed to find expected homepage element: " + pattern[:75])
    return output


def home_paused(text: str) -> str:
    # Strip the dynamically displayed scanner and KRX-specific editorial panels.
    text = replace_one(text, r'\s*<section class="section" id="reading-guide">.*?</section>', '')
    text = replace_one(text, r'\s*<section class="section">\s*<div class="wrap">\s*<div class="section-head">\s*<div>\s*<h2>KRX 증시 조건검색 스캐너</h2>.*?</section>', '')
    text = replace_one(text, r'<script>\s*\(function\(\)\{\s*const nf=new Intl\.NumberFormat\("ko-KR"\);\s*fetch\("/stock/data/scanner\.json.*?</script>', '')
    text = replace_one(text, r'<p>증시·정책 뉴스와 KRX 공식 데이터 기반 증시 스캐너부터 YouTube 순위, 생활 계산기,<br>\s*무료 게임, 로또 당첨정보와 전국 아파트 실거래가까지 자주 찾는 정보를 한곳에 모았습니다\.</p>', '<p>경제·정책 뉴스와 YouTube 순위, 생활 계산기, 무료 게임, 로또 당첨정보와 아파트 실거래가를 한곳에서 확인하세요.</p>')
    text = re.sub(r'<a\s+href="/stock/"[^>]*>.*?</a>', '', text, flags=re.S)
    text = text.replace('뉴스 · 증시 스캐너 · YouTube', '뉴스 · YouTube')
    text = text.replace('grid-template-columns:repeat(7,1fr)', 'grid-template-columns:repeat(6,1fr)')
    # Metadata must reflect services actually available during the pause.
    text = replace_one(text, r'<title>[^<]*</title>', '<title>MODU.TODAY | 로또 기록·생활 계산기·웹게임</title>', required=True)
    text = replace_one(text, r'<meta name="description" content="[^"]*">', '<meta name="description" content="로또 회차별 당첨 기록과 과거 통계, 생활 계산기, 웹게임, 아파트 실거래가와 외부 뉴스 원문 링크를 제공합니다. KRX 증시 스캐너는 데이터 이용 범위 확인을 위해 일시 중단 중입니다.">', required=True)
    if 'id="reading-guide"' in text or 'id="stockHomeSignals"' in text or '/stock/data/scanner.json' in text or 'KRX 공식 데이터 기반 증시 스캐너' in text:
        raise ValueError('KRX elements remain in homepage')
    if '<h2>YouTube 인기 순위</h2>' not in text:
        raise ValueError('Other homepage services must be preserved')
    return text


def apply() -> None:
    if not FLAG.exists():
        print('KRX public suspension not active; no files modified')
        return
    original = HOME.read_text(encoding='utf-8')
    updated = home_paused(original)
    if updated != original:
        HOME.write_text(updated, encoding='utf-8')
    for page in (STOCK, GUIDE):
        page.parent.mkdir(parents=True, exist_ok=True)
        if not page.exists() or page.read_text(encoding='utf-8') != MAINTENANCE:
            page.write_text(MAINTENANCE, encoding='utf-8')
    removed = []
    for page in (ROOT / 'stock/data').glob('*.json'):
        page.unlink()
        removed.append(page.name)
    print('KRX public displays suspended; removed public JSON:', ', '.join(removed) or 'already absent')


def check() -> None:
    if not FLAG.exists():
        raise AssertionError('Suspension flag is missing')
    html = HOME.read_text(encoding='utf-8')
    assert home_paused(html) == html, 'Homepage not fully suspended or processing is not idempotent'
    assert STOCK.read_text(encoding='utf-8') == MAINTENANCE
    assert GUIDE.read_text(encoding='utf-8') == MAINTENANCE
    assert not list((ROOT / 'stock/data').glob('*.json'))
    print('KRX suspension check passed: homepage, stock pages and public JSON')


def test() -> None:
    fixture = '<html><head><title>old</title><meta name="description" content="old"></head><body><main>' + (
        '<section class="section" id="reading-guide"><div>KRX detail</div></section>'
        '<section class="section"><div class="wrap"><div class="section-head"><div><h2>KRX 증시 조건검색 스캐너</h2></div></div><div id="stockHomeSignals">123</div></div></section>'
        '<section class="section"><h2>YouTube 인기 순위</h2></section>'
    ) + '</main><script>(function(){const nf=new Intl.NumberFormat("ko-KR");fetch("/stock/data/scanner.json?v="+Date.now());})();</script></body></html>'
    result = home_paused(fixture)
    assert result == home_paused(result)
    assert 'KRX detail' not in result and '123' not in result
    assert '<h2>YouTube 인기 순위</h2>' in result
    print('KRX suspension fixture and idempotence: passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.test:
        test()
    elif args.check:
        check()
    else:
        apply()
