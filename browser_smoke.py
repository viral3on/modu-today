"""Browser smoke checks for public site UX. Not a Google crawler or AdSense review."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import sys

BASE = 'https://modu.today'
REPORT = Path(__file__).resolve().parent / 'docs/browser-smoke.md'
VIEWPORTS = {'desktop': {'width': 1366, 'height': 900}, 'mobile': {'width': 390, 'height': 844}}


def check_page(page, name, path, action=None):
    page.goto(BASE + path, wait_until='domcontentloaded', timeout=45000)
    if action:
        action(page)
    else:
        page.locator('h1').first.wait_for(state='visible', timeout=18000)
    return f'{path}: visible content' + (' and live interaction' if action else '')


def home(page):
    page.locator('h1').first.wait_for(state='visible', timeout=20000)
    page.locator('#reading-guide').wait_for(state='visible', timeout=15000)
    first = page.locator('.news-live .grid > a').first
    first.wait_for(state='visible', timeout=15000)
    style = first.evaluate('(el) => ({bg:getComputedStyle(el).backgroundColor,fg:getComputedStyle(el).color})')
    if style['bg'] == 'rgba(0, 0, 0, 0)' or style['bg'] in ('rgb(255, 255, 255)', 'transparent'):
        raise AssertionError('News card has no expected dark background: ' + str(style))
    if style['fg'] not in ('rgb(249, 250, 251)', 'rgb(255, 255, 255)'):
        raise AssertionError('News text is not the expected light color: ' + str(style))


def percentage(page):
    page.locator('#p1a').fill('200')
    page.locator('#p1b').fill('15')
    page.wait_for_function('() => document.querySelector("#p1r")?.textContent.trim() === "30"', timeout=10000)
    page.locator('#p3a').fill('80')
    page.locator('#p3b').fill('100')
    page.wait_for_function('() => document.querySelector("#p3r")?.textContent.trim() === "25%"', timeout=10000)


def stock(page):
    page.locator('#rows').wait_for(state='visible', timeout=18000)
    page.wait_for_function('() => document.querySelectorAll("#rows .row").length > 0', timeout=23000)


def test():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        try:
            for name, viewport in VIEWPORTS.items():
                context = browser.new_context(viewport=viewport, device_scale_factor=1, is_mobile=name=='mobile', has_touch=name=='mobile')
                page = context.new_page()
                for path, func in (('/', home), ('/calculator/percent.html', percentage), ('/stock/', stock), ('/youtube/', None), ('/apt/', None), ('/lotto/history/', None)):
                    try:
                        result = check_page(page, name, path, func)
                        results.append((name, path, '확인', result))
                    except Exception as exc:
                        results.append((name, path, '추가 확인 필요', f'{type(exc).__name__}: {str(exc)[:180]}'))
                        try:
                            page.screenshot(path=f'/tmp/modu-{name}-{path.strip("/").replace("/", "-") or "home"}.png', full_page=False, timeout=7000)
                        except Exception:
                            pass
                context.close()
        finally:
            browser.close()
    return results


def main():
    try:
        results = test()
    except Exception as exc:
        results = [('environment', '-', '추가 확인 필요', f'Chromium test setup: {type(exc).__name__}: {exc}')]
    passed = sum(status == '확인' for _, _, status, _ in results)
    lines = ['# 공개 사이트 실제 브라우저 점검', '',
             f'검사 시각 (UTC): {datetime.now(timezone.utc).isoformat(timespec="minutes")}', '',
             f'확인: {passed}/{len(results)}. Chromium을 통한 일부 기능·가독성 검사이며 Google 크롤러나 AdSense 승인 결과를 대체하지 않습니다.', '',
             '| 화면 | 경로 | 결과 | 상세 |', '|---|---|---|---|']
    for viewport, path, status, detail in results:
        lines.append(f'| {viewport} | `{path}` | {status} | {detail.replace("|", "/")} |')
    lines += ['', '검사 항목: PC/모바일 첫 화면 뉴스의 CSS, 실제 퍼센트 계산 2건, 증시 동적 종목 행, 기타 주요 서비스의 제목 표시. 화면별 전체 기능을 모두 검증했다는 뜻은 아닙니다.', '']
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines))
    return 0 if passed == len(results) else 1

if __name__ == '__main__': sys.exit(main())
